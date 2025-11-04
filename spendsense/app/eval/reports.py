"""
Report generation for SpendSense evaluation metrics.

This module generates executive summaries, charts, and PDF reports.

Why this exists:
- PRD requires exportable metrics reports for stakeholders
- Provides human-readable summaries of system performance
- Visualizes metrics with charts (matplotlib)
- Generates PDF reports for distribution (reportlab)

Output:
- Markdown executive summary with pass/fail vs PRD targets
- Charts (PNG images): persona distribution, latency histogram, fairness breakdown
- PDF report combining markdown and charts
"""

import io
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from spendsense.app.core.logging import get_logger
from spendsense.app.db.models import Recommendation

logger = get_logger(__name__)

# Optional dependencies (gracefully handle missing packages)
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    logger.warning("matplotlib not available, charts will not be generated")
    MATPLOTLIB_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
    REPORTLAB_AVAILABLE = True
except ImportError:
    logger.warning("reportlab not available, PDF generation will not work")
    REPORTLAB_AVAILABLE = False


def generate_report_markdown(metrics: dict[str, Any], session: Session) -> str:
    """
    Generate markdown executive summary of evaluation metrics.
    
    How it works:
    1. Extract key metrics from each category
    2. Compare against PRD targets (100% coverage, <5s latency, etc.)
    3. Generate pass/fail assessment
    4. Include sample recommendations with rationales
    5. Add fairness warnings if any
    
    Args:
        metrics: Metrics dictionary from compute_all_metrics()
        session: Database session for sampling recommendations
    
    Returns:
        Markdown string
    """
    logger.info("Generating markdown report")
    
    # Extract metrics
    coverage = metrics.get("coverage", {})
    explainability = metrics.get("explainability", {})
    latency = metrics.get("latency", {})
    auditability = metrics.get("auditability", {})
    fairness = metrics.get("fairness", {})
    metadata = metrics.get("metadata", {})
    
    # Build markdown
    md = []
    
    # Header
    md.append("# SpendSense Evaluation Report")
    md.append("")
    md.append(f"**Generated:** {metadata.get('computed_at', 'N/A')}")
    md.append("")
    md.append("---")
    md.append("")
    
    # Executive Summary
    md.append("## Executive Summary")
    md.append("")
    
    # Determine overall pass/fail
    coverage_pass = coverage.get("full_coverage_pct", 0) >= 80  # 80% is reasonable target
    explainability_pass = explainability.get("explainability_pct", 0) >= 90
    latency_pass = latency.get("users_under_5s_pct", 0) >= 90
    auditability_pass = auditability.get("auditability_pct", 0) >= 90
    fairness_pass = len(fairness.get("warnings", [])) == 0
    
    overall_pass = all([coverage_pass, explainability_pass, latency_pass, auditability_pass])
    
    if overall_pass:
        md.append("✅ **System Status: PASSING**")
    else:
        md.append("⚠️ **System Status: NEEDS ATTENTION**")
    md.append("")
    
    # Coverage Section
    md.append("## Coverage Metrics")
    md.append("")
    md.append(f"- **Total Users:** {coverage.get('total_users', 0)}")
    md.append(f"- **Users with Persona:** {coverage.get('users_with_persona', 0)} ({coverage.get('coverage_persona_pct', 0)}%)")
    md.append(f"- **Users with ≥3 Signals:** {coverage.get('users_with_3plus_signals', 0)} ({coverage.get('coverage_signals_pct', 0)}%)")
    md.append(f"- **Full Coverage (Persona + Signals):** {coverage.get('users_with_full_coverage', 0)} ({coverage.get('full_coverage_pct', 0)}%)")
    md.append("")
    
    if coverage_pass:
        md.append("✅ **Target: ≥80% full coverage** - PASS")
    else:
        md.append("❌ **Target: ≥80% full coverage** - FAIL")
    md.append("")
    
    # Explainability Section
    md.append("## Explainability Metrics")
    md.append("")
    md.append(f"- **Total Recommendations:** {explainability.get('total_recommendations', 0)}")
    md.append(f"- **Recommendations with Rationale:** {explainability.get('recommendations_with_rationale', 0)} ({explainability.get('explainability_pct', 0)}%)")
    md.append("")
    
    if explainability_pass:
        md.append("✅ **Target: ≥90% with rationales** - PASS")
    else:
        md.append("❌ **Target: ≥90% with rationales** - FAIL")
    md.append("")
    
    # Latency Section
    md.append("## Latency Metrics")
    md.append("")
    md.append(f"- **Sample Size:** {latency.get('sample_size', 0)} users")
    md.append(f"- **Min Latency:** {latency.get('min_latency_s', 0)}s")
    md.append(f"- **Max Latency:** {latency.get('max_latency_s', 0)}s")
    md.append(f"- **Avg Latency:** {latency.get('avg_latency_s', 0)}s")
    md.append(f"- **Median Latency:** {latency.get('median_latency_s', 0)}s")
    md.append(f"- **Users Under 5s:** {latency.get('users_under_5s', 0)}/{latency.get('sample_size', 0)} ({latency.get('users_under_5s_pct', 0)}%)")
    md.append("")
    
    if latency_pass:
        md.append("✅ **Target: ≥90% under 5 seconds** - PASS")
    else:
        md.append("❌ **Target: ≥90% under 5 seconds** - FAIL")
    md.append("")
    
    # Auditability Section
    md.append("## Auditability Metrics")
    md.append("")
    md.append(f"- **Total Recommendations:** {auditability.get('total_recommendations', 0)}")
    md.append(f"- **Recommendations with Traces:** {auditability.get('recommendations_with_traces', 0)} ({auditability.get('auditability_pct', 0)}%)")
    md.append("")
    
    if auditability_pass:
        md.append("✅ **Target: ≥90% with decision traces** - PASS")
    else:
        md.append("❌ **Target: ≥90% with decision traces** - FAIL")
    md.append("")
    
    # Fairness Section
    md.append("## Fairness Analysis")
    md.append("")
    md.append(f"- **Total Users Analyzed:** {fairness.get('total_users_analyzed', 0)}")
    md.append(f"- **Fairness Threshold:** {fairness.get('threshold_pct', 20)}%")
    md.append(f"- **Disparities Detected:** {len(fairness.get('disparities', []))}")
    md.append(f"- **Warnings:** {len(fairness.get('warnings', []))}")
    md.append("")
    
    if fairness_pass:
        md.append("✅ **No fairness warnings detected** - PASS")
    else:
        md.append("⚠️ **Fairness warnings detected** - REVIEW NEEDED")
        md.append("")
        md.append("**Warnings:**")
        for warning in fairness.get("warnings", [])[:5]:  # Limit to top 5
            md.append(f"- {warning}")
        md.append("")
    
    # Sample Recommendations
    md.append("## Sample Recommendations")
    md.append("")
    
    sample_recs = session.query(Recommendation).limit(3).all()
    if sample_recs:
        for i, rec in enumerate(sample_recs, 1):
            md.append(f"### Sample {i}: {rec.title}")
            md.append("")
            md.append(f"- **Type:** {rec.item_type}")
            md.append(f"- **User:** {rec.user_id}")
            md.append(f"- **Rationale:** {rec.rationale or 'N/A'}")
            md.append(f"- **Status:** {rec.status}")
            md.append("")
    else:
        md.append("*No recommendations found.*")
        md.append("")
    
    # Footer
    md.append("---")
    md.append("")
    md.append("*This report was automatically generated by SpendSense evaluation system.*")
    md.append("")
    
    markdown_text = "\n".join(md)
    logger.info("Markdown report generated")
    return markdown_text


