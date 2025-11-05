"""
Evaluation metrics for SpendSense.

This module computes objective metrics to measure system performance:
- Coverage: % of users with persona + ≥3 behavioral signals
- Explainability: % of recommendations with rationales
- Latency: recommendation generation time per user (target <5s)
- Auditability: % of recommendations with decision traces
- Fairness: Demographic analysis to detect disparities in persona/recommendations

Why this exists:
- PRD requires objective evaluation metrics
- Enables measurement against targets (100% coverage, <5s latency, etc.)
- Provides exportable JSON/CSV for analysis
- Demonstrates system quality and transparency
- Detects potential bias in persona assignment and recommendations
"""

import csv
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from spendsense.app.core.config import settings
from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import (
    CreditSignal,
    IncomeSignal,
    Persona,
    Recommendation,
    SavingsSignal,
    SubscriptionSignal,
    User,
)
from spendsense.app.recommend.engine import generate_recommendations

logger = get_logger(__name__)


def compute_coverage_metrics(session: Session) -> dict[str, Any]:
    """
    Compute coverage metrics: % of users with persona + ≥3 behavioral signals.
    
    PRD Target: 100% coverage for users with sufficient data.
    
    How it works:
    1. Count total users in database
    2. For each user, check if they have a persona assigned (any window)
    3. For each user, count how many signal types they have (subscription, savings, credit, income)
    4. Calculate % with persona and % with ≥3 signals
    
    Returns:
        Dict with coverage metrics
    """
    logger.info("Computing coverage metrics")

    # Total users
    total_users = session.query(func.count(User.id)).scalar() or 0

    if total_users == 0:
        logger.warning("No users found in database")
        return {
            "total_users": 0,
            "users_with_persona": 0,
            "users_with_3plus_signals": 0,
            "coverage_persona_pct": 0.0,
            "coverage_signals_pct": 0.0,
            "full_coverage_pct": 0.0,
        }

    # Users with at least one persona assigned
    users_with_persona = session.query(
        func.count(func.distinct(Persona.user_id))
    ).scalar() or 0

    # Count users with ≥3 signal types
    users_with_3plus_signals = 0

    all_users = session.query(User).all()
    for user in all_users:
        signal_count = 0

        # Check each signal type (using any window)
        has_subscription = session.query(SubscriptionSignal).filter(
            SubscriptionSignal.user_id == user.user_id
        ).first() is not None
        if has_subscription:
            signal_count += 1

        has_savings = session.query(SavingsSignal).filter(
            SavingsSignal.user_id == user.user_id
        ).first() is not None
        if has_savings:
            signal_count += 1

        has_credit = session.query(CreditSignal).filter(
            CreditSignal.user_id == user.user_id
        ).first() is not None
        if has_credit:
            signal_count += 1

        has_income = session.query(IncomeSignal).filter(
            IncomeSignal.user_id == user.user_id
        ).first() is not None
        if has_income:
            signal_count += 1

        if signal_count >= 3:
            users_with_3plus_signals += 1

    # Calculate percentages
    coverage_persona_pct = (users_with_persona / total_users * 100) if total_users > 0 else 0.0
    coverage_signals_pct = (users_with_3plus_signals / total_users * 100) if total_users > 0 else 0.0

    # Full coverage: users with both persona AND ≥3 signals
    # For simplicity, we'll count users that have both
    users_with_full_coverage = 0
    for user in all_users:
        has_persona = session.query(Persona).filter(
            Persona.user_id == user.user_id
        ).first() is not None

        signal_count = 0
        if session.query(SubscriptionSignal).filter(SubscriptionSignal.user_id == user.user_id).first():
            signal_count += 1
        if session.query(SavingsSignal).filter(SavingsSignal.user_id == user.user_id).first():
            signal_count += 1
        if session.query(CreditSignal).filter(CreditSignal.user_id == user.user_id).first():
            signal_count += 1
        if session.query(IncomeSignal).filter(IncomeSignal.user_id == user.user_id).first():
            signal_count += 1

        if has_persona and signal_count >= 3:
            users_with_full_coverage += 1

    full_coverage_pct = (users_with_full_coverage / total_users * 100) if total_users > 0 else 0.0

    metrics = {
        "total_users": total_users,
        "users_with_persona": users_with_persona,
        "users_with_3plus_signals": users_with_3plus_signals,
        "users_with_full_coverage": users_with_full_coverage,
        "coverage_persona_pct": round(coverage_persona_pct, 2),
        "coverage_signals_pct": round(coverage_signals_pct, 2),
        "full_coverage_pct": round(full_coverage_pct, 2),
    }

    logger.info(f"Coverage metrics: {metrics}")
    return metrics


