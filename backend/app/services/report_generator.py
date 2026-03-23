"""Report generation service for vulnerability reports."""
import logging
from datetime import datetime
from typing import Optional
from io import BytesIO

import httpx
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate vulnerability reports in various formats."""

    SEVERITY_COLORS = {
        "critical": "#dc2626",
        "high": "#ea580c",
        "medium": "#ca8a04",
        "low": "#16a34a",
        "informational": "#6b7280",
    }

    _reports: dict[str, dict] = {}

    def save_report(self, report_id: str, data: dict) -> None:
        """Save a report to memory for later retrieval."""
        self._reports[report_id] = data

    def get_report(self, report_id: str) -> dict | None:
        """Get a saved report by ID."""
        return self._reports.get(report_id)

    def generate_html(
        self,
        program_name: str,
        target: str,
        findings: list[dict],
        cvss_scores: bool = True,
        screenshots: bool = True,
        remediation: bool = True,
    ) -> str:
        """Generate HTML vulnerability report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        severity_counts = {}
        for f in findings:
            severity = f.get("severity", "informational").lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vulnerability Report - {program_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        .header {{
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #1e40af;
            margin: 0;
        }}
        .meta {{
            color: #6b7280;
            font-size: 14px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: #f3f4f6;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card .count {{
            font-size: 32px;
            font-weight: bold;
        }}
        .summary-card.critical {{ background: #fef2f2; }}
        .summary-card.critical .count {{ color: #dc2626; }}
        .summary-card.high {{ background: #fff7ed; }}
        .summary-card.high .count {{ color: #ea580c; }}
        .summary-card.medium {{ background: #fefce8; }}
        .summary-card.medium .count {{ color: #ca8a04; }}
        .summary-card.low {{ background: #f0fdf4; }}
        .summary-card.low .count {{ color: #16a34a; }}
        .finding {{
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .finding-header {{
            padding: 15px 20px;
            background: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .finding-title {{
            font-size: 18px;
            font-weight: 600;
            margin: 0;
        }}
        .severity-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            color: white;
        }}
        .finding-body {{
            padding: 20px;
        }}
        .section {{
            margin-bottom: 20px;
        }}
        .section-title {{
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
        }}
        .cvss-box {{
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 6px;
            padding: 12px;
            font-family: monospace;
            font-size: 13px;
        }}
        .steps {{
            background: #f9fafb;
            padding: 15px;
            border-radius: 6px;
        }}
        .steps ol {{
            margin: 0;
            padding-left: 25px;
        }}
        .screenshot {{
            max-width: 100%;
            border: 1px solid #e5e7eb;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .remediation {{
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 6px;
            padding: 15px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Vulnerability Report</h1>
        <p class="meta">
            <strong>Program:</strong> {program_name} |
            <strong>Target:</strong> {target} |
            <strong>Generated:</strong> {timestamp}
        </p>
    </div>

    <div class="summary">
        <div class="summary-card critical">
            <div class="count">{severity_counts.get('critical', 0)}</div>
            <div>Critical</div>
        </div>
        <div class="summary-card high">
            <div class="count">{severity_counts.get('high', 0)}</div>
            <div>High</div>
        </div>
        <div class="summary-card medium">
            <div class="count">{severity_counts.get('medium', 0)}</div>
            <div>Medium</div>
        </div>
        <div class="summary-card low">
            <div class="count">{severity_counts.get('low', 0)}</div>
            <div>Low</div>
        </div>
    </div>
"""

        for i, finding in enumerate(findings, 1):
            severity = finding.get("severity", "informational").lower()
            color = self.SEVERITY_COLORS.get(severity, "#6b7280")

            html += f"""
    <div class="finding">
        <div class="finding-header">
            <h2 class="finding-title">{i}. {finding.get('title', 'Untitled')}</h2>
            <span class="severity-badge" style="background: {color}">
                {severity.upper()}
            </span>
        </div>
        <div class="finding-body">
            <div class="section">
                <div class="section-title">Description</div>
                <p>{finding.get('description', 'No description provided.')}</p>
            </div>

            <div class="section">
                <div class="section-title">Impact</div>
                <p>{finding.get('impact', 'No impact description provided.')}</p>
            </div>
"""

            if cvss_scores and finding.get("cvss_vector"):
                html += f"""
            <div class="section">
                <div class="section-title">CVSS Score</div>
                <div class="cvss-box">
                    Vector: {finding.get('cvss_vector', 'N/A')}<br>
                    Score: {finding.get('cvss_score', 'N/A')}
                </div>
            </div>
"""

            html += f"""
            <div class="section">
                <div class="section-title">Steps to Reproduce</div>
                <div class="steps">
                    <ol>
"""

            for step in finding.get("steps_to_reproduce", []):
                html += f"                        <li>{step}</li>\n"

            html += """                    </ol>
                </div>
            </div>
"""

            if screenshots and finding.get("screenshots"):
                html += """
            <div class="section">
                <div class="section-title">Evidence</div>
"""
                for screenshot in finding.get("screenshots", []):
                    html += f'                <img src="{screenshot}" alt="Screenshot" class="screenshot">\n'
                html += """            </div>
"""

            if remediation and finding.get("remediation"):
                html += f"""
            <div class="section">
                <div class="section-title">Remediation</div>
                <div class="remediation">{finding.get('remediation', 'No remediation advice provided.')}</div>
            </div>
"""

            if finding.get("cwe_id"):
                html += f"""
            <div class="section">
                <div class="section-title">Classification</div>
                <p><strong>CWE:</strong> {finding.get('cwe_id')}</p>
                <p><strong>CVE:</strong> {finding.get('cve_id', 'N/A')}</p>
            </div>
"""

            html += """        </div>
    </div>
"""

        html += f"""
    <div class="footer">
        <p>Generated by Bug Bounty Automator | {timestamp}</p>
        <p>Total Findings: {len(findings)}</p>
    </div>
</body>
</html>"""

        return html

    def generate_markdown(
        self,
        program_name: str,
        target: str,
        findings: list[dict],
        cvss_scores: bool = True,
        remediation: bool = True,
    ) -> str:
        """Generate Markdown vulnerability report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = f"""# Vulnerability Report

**Program:** {program_name}  
**Target:** {target}  
**Generated:** {timestamp}

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | {sum(1 for f in findings if f.get('severity', '').lower() == 'critical')} |
| High | {sum(1 for f in findings if f.get('severity', '').lower() == 'high')} |
| Medium | {sum(1 for f in findings if f.get('severity', '').lower() == 'medium')} |
| Low | {sum(1 for f in findings if f.get('severity', '').lower() == 'low')} |

**Total Findings:** {len(findings)}

---

"""

        for i, finding in enumerate(findings, 1):
            severity = finding.get("severity", "informational")
            cvss = ""
            if cvss_scores and finding.get("cvss_vector"):
                cvss = f"\n**CVSS:** {finding.get('cvss_score', 'N/A')} ({finding.get('cvss_vector', 'N/A')})"

            cwe_cve = ""
            if finding.get("cwe_id"):
                cwe_cve = f"\n**CWE:** {finding.get('cwe_id')}"
            if finding.get("cve_id"):
                cwe_cve += f"\n**CVE:** {finding.get('cve_id')}"

            md += f"""## {i}. {finding.get('title', 'Untitled')}

**Severity:** {severity.upper()}{cvss}{cwe_cve}

### Description

{finding.get('description', 'No description provided.')}

### Impact

{finding.get('impact', 'No impact description provided.')}

### Steps to Reproduce

"""
            for j, step in enumerate(finding.get("steps_to_reproduce", []), 1):
                md += f"{j}. {step}\n"

            md += "\n"

            if remediation and finding.get("remediation"):
                md += f"""### Remediation

{finding.get('remediation')}

"""

            if finding.get("screenshots"):
                md += """### Evidence

"""
                for screenshot in finding.get("screenshots", []):
                    md += f"![Screenshot]({screenshot})\n"

            md += "---\n\n"

        md += f"""
---

*Generated by Bug Bounty Automator | {timestamp}*
"""

        return md

    async def save_html(self, html: str, filepath: str) -> bool:
        """Save HTML report to file."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            logger.info(f"HTML report saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save HTML report: {e}")
            return False

    async def save_markdown(self, md: str, filepath: str) -> bool:
        """Save Markdown report to file."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md)
            logger.info(f"Markdown report saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save Markdown report: {e}")
            return False


    def generate_pdf(
        self,
        program_name: str,
        target: str,
        findings: list[dict],
        cvss_scores: bool = True,
        remediation: bool = True,
    ) -> bytes:
        """Generate PDF vulnerability report."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1e40af'),
            spaceAfter=20,
            alignment=TA_CENTER,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#374151'),
            spaceBefore=15,
            spaceAfter=10,
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            spaceAfter=10,
        )
        
        severity_styles = {
            'critical': HexColor('#dc2626'),
            'high': HexColor('#ea580c'),
            'medium': HexColor('#ca8a04'),
            'low': HexColor('#16a34a'),
            'informational': HexColor('#6b7280'),
        }
        
        elements = []
        
        elements.append(Paragraph("Vulnerability Report", title_style))
        elements.append(Spacer(1, 10))
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        meta_text = f"<b>Program:</b> {program_name} | <b>Target:</b> {target} | <b>Generated:</b> {timestamp}"
        elements.append(Paragraph(meta_text, body_style))
        elements.append(Spacer(1, 20))
        
        severity_counts = {}
        for f in findings:
            severity = f.get("severity", "informational").lower()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        summary_data = [["Severity", "Count"]]
        for sev, count in severity_counts.items():
            summary_data.append([sev.upper(), str(count)])
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e5e7eb')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#374151')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#d1d5db')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 30))
        
        for i, finding in enumerate(findings, 1):
            severity = finding.get("severity", "informational").lower()
            sev_color = severity_styles.get(severity, HexColor('#6b7280'))
            
            elements.append(Paragraph(f"{i}. {finding.get('title', 'Untitled')}", heading_style))
            
            sev_style = ParagraphStyle('SevStyle', parent=body_style, textColor=sev_color, fontName='Helvetica-Bold')
            elements.append(Paragraph(f"<b>Severity:</b> {severity.upper()}", sev_style))
            elements.append(Spacer(1, 5))
            
            elements.append(Paragraph(f"<b>Description:</b><br/>{finding.get('description', 'No description provided.')}", body_style))
            elements.append(Paragraph(f"<b>Impact:</b><br/>{finding.get('impact', 'No impact description provided.')}", body_style))
            
            if cvss_scores and finding.get("cvss_vector"):
                cvss_text = f"<b>CVSS Score:</b> {finding.get('cvss_score', 'N/A')} ({finding.get('cvss_vector', 'N/A')})"
                elements.append(Paragraph(cvss_text, body_style))
            
            steps_text = "<b>Steps to Reproduce:</b><br/>"
            for j, step in enumerate(finding.get("steps_to_reproduce", []), 1):
                steps_text += f"{j}. {step}<br/>"
            elements.append(Paragraph(steps_text, body_style))
            
            if remediation and finding.get("remediation"):
                elements.append(Paragraph(f"<b>Remediation:</b><br/>{finding.get('remediation')}", body_style))
            
            if finding.get("cwe_id"):
                elements.append(Paragraph(f"<b>CWE:</b> {finding.get('cwe_id')}", body_style))
            if finding.get("cve_id"):
                elements.append(Paragraph(f"<b>CVE:</b> {finding.get('cve_id')}", body_style))
            
            elements.append(Spacer(1, 20))
            
            if i < len(findings):
                elements.append(Spacer(1, 10))
        
        elements.append(Spacer(1, 30))
        footer_style = ParagraphStyle('Footer', parent=body_style, fontSize=8, textColor=HexColor('#9ca3af'), alignment=TA_CENTER)
        elements.append(Paragraph(f"Generated by Bug Bounty Automator | {timestamp} | Total Findings: {len(findings)}", footer_style))
        
        doc.build(elements)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes

def get_report_generator() -> ReportGenerator:
    """Get report generator instance."""
    return ReportGenerator()
