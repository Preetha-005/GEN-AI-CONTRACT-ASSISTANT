"""
Export Manager Module
Handles PDF export and report generation
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import logging

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus import Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExportManager:
    """Manages export of analysis results to various formats"""
    
    def __init__(self):
        """Initialize export manager"""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom PDF styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#1E3A8A'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=HexColor('#1E3A8A'),
            spaceAfter=12,
            spaceBefore=20
        ))
        
        # Risk level styles
        self.styles.add(ParagraphStyle(
            name='HighRisk',
            parent=self.styles['Normal'],
            textColor=colors.red,
            fontSize=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='MediumRisk',
            parent=self.styles['Normal'],
            textColor=colors.orange,
            fontSize=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='LowRisk',
            parent=self.styles['Normal'],
            textColor=colors.green,
            fontSize=12
        ))
    
    def export_to_pdf(self, analysis_results: Dict, output_path: str) -> str:
        """
        Export complete analysis to PDF
        
        Args:
            analysis_results: Complete analysis results
            output_path: Path for output PDF
            
        Returns:
            Path to generated PDF
        """
        logger.info(f"Generating PDF report: {output_path}")
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        story = []
        
        # Title Page
        story.extend(self._create_title_page(analysis_results))
        story.append(PageBreak())
        
        # Executive Summary
        story.extend(self._create_executive_summary(analysis_results))
        story.append(PageBreak())
        
        # Risk Assessment Section
        story.extend(self._create_risk_section(analysis_results))
        story.append(PageBreak())
        
        # Clause Analysis Section
        story.extend(self._create_clause_section(analysis_results))
        story.append(PageBreak())
        
        # Recommendations
        story.extend(self._create_recommendations_section(analysis_results))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF report generated successfully: {output_path}")
        
        return output_path
    
    def _create_title_page(self, results: Dict) -> List:
        """Create title page elements"""
        elements = []
        
        # Title
        title = Paragraph(
            "Legal Contract Analysis Report",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 0.5*inch))
        
        # Metadata
        metadata = results.get('metadata', {})
        
        info_data = [
            ['Contract File:', metadata.get('filename', 'N/A')],
            ['Analysis Date:', datetime.now().strftime('%Y-%m-%d %H:%M')],
            ['Document Type:', metadata.get('file_type', 'N/A')],
            ['Language:', metadata.get('language', 'N/A').upper()],
            ['Page Count:', str(metadata.get('page_count', 'N/A'))],
            ['Word Count:', str(metadata.get('word_count', 'N/A'))]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#1E3A8A')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Disclaimer
        disclaimer = Paragraph(
            "<b>Disclaimer:</b> This analysis is generated by AI and should not be considered as legal advice. "
            "Please consult with a qualified legal professional before making any decisions based on this report.",
            self.styles['Normal']
        )
        elements.append(disclaimer)
        
        return elements
    
    def _create_executive_summary(self, results: Dict) -> List:
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Overall Risk
        risk_data = results.get('risk_assessment', {})
        overall_risk = risk_data.get('overall_risk_score', 0)
        risk_level = risk_data.get('overall_risk_level', 'low').upper()
        
        risk_color = {
            'HIGH': 'red',
            'MEDIUM': 'orange',
            'LOW': 'green'
        }.get(risk_level, 'black')
        
        summary_html = f"""
        <b>Overall Risk Assessment:</b> <font color="{risk_color}"><b>{risk_level}</b></font> 
        (Score: {overall_risk}/1.0)<br/><br/>
        """
        
        # Risk distribution
        distribution = risk_data.get('risk_distribution', {})
        summary_html += f"""
        <b>Risk Distribution:</b><br/>
        • High Risk Clauses: {distribution.get('high', 0)}<br/>
        • Medium Risk Clauses: {distribution.get('medium', 0)}<br/>
        • Low Risk Clauses: {distribution.get('low', 0)}<br/><br/>
        """
        
        # Contract classification
        if results.get('contract_classification'):
            classification = results['contract_classification']
            summary_html += f"""
            <b>Contract Type:</b> {classification.get('contract_type', 'Unknown')}<br/>
            <b>Confidence:</b> {classification.get('confidence', 'N/A')}<br/><br/>
            """
        
        # Summary text
        if results.get('contract_summary'):
            summary_text = results['contract_summary']
            summary_html += f"""
            <b>Contract Summary:</b><br/>
            {summary_text[:500]}{'...' if len(summary_text) > 500 else ''}
            """
        
        elements.append(Paragraph(summary_html, self.styles['Normal']))
        
        return elements
    
    def _create_risk_section(self, results: Dict) -> List:
        """Create risk assessment section"""
        elements = []
        
        elements.append(Paragraph("Risk Assessment Details", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        risk_data = results.get('risk_assessment', {})
        
        # Risk Flags
        risk_flags = risk_data.get('risk_flags', [])
        if risk_flags:
            elements.append(Paragraph("<b>Critical Risk Flags:</b>", self.styles['Heading3']))
            
            for flag in risk_flags[:10]:  # Top 10 flags
                severity = flag.get('severity', 'medium').upper()
                flag_html = f"""
                <b>[{severity}]</b> {flag.get('title', 'N/A')}<br/>
                {flag.get('description', 'N/A')}<br/>
                <i>Recommendation: {flag.get('recommendation', 'N/A')}</i>
                """
                elements.append(Paragraph(flag_html, self.styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
        
        # Unfavorable Terms
        unfavorable = risk_data.get('unfavorable_terms', [])
        if unfavorable:
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("<b>Unfavorable Terms Identified:</b>", self.styles['Heading3']))
            
            for term in unfavorable[:5]:  # Top 5
                term_html = f"""
                <b>{term.get('term_type', 'N/A')}</b> (Clause {term.get('clause_number', 'N/A')})<br/>
                {term.get('explanation', 'N/A')}<br/>
                <i>Alternative: {term.get('alternative', 'N/A')}</i>
                """
                elements.append(Paragraph(term_html, self.styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _create_clause_section(self, results: Dict) -> List:
        """Create clause analysis section"""
        elements = []
        
        elements.append(Paragraph("Clause-by-Clause Analysis", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        # High-risk clauses
        risk_data = results.get('risk_assessment', {})
        high_risk_clauses = risk_data.get('high_risk_clauses', [])[:10]  # Top 10
        
        if high_risk_clauses:
            elements.append(Paragraph("<b>High-Risk Clauses Requiring Attention:</b>", self.styles['Heading3']))
            
            for clause in high_risk_clauses:
                clause_html = f"""
                <b>Clause {clause.get('clause_number', 'N/A')}</b> 
                (Risk Score: {clause.get('risk_score', 0)})<br/>
                <b>Categories:</b> {', '.join(clause.get('risk_categories', []))}<br/>
                <b>Content:</b> {clause.get('content', '')[:300]}...
                """
                elements.append(Paragraph(clause_html, self.styles['Normal']))
                elements.append(Spacer(1, 0.15*inch))
        
        # Obligations, Rights, Prohibitions
        nlp_data = results.get('nlp_analysis', {})
        
        if nlp_data.get('obligations'):
            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("<b>Key Obligations:</b>", self.styles['Heading3']))
            for item in nlp_data['obligations'][:5]:
                elements.append(Paragraph(
                    f"• {item.get('content', '')[:200]}...",
                    self.styles['Normal']
                ))
        
        return elements
    
    def _create_recommendations_section(self, results: Dict) -> List:
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        elements.append(Spacer(1, 0.2*inch))
        
        risk_data = results.get('risk_assessment', {})
        recommendations = risk_data.get('recommendations', [])
        
        if recommendations:
            for idx, rec in enumerate(recommendations, 1):
                elements.append(Paragraph(f"{idx}. {rec}", self.styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
        else:
            elements.append(Paragraph(
                "No specific recommendations at this time. Review all flagged items above.",
                self.styles['Normal']
            ))
        
        elements.append(Spacer(1, 0.3*inch))
        elements.append(Paragraph(
            "<b>Next Steps:</b><br/>"
            "1. Review all high-risk clauses with your legal advisor<br/>"
            "2. Consider suggested alternative clauses<br/>"
            "3. Negotiate unfavorable terms before signing<br/>"
            "4. Ensure all critical clauses are present and clear",
            self.styles['Normal']
        ))
        
        return elements
    
    def export_to_json(self, analysis_results: Dict, output_path: str) -> str:
        """
        Export analysis results to JSON
        
        Args:
            analysis_results: Complete analysis results
            output_path: Path for output JSON
            
        Returns:
            Path to generated JSON
        """
        logger.info(f"Exporting to JSON: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON export completed: {output_path}")
        return output_path
    
    def export_to_txt(self, analysis_results: Dict, output_path: str) -> str:
        """
        Export simplified analysis to text file
        
        Args:
            analysis_results: Complete analysis results
            output_path: Path for output text file
            
        Returns:
            Path to generated text file
        """
        logger.info(f"Exporting to TXT: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("LEGAL CONTRACT ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            # Metadata
            metadata = analysis_results.get('metadata', {})
            f.write(f"File: {metadata.get('filename', 'N/A')}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"Language: {metadata.get('language', 'N/A').upper()}\n\n")
            
            # Risk Summary
            risk_data = analysis_results.get('risk_assessment', {})
            f.write("-" * 80 + "\n")
            f.write("RISK ASSESSMENT\n")
            f.write("-" * 80 + "\n")
            f.write(f"Overall Risk Level: {risk_data.get('overall_risk_level', 'N/A').upper()}\n")
            f.write(f"Risk Score: {risk_data.get('overall_risk_score', 0)}/1.0\n\n")
            
            # Recommendations
            recommendations = risk_data.get('recommendations', [])
            if recommendations:
                f.write("\nRECOMMENDATIONS:\n")
                for idx, rec in enumerate(recommendations, 1):
                    f.write(f"{idx}. {rec}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("End of Report\n")
        
        logger.info(f"TXT export completed: {output_path}")
        return output_path


if __name__ == "__main__":
    # Test the export manager
    manager = ExportManager()
    print("Export Manager initialized successfully")
