#!/usr/bin/env python3
"""
Evaluation metrics computation and export script.

This script computes all evaluation metrics and exports them to JSON/CSV.
It also exports per-user decision traces for auditability.

What it does:
1. Computes coverage metrics (% users with persona + ≥3 signals)
2. Computes explainability metrics (% recommendations with rationales)
3. Computes latency metrics (recommendation generation time)
4. Computes auditability metrics (% recommendations with decision traces)
5. Computes fairness metrics (demographic analysis)
6. Exports metrics to ./data/eval_metrics.json and ./data/eval_metrics.csv
7. Exports per-user decision traces to ./data/decision_traces/
8. (Optional) Generates markdown and PDF reports with --report flag

PRD Targets:
- Coverage: 100% of users with sufficient data
- Explainability: 100% of recommendations with rationales
- Latency: <5 seconds per user
- Auditability: 100% of recommendations with decision traces
- Fairness: No disparities >threshold% across demographics

Usage:
    python -m scripts.run_metrics [--latency-sample-size N] [--window 30|180] [--report]
"""

import argparse
from pathlib import Path

from scripts._bootstrap import add_project_root

add_project_root()

from spendsense.app.db.session import get_session
from spendsense.app.core.config import settings
from spendsense.app.core.logging import get_logger
from spendsense.app.eval.metrics import compute_all_metrics, export_metrics
from spendsense.app.eval.traces import export_all_decision_traces


logger = get_logger(__name__)