def compute_explainability_metrics(session: Session) -> dict[str, Any]:
    """
    Compute explainability metrics: % of recommendations with rationales.
    
    PRD Target: 100% of recommendations have rationales.
    
    How it works:
    1. Count total recommendations in database
    2. Count recommendations with non-null, non-empty rationale
    3. Calculate percentage
    
    Returns:
        Dict with explainability metrics
    """
    logger.info("Computing explainability metrics")

    # Total recommendations
    total_recs = session.query(func.count(Recommendation.id)).scalar() or 0

    if total_recs == 0:
        logger.warning("No recommendations found in database")
        return {
            "total_recommendations": 0,
            "recommendations_with_rationale": 0,
            "explainability_pct": 0.0,
        }

    # Recommendations with rationale (non-null and non-empty)
    recs_with_rationale = session.query(func.count(Recommendation.id)).filter(
        Recommendation.rationale.isnot(None),
        Recommendation.rationale != ""
    ).scalar() or 0

    explainability_pct = (recs_with_rationale / total_recs * 100) if total_recs > 0 else 0.0

    metrics = {
        "total_recommendations": total_recs,
        "recommendations_with_rationale": recs_with_rationale,
        "explainability_pct": round(explainability_pct, 2),
    }

    logger.info(f"Explainability metrics: {metrics}")
    return metrics