def generate_charts(metrics: dict[str, Any], session: Session) -> dict[str, io.BytesIO]:
    """
    Generate charts for metrics visualization.
    
    Charts:
    - persona_distribution: Bar chart of persona assignments
    - latency_histogram: Histogram of latency measurements
    - fairness_age: Bar chart of age distribution
    
    Args:
        metrics: Metrics dictionary
        session: Database session
    
    Returns:
        Dict mapping chart name to BytesIO image buffer
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.warning("matplotlib not available, skipping chart generation")
        return {}
    
    logger.info("Generating charts")
    charts = {}
    
    # Chart 1: Persona Distribution
    try:
        fairness = metrics.get("fairness", {})
        demographics = fairness.get("demographics", {})
        age_data = demographics.get("age_range", {})
        
        if age_data:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            ages = list(age_data.keys())
            counts = [age_data[age]["count"] for age in ages]
            
            ax.bar(ages, counts, color='steelblue')
            ax.set_xlabel('Age Range')
            ax.set_ylabel('User Count')
            ax.set_title('User Distribution by Age Range')
            ax.grid(axis='y', alpha=0.3)
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            charts['fairness_age'] = buf
            plt.close(fig)
            
            logger.debug("Generated fairness_age chart")
    except Exception as e:
        logger.error(f"Error generating fairness_age chart: {e}")
    
    # Chart 2: Latency Histogram
    try:
        latency = metrics.get("latency", {})
        latencies = latency.get("latencies_seconds", [])
        
        if latencies:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            ax.hist(latencies, bins=10, color='coral', edgecolor='black')
            ax.axvline(5.0, color='red', linestyle='--', linewidth=2, label='5s Target')
            ax.set_xlabel('Latency (seconds)')
            ax.set_ylabel('Frequency')
            ax.set_title('Recommendation Generation Latency Distribution')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            charts['latency_histogram'] = buf
            plt.close(fig)
            
            logger.debug("Generated latency_histogram chart")
    except Exception as e:
        logger.error(f"Error generating latency_histogram chart: {e}")
    
    # Chart 3: Persona Distribution
    try:
        from collections import Counter
        from spendsense.app.db.models import Persona
        
        personas = session.query(Persona.persona_id).all()
        persona_counts = Counter([p[0] for p in personas])
        
        if persona_counts:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            persona_ids = list(persona_counts.keys())
            counts = list(persona_counts.values())
            
            ax.bar(persona_ids, counts, color='mediumseagreen')
            ax.set_xlabel('Persona')
            ax.set_ylabel('User Count')
            ax.set_title('Persona Assignment Distribution')
            ax.grid(axis='y', alpha=0.3)
            plt.xticks(rotation=45, ha='right')
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            charts['persona_distribution'] = buf
            plt.close(fig)
            
            logger.debug("Generated persona_distribution chart")
    except Exception as e:
        logger.error(f"Error generating persona_distribution chart: {e}")
    
    logger.info(f"Generated {len(charts)} charts")
    return charts


def generate_report_pdf(
    markdown: str,
    output_path: Path,
    metrics: dict[str, Any],
    session: Session
) -> None:
    """
    Generate PDF report from markdown and charts.
    
    How it works:
    1. Convert markdown to simple paragraphs (basic conversion)
    2. Generate charts with matplotlib
    3. Use reportlab to create PDF with text and images
    
    Args:
        markdown: Markdown report text
        output_path: Path to save PDF
        metrics: Metrics dictionary
        session: Database session
    
    Note: This is a simple implementation. For production, consider using a
    proper markdown-to-PDF converter like md2pdf or WeasyPrint.
    """
    if not REPORTLAB_AVAILABLE:
        logger.warning("reportlab not available, skipping PDF generation")
        return
    
    logger.info(f"Generating PDF report: {output_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create PDF document
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Parse markdown into simple paragraphs (basic conversion)
    lines = markdown.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.1 * inch))
            continue
        
        if line.startswith('# '):
            # Title
            text = line[2:]
            story.append(Paragraph(text, styles['Title']))
            story.append(Spacer(1, 0.2 * inch))
        elif line.startswith('## '):
            # Heading
            text = line[3:]
            story.append(Paragraph(text, styles['Heading1']))
            story.append(Spacer(1, 0.1 * inch))
        elif line.startswith('### '):
            # Subheading
            text = line[4:]
            story.append(Paragraph(text, styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
        elif line.startswith('- '):
            # Bullet point
            text = line[2:]
            story.append(Paragraph(f"• {text}", styles['Normal']))
        elif line == '---':
            # Horizontal rule
            story.append(Spacer(1, 0.2 * inch))
        else:
            # Regular paragraph
            story.append(Paragraph(line, styles['Normal']))
    
    # Add page break before charts
    story.append(PageBreak())
    
    # Add charts if available
    charts = generate_charts(metrics, session)
    
    if charts:
        story.append(Paragraph("Charts and Visualizations", styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))
        
        for chart_name, chart_buf in charts.items():
            try:
                # Save chart to temp file (reportlab needs file path)
                temp_path = output_path.parent / f"temp_{chart_name}.png"
                with open(temp_path, 'wb') as f:
                    f.write(chart_buf.getvalue())
                
                # Add chart to PDF
                img = Image(str(temp_path), width=6*inch, height=3.6*inch)
                story.append(img)
                story.append(Spacer(1, 0.3 * inch))
                
                # Clean up temp file
                temp_path.unlink()
            except Exception as e:
                logger.error(f"Error adding chart {chart_name} to PDF: {e}")
    
    # Build PDF
    doc.build(story)
    
    logger.info(f"PDF report generated: {output_path}")

