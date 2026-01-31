"""
GenAI Legal Contract Assistant - Main Application
Streamlit-based UI for contract analysis
"""
import streamlit as st
import sys
from pathlib import Path
import tempfile
from datetime import datetime
import json

# Add modules to path
sys.path.append(str(Path(__file__).parent))

import config
from modules.document_parser import DocumentParser
from modules.nlp_analyzer import NLPAnalyzer
from modules.risk_assessor import RiskAssessor
from modules.llm_processor import LLMProcessor
from modules.template_matcher import TemplateMatcher
from modules.export_manager import ExportManager
from utils.audit_logger import AuditLogger
from utils.text_processor import TextProcessor

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .risk-high {
        color: #dc2626;
        font-weight: bold;
    }
    .risk-medium {
        color: #ea580c;
        font-weight: bold;
    }
    .risk-low {
        color: #16a34a;
        font-weight: bold;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .metric-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None


def render_header():
    """Render application header"""
    st.title(config.APP_TITLE)
    st.markdown(f"**{config.APP_SUBTITLE}**")
    st.markdown("---")


def render_sidebar():
    """Render sidebar with instructions and settings"""
    with st.sidebar:
        st.header("How to Use")
        st.markdown("""
        1. **Upload Contract**: Upload PDF, DOCX, or TXT file
        2. **Analyze**: Click 'Analyze Contract' button
        3. **Review Results**: Examine risk assessment and recommendations
        4. **Export Report**: Download PDF report for legal review
        """)
        
        st.markdown("---")
        
        st.header("Settings")
        
        # LLM Provider selection
        llm_provider = st.selectbox(
            "LLM Provider",
            options=["anthropic", "openai"],
            index=0 if config.LLM_PROVIDER == "anthropic" else 1,
            help="Select the LLM provider for legal reasoning"
        )
        
        # Analysis depth
        analysis_depth = st.select_slider(
            "Analysis Depth",
            options=["Quick", "Standard", "Comprehensive"],
            value="Standard",
            help="Choose analysis thoroughness"
        )
        
        # Language
        language = st.selectbox(
            "Output Language",
            options=["English", "Hindi (Limited)"],
            index=0
        )
        
        st.markdown("---")
        
        st.header("About")
        st.info("""
        This AI-powered legal assistant helps SMEs understand contracts and identify risks.
        
        **Features:**
        - Risk Assessment
        - Plain Language Explanations
        - Compliance Checking
        - Alternative Clause Suggestions
        """)
        
        st.warning("⚠️ This is not legal advice. Consult a qualified lawyer before making decisions.")
        
        return llm_provider, analysis_depth, language


def upload_contract():
    """Handle contract file upload"""
    st.header("Upload Contract")
    
    uploaded_file = st.file_uploader(
        "Choose a contract file",
        type=['pdf', 'docx', 'doc', 'txt'],
        help=f"Maximum file size: {config.MAX_FILE_SIZE_MB}MB"
    )
    
    return uploaded_file


def analyze_contract(uploaded_file, llm_provider, analysis_depth, language):
    """Perform complete contract analysis"""
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Initialize components
        status_text.text("Initializing analyzers...")
        parser = DocumentParser()
        nlp_analyzer = NLPAnalyzer()
        risk_assessor = RiskAssessor(language=language)
        template_matcher = TemplateMatcher()
        audit_logger = AuditLogger()
        
        try:
            llm_processor = LLMProcessor(provider=llm_provider, language=language)
            llm_available = True
        except Exception as e:
            st.warning(f"LLM not available: {e}. Proceeding with NLP-only analysis.")
            llm_available = False
        
        progress_bar.progress(10)
        
        # Step 1: Parse document
        status_text.text("📄 Parsing document...")
        parsed_doc = parser.parse_document(tmp_path)
        progress_bar.progress(25)
        
        # Step 2: Extract clauses
        status_text.text("📋 Extracting clauses...")
        clauses = parser.extract_clauses(parsed_doc['text'])
        sections = parser.extract_sections(parsed_doc['text'])
        progress_bar.progress(35)
        
        # Step 3: NLP Analysis
        status_text.text("🔍 Performing NLP analysis...")
        nlp_results = nlp_analyzer.analyze_document(parsed_doc['text'], clauses)
        progress_bar.progress(50)
        
        # Step 4: Risk Assessment
        status_text.text("⚠️ Assessing risks...")
        risk_results = risk_assessor.assess_contract_risk(clauses, nlp_results)
        progress_bar.progress(70)
        
        # Step 5: Template Matching
        status_text.text("📝 Matching templates...")
        template_matches = template_matcher.match_clauses_to_templates(clauses)
        progress_bar.progress(80)
        
        # Step 6: LLM Processing (if available)
        contract_summary = None
        contract_classification = None
        clause_explanations = []
        
        if llm_available and analysis_depth in ["Standard", "Comprehensive"]:
            status_text.text("🤖 Generating AI insights...")
            
            # Classify contract
            contract_classification = llm_processor.classify_contract_type(parsed_doc['text'])
            
            # Generate summary
            contract_summary = llm_processor.generate_contract_summary(
                parsed_doc['text'], 
                parsed_doc['metadata']
            )
            
            # Explain high-risk clauses
            if analysis_depth == "Comprehensive":
                high_risk_clauses = risk_results.get('high_risk_clauses', [])[:5]
                clause_explanations = llm_processor.batch_explain_clauses(high_risk_clauses, limit=5)
        
        progress_bar.progress(95)
        
        # Compile results
        analysis_results = {
            'metadata': {**parsed_doc['metadata'], 'output_language': language},
            'document_text': parsed_doc['text'],
            'sections': sections,
            'clauses': clauses,
            'nlp_analysis': nlp_results,
            'risk_assessment': risk_results,
            'template_matches': template_matches,
            'contract_classification': contract_classification,
            'contract_summary': contract_summary,
            'clause_explanations': clause_explanations,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Create audit log
        audit_logger.log_analysis(
            document_info={
                'filename': uploaded_file.name,
                'file_path': tmp_path,
                'file_size': uploaded_file.size,
                'file_type': Path(uploaded_file.name).suffix
            },
            analysis_results=analysis_results
        )
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)
        
        return analysis_results
    
    except Exception as e:
        st.error(f"Error during analysis: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None


def display_results(results):
    """Display analysis results"""
    
    # Overview Section
    st.header("Analysis Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Overall Risk",
            results['risk_assessment']['overall_risk_level'].upper(),
            f"{results['risk_assessment']['overall_risk_score']}/1.0"
        )
    
    with col2:
        high_risk = results['risk_assessment']['risk_distribution']['high']
        st.metric("High Risk Clauses", high_risk)
    
    with col3:
        flags = len(results['risk_assessment']['risk_flags'])
        st.metric("Risk Flags", flags)
    
    with col4:
        clauses_count = len(results['clauses'])
        st.metric("Total Clauses", clauses_count)
    
    st.markdown("---")
    
    # Contract Classification
    if results.get('contract_classification'):
        st.header("Contract Information")
        classification = results['contract_classification']
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Contract Type:** {classification.get('contract_type', 'Unknown')}")
            st.write(f"**Confidence:** {classification.get('confidence', 'N/A')}")
        with col2:
            st.write(f"**Language:** {results['metadata'].get('language', 'Unknown').upper()}")
            st.write(f"**Word Count:** {results['metadata'].get('word_count', 'N/A'):,}")
    
    # Contract Summary
    if results.get('contract_summary'):
        with st.expander("Contract Summary", expanded=True):
            st.write(results['contract_summary'])
    
    st.markdown("---")
    
    # Risk Assessment
    st.header("Risk Assessment")
    
    # Risk level indicator
    risk_level = results['risk_assessment']['overall_risk_level']
    
    if risk_level == 'high':
        st.error("🚨 **HIGH RISK CONTRACT** - Exercise extreme caution before signing")
    elif risk_level == 'medium':
        st.warning("⚠️ **MEDIUM RISK CONTRACT** - Review carefully and consider legal advice")
    else:
        st.success("✅ **LOW RISK CONTRACT** - Appears manageable, still review thoroughly")
    
    # Risk Flags
    risk_flags = results['risk_assessment']['risk_flags']
    if risk_flags:
        with st.expander(f"Risk Flags ({len(risk_flags)})", expanded=True):
            for flag in risk_flags:
                severity = flag.get('severity', 'medium')
                # Determine icon based on severity
                if severity == 'high':
                    icon = "🔴"
                elif severity == 'medium':
                    icon = "🟡"
                else:
                    icon = "🟢"
                
                st.markdown(f"""
                {icon} **{flag.get('title', 'Unknown Risk')}** [{severity.upper()}]
                
                {flag.get('description', 'No description')}
                
                💡 *Recommendation:* {flag.get('recommendation', 'No recommendation')}
                """)
                st.markdown("---")
    
    # Unfavorable Terms
    unfavorable = results['risk_assessment']['unfavorable_terms']
    if unfavorable:
        with st.expander(f"Unfavorable Terms ({len(unfavorable)})", expanded=False):
            for term in unfavorable:
                st.markdown(f"""
                **{term.get('term_type')}** (Clause {term.get('clause_number')})
                
                ⚠️ {term.get('explanation')}
                
                ✏️ *Alternative:* {term.get('alternative')}
                """)
                st.markdown("---")
    
    # Recommendations
    with st.expander("Recommendations", expanded=True):
        recommendations = results['risk_assessment']['recommendations']
        for rec in recommendations:
            st.write(rec)
    
    st.markdown("---")
    
    # Detailed Analysis Tabs
    st.header("Detailed Analysis")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Clauses", "Obligations & Rights", "Entities", "Templates"])
    
    with tab1:
        st.subheader("High-Risk Clauses")
        high_risk_clauses = results['risk_assessment']['high_risk_clauses']
        
        if high_risk_clauses:
            for clause in high_risk_clauses[:10]:
                with st.expander(f"Clause {clause['clause_number']} - Risk: {clause['risk_score']}"):
                    st.write(f"**Risk Categories:** {', '.join(clause['risk_categories'])}")
                    st.write("**Content:**")
                    st.write(clause['content'][:500] + ('...' if len(clause['content']) > 500 else ''))
                    
                    # Show explanation if available
                    if results.get('clause_explanations'):
                        for exp in results['clause_explanations']:
                            if exp['clause_id'] == clause['clause_id']:
                                st.info(f"**AI Explanation:** {exp['explanation']['explanation']}")
        else:
            st.success("No high-risk clauses identified!")
    
    with tab2:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Obligations")
            obligations = results['nlp_analysis']['obligations']
            st.write(f"Found {len(obligations)} obligation clauses")
            for ob in obligations[:5]:
                st.write(f"- {ob['clause_number']}")
        
        with col2:
            st.subheader("Rights")
            rights = results['nlp_analysis']['rights']
            st.write(f"Found {len(rights)} rights clauses")
            for r in rights[:5]:
                st.write(f"- {r['clause_number']}")
        
        with col3:
            st.subheader("Prohibitions")
            prohibitions = results['nlp_analysis']['prohibitions']
            st.write(f"Found {len(prohibitions)} prohibitions")
            for p in prohibitions[:5]:
                st.write(f"- {p['clause_number']}")
    
    with tab3:
        st.subheader("Extracted Entities")
        
        # Parties
        parties = results['nlp_analysis']['parties']
        if parties:
            st.write("**Parties to the Contract:**")
            for party in parties:
                st.write(f"- {party['name']} ({party['type']})")
        
        # Dates
        dates = results['nlp_analysis']['dates']
        if dates:
            st.write("**Important Dates:**")
            for date in dates[:10]:
                st.write(f"- {date['date']}: {date['context'][:100]}...")
        
        # Amounts
        amounts = results['nlp_analysis']['amounts']
        if amounts:
            st.write("**Financial Terms:**")
            for amount in amounts[:10]:
                st.write(f"- {amount['amount']} ({amount['type']}): {amount['context'][:100]}...")
    
    with tab4:
        st.subheader("Template Matches")
        template_matches = results['template_matches']
        
        if template_matches:
            st.write(f"Found {len(template_matches)} clauses matching standard templates")
            
            for match in template_matches[:10]:
                with st.expander(f"{match['template_title']} - Similarity: {match['similarity_score']}"):
                    st.write(f"**Clause {match['clause_number']} matches this template type**")
                    st.write("**Recommended Template:**")
                    st.info(match['template_text'])
                    st.write("**Key Points:**")
                    for point in match['key_points']:
                        st.write(f"- {point}")
        else:
            st.info("No template matches found. Consider using standard SME-friendly clauses.")


def export_results(results):
    """Handle export functionality"""
    st.header("Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    export_manager = ExportManager()
    
    with col1:
        if st.button("Export PDF Report"):
            with st.spinner("Generating PDF..."):
                pdf_path = f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                export_manager.export_to_pdf(results, pdf_path)
                
                with open(pdf_path, 'rb') as f:
                    st.download_button(
                        "Download PDF",
                        f,
                        file_name=pdf_path,
                        mime="application/pdf"
                    )
                
                Path(pdf_path).unlink(missing_ok=True)
    
    with col2:
        if st.button("Export JSON Data"):
            json_data = json.dumps(results, indent=2, default=str)
            st.download_button(
                "Download JSON",
                json_data,
                file_name=f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("Export Text Summary"):
            txt_path = f"contract_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            export_manager.export_to_txt(results, txt_path)
            
            with open(txt_path, 'r', encoding='utf-8') as f:
                st.download_button(
                    "Download TXT",
                    f,
                    file_name=txt_path,
                    mime="text/plain"
                )
            
            Path(txt_path).unlink(missing_ok=True)


def main():
    """Main application"""
    initialize_session_state()
    render_header()
    llm_provider, analysis_depth, language = render_sidebar()
    
    # File upload
    uploaded_file = upload_contract()
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Analyze button
        if st.button("Analyze Contract", type="primary"):
            with st.spinner("Analyzing contract..."):
                results = analyze_contract(uploaded_file, llm_provider, analysis_depth, language)
                
                if results:
                    st.session_state.analysis_results = results
                    st.session_state.analysis_complete = True
                    st.session_state.uploaded_file_name = uploaded_file.name
                    st.success("Analysis complete!")
                    st.rerun()
    
    # Display results if available
    if st.session_state.analysis_complete and st.session_state.analysis_results:
        st.markdown("---")
        display_results(st.session_state.analysis_results)
        st.markdown("---")
        export_results(st.session_state.analysis_results)
        
        # Reset button
        if st.button("Analyze Another Contract"):
            st.session_state.analysis_complete = False
            st.session_state.analysis_results = None
            st.session_state.uploaded_file_name = None
            st.rerun()
    
    elif not uploaded_file:
        # Show welcome message
        st.info("""
        ### Welcome to the GenAI Legal Contract Assistant!
        
        This tool helps small and medium business owners:
        - Understand complex legal contracts
        - Identify potential risks and unfavorable terms
        - Get plain language explanations of legal clauses
        - Receive actionable recommendations
        
        **To get started:**
        1. Upload your contract (PDF, DOCX, or TXT format)
        2. Click 'Analyze Contract'
        3. Review the comprehensive analysis
        4. Export the report for your records
        
        **Note:** This tool is designed for Indian SMEs and supports both English and Hindi contracts.
        """)


if __name__ == "__main__":
    main()