def compute_latency_metrics(session: Session, sample_size: int = 10) -> dict[str, Any]:
    """
    Compute latency metrics: recommendation generation time per user.
    
    PRD Target: <5 seconds per user for full pipeline (signals → persona → recommendations).
    
    How it works:
    1. Sample a subset of users (default 10 for performance)
    2. For each user, time the full pipeline: assign_persona + generate_recommendations
    3. Calculate min, max, avg, median latency
    4. Check % of users meeting <5s target
    
    Args:
        session: Database session
        sample_size: Number of users to sample (default 10)
    
    Returns:
        Dict with latency metrics
    """
    logger.info(f"Computing latency metrics (sample_size={sample_size})")

    # Get sample users with personas
    users_with_personas = session.query(Persona.user_id).distinct().limit(sample_size).all()

    if not users_with_personas:
        logger.warning("No users with personas found for latency testing")
        return {
            "sample_size": 0,
            "latencies_seconds": [],
            "min_latency_s": 0.0,
            "max_latency_s": 0.0,
            "avg_latency_s": 0.0,
            "median_latency_s": 0.0,
            "users_under_5s": 0,
            "users_under_5s_pct": 0.0,
        }

    latencies: list[float] = []

    for (user_id,) in users_with_personas:
        # Time the full recommendation generation pipeline
        start_time = time.time()

        try:
            # Generate recommendations (this internally uses persona assignment)
            generate_recommendations(user_id, window_days=30, session=session)

            end_time = time.time()
            latency = end_time - start_time
            latencies.append(latency)

            logger.debug(f"User {user_id}: {latency:.3f}s")
        except Exception as e:
            logger.error(f"Error generating recommendations for {user_id}: {e}")
            continue

    if not latencies:
        logger.warning("No successful latency measurements")
        return {
            "sample_size": 0,
            "latencies_seconds": [],
            "min_latency_s": 0.0,
            "max_latency_s": 0.0,
            "avg_latency_s": 0.0,
            "median_latency_s": 0.0,
            "users_under_5s": 0,
            "users_under_5s_pct": 0.0,
        }

    # Calculate statistics
    min_latency = min(latencies)
    max_latency = max(latencies)
    avg_latency = sum(latencies) / len(latencies)

    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)
    if n % 2 == 0:
        median_latency = (sorted_latencies[n // 2 - 1] + sorted_latencies[n // 2]) / 2
    else:
        median_latency = sorted_latencies[n // 2]

    users_under_5s = sum(1 for lat in latencies if lat < 5.0)
    users_under_5s_pct = (users_under_5s / len(latencies) * 100) if latencies else 0.0

    metrics = {
        "sample_size": len(latencies),
        "latencies_seconds": [round(lat, 3) for lat in latencies],
        "min_latency_s": round(min_latency, 3),
        "max_latency_s": round(max_latency, 3),
        "avg_latency_s": round(avg_latency, 3),
        "median_latency_s": round(median_latency, 3),
        "users_under_5s": users_under_5s,
        "users_under_5s_pct": round(users_under_5s_pct, 2),
    }

    logger.info(f"Latency metrics: avg={avg_latency:.3f}s, {users_under_5s_pct:.1f}% under 5s")
    return metrics


def compute_auditability_metrics(session: Session) -> dict[str, Any]:
    """
    Compute auditability metrics: % of recommendations with decision traces.
    
    PRD Target: 100% of recommendations have decision traces.
    
    How it works:
    1. Count total recommendations
    2. Check for recommendations with eligibility_flags (used as decision trace proxy)
    3. Calculate percentage
    
    Note: Full decision traces are exported separately per-user via traces.py
    
    Returns:
        Dict with auditability metrics
    """
    logger.info("Computing auditability metrics")

    # Total recommendations
    total_recs = session.query(func.count(Recommendation.id)).scalar() or 0

    if total_recs == 0:
        logger.warning("No recommendations found in database")
        return {
            "total_recommendations": 0,
            "recommendations_with_traces": 0,
            "auditability_pct": 0.0,
        }

    # Recommendations with eligibility_flags (contains guardrail decisions)
    # We consider a recommendation auditable if it has eligibility_flags set
    recs_with_traces = session.query(func.count(Recommendation.id)).filter(
        Recommendation.eligibility_flags.isnot(None),
        Recommendation.eligibility_flags != ""
    ).scalar() or 0

    auditability_pct = (recs_with_traces / total_recs * 100) if total_recs > 0 else 0.0

    metrics = {
        "total_recommendations": total_recs,
        "recommendations_with_traces": recs_with_traces,
        "auditability_pct": round(auditability_pct, 2),
    }

    logger.info(f"Auditability metrics: {metrics}")
    return metrics


def compute_fairness_metrics(session: Session) -> dict[str, Any]:
    """
    Compute fairness metrics: demographic analysis of persona and recommendation distribution.
    
    PRD Requirement: Detect disparities in persona assignment and recommendations across demographics.
    
    How it works:
    1. Group users by age_range, gender, ethnicity
    2. For each demographic group:
       - Count users in each persona
       - Count education vs offer recommendations
       - Calculate distribution percentages
    3. Detect disparities: flag if any group is >FAIRNESS_THRESHOLD% over/under-represented
    
    Returns:
        Dict with:
        - demographics: breakdown by demographic attribute
        - disparities: list of detected fairness issues
        - warnings: actionable alerts for operators
    """
    logger.info("Computing fairness metrics")
    
    # Get fairness threshold from config (default 20%)
    threshold = settings.fairness_threshold
    
    # Initialize result structure
    demographics_analysis: dict[str, dict[str, Any]] = {}
    disparities: list[dict[str, Any]] = []
    warnings: list[str] = []
    
    # Get all users with demographics
    all_users = session.query(User).filter(User.is_active == True).all()
    total_users = len(all_users)
    
    if total_users == 0:
        logger.warning("No active users found for fairness analysis")
        return {
            "demographics": {},
            "disparities": [],
            "warnings": ["No active users found"],
            "threshold_pct": threshold,
        }
    
    # Analyze by age_range
    age_groups = defaultdict(lambda: {
        "count": 0,
        "personas": defaultdict(int),
        "education_recs": 0,
        "offer_recs": 0,
    })
    
    for user in all_users:
        age = user.age_range or "unknown"
        age_groups[age]["count"] += 1
        
        # Count persona assignments
        persona = session.query(Persona).filter(
            Persona.user_id == user.user_id
        ).first()
        if persona:
            age_groups[age]["personas"][persona.persona_id] += 1
        
        # Count recommendations by type
        recommendations = session.query(Recommendation).filter(
            Recommendation.user_id == user.user_id
        ).all()
        for rec in recommendations:
            if rec.item_type == "education":
                age_groups[age]["education_recs"] += 1
            elif rec.item_type == "offer":
                age_groups[age]["offer_recs"] += 1
    
    # Calculate percentages and detect disparities for age
    age_analysis = {}
    for age, data in age_groups.items():
        pct_of_total = (data["count"] / total_users * 100) if total_users > 0 else 0
        
        age_analysis[age] = {
            "count": data["count"],
            "pct_of_total": round(pct_of_total, 2),
            "personas": dict(data["personas"]),
            "education_recs": data["education_recs"],
            "offer_recs": data["offer_recs"],
        }
        
        # Check for under-representation (less than threshold% of expected)
        expected_pct = 100.0 / len(age_groups) if len(age_groups) > 0 else 0
        if abs(pct_of_total - expected_pct) > threshold:
            disparities.append({
                "demographic": "age_range",
                "group": age,
                "issue": f"Representation {pct_of_total:.1f}% vs expected ~{expected_pct:.1f}%",
                "severity": "warning",
            })
            warnings.append(f"Age group '{age}' is {pct_of_total:.1f}% of users (expected ~{expected_pct:.1f}%)")
    
    demographics_analysis["age_range"] = age_analysis
    
    # Analyze by gender
    gender_groups = defaultdict(lambda: {
        "count": 0,
        "personas": defaultdict(int),
        "education_recs": 0,
        "offer_recs": 0,
    })
    
    for user in all_users:
        gender = user.gender or "unknown"
        gender_groups[gender]["count"] += 1
        
        persona = session.query(Persona).filter(
            Persona.user_id == user.user_id
        ).first()
        if persona:
            gender_groups[gender]["personas"][persona.persona_id] += 1
        
        recommendations = session.query(Recommendation).filter(
            Recommendation.user_id == user.user_id
        ).all()
        for rec in recommendations:
            if rec.item_type == "education":
                gender_groups[gender]["education_recs"] += 1
            elif rec.item_type == "offer":
                gender_groups[gender]["offer_recs"] += 1
    
    gender_analysis = {}
    for gender, data in gender_groups.items():
        pct_of_total = (data["count"] / total_users * 100) if total_users > 0 else 0
        
        gender_analysis[gender] = {
            "count": data["count"],
            "pct_of_total": round(pct_of_total, 2),
            "personas": dict(data["personas"]),
            "education_recs": data["education_recs"],
            "offer_recs": data["offer_recs"],
        }
    
    demographics_analysis["gender"] = gender_analysis
    
    # Analyze by ethnicity
    ethnicity_groups = defaultdict(lambda: {
        "count": 0,
        "personas": defaultdict(int),
        "education_recs": 0,
        "offer_recs": 0,
    })
    
    for user in all_users:
        ethnicity = user.ethnicity or "unknown"
        ethnicity_groups[ethnicity]["count"] += 1
        
        persona = session.query(Persona).filter(
            Persona.user_id == user.user_id
        ).first()
        if persona:
            ethnicity_groups[ethnicity]["personas"][persona.persona_id] += 1
        
        recommendations = session.query(Recommendation).filter(
            Recommendation.user_id == user.user_id
        ).all()
        for rec in recommendations:
            if rec.item_type == "education":
                ethnicity_groups[ethnicity]["education_recs"] += 1
            elif rec.item_type == "offer":
                ethnicity_groups[ethnicity]["offer_recs"] += 1
    
    ethnicity_analysis = {}
    for ethnicity, data in ethnicity_groups.items():
        pct_of_total = (data["count"] / total_users * 100) if total_users > 0 else 0
        
        ethnicity_analysis[ethnicity] = {
            "count": data["count"],
            "pct_of_total": round(pct_of_total, 2),
            "personas": dict(data["personas"]),
            "education_recs": data["education_recs"],
            "offer_recs": data["offer_recs"],
        }
    
    demographics_analysis["ethnicity"] = ethnicity_analysis
    
    # Count total personas assigned
    total_personas = session.query(func.count(func.distinct(Persona.user_id))).scalar() or 0
    
    metrics = {
        "demographics": demographics_analysis,
        "disparities": disparities,
        "warnings": warnings,
        "threshold_pct": threshold,
        "total_users_analyzed": total_users,
        "total_users": total_users,  # For frontend compatibility
        "total_personas": total_personas,  # Number of users with assigned personas
    }
    
    logger.info(f"Fairness metrics: {len(disparities)} disparities detected, {len(warnings)} warnings")
    return metrics


def compute_all_metrics(session: Session, latency_sample_size: int = 10) -> dict[str, Any]:
    """
    Compute all evaluation metrics.
    
    This is the main entry point for metrics computation.
    
    Args:
        session: Database session
        latency_sample_size: Number of users to sample for latency testing
    
    Returns:
        Dict with all metrics organized by category
    """
    logger.info("Computing all evaluation metrics")

    metrics = {
        "coverage": compute_coverage_metrics(session),
        "explainability": compute_explainability_metrics(session),
        "latency": compute_latency_metrics(session, sample_size=latency_sample_size),
        "auditability": compute_auditability_metrics(session),
        "fairness": compute_fairness_metrics(session),
        "metadata": {
            "computed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "latency_sample_size": latency_sample_size,
        }
    }

    logger.info("All metrics computed successfully")
    return metrics


def export_metrics_json(metrics: dict[str, Any], output_path: Path) -> None:
    """
    Export metrics to JSON file.
    
    Args:
        metrics: Metrics dictionary
        output_path: Path to output JSON file
    """
    logger.info(f"Exporting metrics to JSON: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    logger.info(f"Metrics exported to {output_path}")


def export_metrics_csv(metrics: dict[str, Any], output_path: Path) -> None:
    """
    Export metrics to CSV file.
    
    Flattens the nested metrics dict into CSV rows.
    Each category becomes rows with category.metric_name and value columns.
    
    Args:
        metrics: Metrics dictionary
        output_path: Path to output CSV file
    """
    logger.info(f"Exporting metrics to CSV: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Flatten metrics for CSV
    rows = []

    for category, category_metrics in metrics.items():
        if category == "metadata":
            continue  # Skip metadata for CSV simplicity

        if isinstance(category_metrics, dict):
            for metric_name, value in category_metrics.items():
                # Skip list values in CSV (like latencies_seconds)
                if isinstance(value, list):
                    continue

                rows.append({
                    "category": category,
                    "metric": metric_name,
                    "value": value,
                })

    # Write CSV
    with open(output_path, "w", newline="") as f:
        if rows:
            fieldnames = ["category", "metric", "value"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    logger.info(f"Metrics exported to {output_path}")


def export_metrics(metrics: dict[str, Any], output_dir: Path) -> None:
    """
    Export metrics to both JSON and CSV formats.
    
    Args:
        metrics: Metrics dictionary
        output_dir: Directory to write files (e.g., ./data/)
    """
    json_path = output_dir / "eval_metrics.json"
    csv_path = output_dir / "eval_metrics.csv"

    export_metrics_json(metrics, json_path)
    export_metrics_csv(metrics, csv_path)

    logger.info(f"Metrics exported to {output_dir}")