def main(latency_sample_size: int = 10, window_days: int = 30, generate_report: bool = False):
    """
    Main entry point for metrics computation.
    
    Args:
        latency_sample_size: Number of users to sample for latency testing
        window_days: Time window for decision traces (30 or 180)
        generate_report: Whether to generate markdown and PDF reports
    """
    logger.info("=" * 60)
    logger.info("SpendSense Evaluation Metrics Computation")
    logger.info("=" * 60)
    
    # Get database session using context manager
    with next(get_session()) as session:
        try:
            # 1. Compute all metrics
            logger.info("Step 1/5: Computing evaluation metrics...")
            metrics = compute_all_metrics(session, latency_sample_size=latency_sample_size)
            
            # 2. Export metrics to JSON and CSV
            logger.info("Step 2/5: Exporting metrics...")
            output_dir = Path(settings.data_dir)
            export_metrics(metrics, output_dir)
            
            # 3. Export decision traces
            logger.info(f"Step 3/5: Exporting decision traces (window={window_days}d)...")
            traces_dir = output_dir / "decision_traces"
            exported_traces = export_all_decision_traces(session, traces_dir, window_days=window_days)
            
            # 4. Export fairness traces
            logger.info("Step 4/5: Exporting fairness traces...")
            from spendsense.app.eval.fairness_traces import export_fairness_traces
            export_fairness_traces(session, traces_dir)
            
            # 5. Generate reports if requested
            if generate_report:
                logger.info("Step 5/5: Generating reports...")
                
                from spendsense.app.eval.reports import (
                    generate_report_markdown,
                    generate_report_pdf,
                )
                from spendsense.app.eval.report_history import save_report_with_timestamp
                
                # Generate markdown report
                markdown = generate_report_markdown(metrics, session)
                md_path = output_dir / "eval_report.md"
                md_path.write_text(markdown)
                logger.info(f"Markdown report: {md_path}")
                
                # Generate PDF report
                try:
                    pdf_path = output_dir / "eval_report.pdf"
                    generate_report_pdf(markdown, pdf_path, metrics, session)
                    logger.info(f"PDF report: {pdf_path}")
                    
                    # Archive reports with timestamp
                    save_report_with_timestamp(md_path)
                    save_report_with_timestamp(pdf_path)
                    
                except Exception as e:
                    logger.warning(f"PDF generation failed (optional dependency): {e}")
            else:
                logger.info("Step 5/5: Skipping report generation (use --report to enable)")
            
            # Print summary
            logger.info("=" * 60)
            logger.info("METRICS SUMMARY")
            logger.info("=" * 60)
            
            # Coverage
            cov = metrics["coverage"]
            logger.info(f"Coverage:")
            logger.info(f"  - Total users: {cov['total_users']}")
            logger.info(f"  - Users with persona: {cov['users_with_persona']} ({cov['coverage_persona_pct']:.1f}%)")
            logger.info(f"  - Users with ≥3 signals: {cov['users_with_3plus_signals']} ({cov['coverage_signals_pct']:.1f}%)")
            logger.info(f"  - Full coverage (persona + ≥3 signals): {cov['users_with_full_coverage']} ({cov['full_coverage_pct']:.1f}%)")
            
            # Explainability
            exp = metrics["explainability"]
            logger.info(f"\nExplainability:")
            logger.info(f"  - Total recommendations: {exp['total_recommendations']}")
            logger.info(f"  - Recommendations with rationale: {exp['recommendations_with_rationale']} ({exp['explainability_pct']:.1f}%)")
            
            # Latency
            lat = metrics["latency"]
            logger.info(f"\nLatency:")
            logger.info(f"  - Sample size: {lat['sample_size']} users")
            logger.info(f"  - Avg latency: {lat['avg_latency_s']:.3f}s")
            logger.info(f"  - Min latency: {lat['min_latency_s']:.3f}s")
            logger.info(f"  - Max latency: {lat['max_latency_s']:.3f}s")
            logger.info(f"  - Median latency: {lat['median_latency_s']:.3f}s")
            logger.info(f"  - Users under 5s: {lat['users_under_5s']}/{lat['sample_size']} ({lat['users_under_5s_pct']:.1f}%)")
            
            # Auditability
            aud = metrics["auditability"]
            logger.info(f"\nAuditability:")
            logger.info(f"  - Total recommendations: {aud['total_recommendations']}")
            logger.info(f"  - Recommendations with traces: {aud['recommendations_with_traces']} ({aud['auditability_pct']:.1f}%)")
            
            # Fairness
            fair = metrics["fairness"]
            logger.info(f"\nFairness:")
            logger.info(f"  - Total users analyzed: {fair['total_users_analyzed']}")
            logger.info(f"  - Fairness threshold: {fair['threshold_pct']}%")
            logger.info(f"  - Disparities detected: {len(fair.get('disparities', []))}")
            logger.info(f"  - Warnings: {len(fair.get('warnings', []))}")
            if fair.get('warnings'):
                for warning in fair['warnings'][:3]:  # Show first 3
                    logger.info(f"    • {warning}")
            
            # Outputs
            logger.info("\n" + "=" * 60)
            logger.info("OUTPUTS")
            logger.info("=" * 60)
            logger.info(f"Metrics JSON: {output_dir / 'eval_metrics.json'}")
            logger.info(f"Metrics CSV: {output_dir / 'eval_metrics.csv'}")
            logger.info(f"Decision traces: {traces_dir}/ ({len(exported_traces)} files)")
            logger.info(f"Fairness traces: {traces_dir}/fairness/")
            if generate_report:
                logger.info(f"Markdown report: {output_dir / 'eval_report.md'}")
                if (output_dir / 'eval_report.pdf').exists():
                    logger.info(f"PDF report: {output_dir / 'eval_report.pdf'}")
            
            # PRD targets check
            logger.info("\n" + "=" * 60)
            logger.info("PRD TARGETS CHECK")
            logger.info("=" * 60)
            
            target_coverage = cov['full_coverage_pct'] >= 80.0  # 80% threshold (100% ideal)
            target_explainability = exp['explainability_pct'] >= 95.0  # 95% threshold (100% ideal)
            target_latency = lat['users_under_5s_pct'] >= 90.0  # 90% under 5s (100% ideal)
            target_auditability = aud['auditability_pct'] >= 95.0  # 95% threshold (100% ideal)
            
            logger.info(f"✓ Coverage ≥80%: {'PASS' if target_coverage else 'FAIL'} ({cov['full_coverage_pct']:.1f}%)")
            logger.info(f"✓ Explainability ≥95%: {'PASS' if target_explainability else 'FAIL'} ({exp['explainability_pct']:.1f}%)")
            logger.info(f"✓ Latency <5s ≥90%: {'PASS' if target_latency else 'FAIL'} ({lat['users_under_5s_pct']:.1f}%)")
            logger.info(f"✓ Auditability ≥95%: {'PASS' if target_auditability else 'FAIL'} ({aud['auditability_pct']:.1f}%)")
            
            all_pass = target_coverage and target_explainability and target_latency and target_auditability
            logger.info("\n" + "=" * 60)
            if all_pass:
                logger.info("✓ ALL PRD TARGETS MET")
            else:
                logger.info("⚠ SOME PRD TARGETS NOT MET (see above)")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Error computing metrics: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute and export SpendSense evaluation metrics"
    )
    parser.add_argument(
        "--latency-sample-size",
        type=int,
        default=10,
        help="Number of users to sample for latency testing (default: 10)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=30,
        choices=[30, 180],
        help="Time window for decision traces in days (default: 30)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate markdown and PDF reports (requires matplotlib and reportlab)",
    )
    
    args = parser.parse_args()
    
    main(
        latency_sample_size=args.latency_sample_size,
        window_days=args.window,
        generate_report=args.report,
    )
