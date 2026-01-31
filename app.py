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

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title=config.APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# Session State
# --------------------------------------------------
def initialize_session_state():
    defaults = {
        "analysis_complete": False,
        "analysis_results": None,
        "uploaded_file_name": None,
        "llm_provider": config.LLM_PROVIDER or "anthropic",
        "analysis_depth": "Standard",
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# --------------------------------------------------
# UI Helpers
# --------------------------------------------------
def render_header():
    st.title(config.APP_TITLE)
    st.markdown(f"**{config.APP_SUBTITLE}**")
    st.divider()


def render_sidebar():
    with st.sidebar:
        st.header("How to Use")
        st.markdown("""
        1. Upload contract  
        2. Click **Analyze Contract**  
        3. Review risks and clauses  
        4. Export report  
        """)

        st.divider()
        st.header("Settings")

        llm_provider = st.selectbox(
            "LLM Provider",
            options=["anthropic", "openai"],
            key="llm_provider",
        )

        analysis_depth = st.selectbox(
            "Analysis Depth",
            options=["Quick", "Standard", "Comprehensive"],
            key="analysis_depth",
        )

        st.divider()
        st.warning("⚠️ This is not legal advice.")

        return llm_provider, analysis_depth


def upload_contract():
    st.header("Upload Contract")
    return st.file_uploader(
        "Choose a contract file",
        type=["pdf", "docx", "doc", "txt"]
    )


# --------------------------------------------------
# Analysis Pipeline
# --------------------------------------------------
def analyze_contract(uploaded_file, llm_provider, analysis_depth):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        parser = DocumentParser()
        nlp_analyzer = NLPAnalyzer()
        risk_assessor = RiskAssessor()
        template_matcher = TemplateMatcher()
        audit_logger = AuditLogger()

        try:
            llm_processor = LLMProcessor(provider=llm_provider)
            llm_available = True
        except Exception:
            llm_available = False

        parsed_doc = parser.parse_document(tmp_path)
        clauses = parser.extract_clauses(parsed_doc["text"])
        sections = parser.extract_sections(parsed_doc["text"])

        nlp_results = nlp_analyzer.analyze_document(parsed_doc["text"], clauses)
        risk_results = risk_assessor.assess_contract_risk(clauses, nlp_results)
        template_matches = template_matcher.match_clauses_to_templates(clauses)

        contract_summary = None
        contract_classification = None

        if llm_available and analysis_depth != "Quick":
            contract_classification = llm_processor.classify_contract_type(parsed_doc["text"])
            contract_summary = llm_processor.generate_contract_summary(
                parsed_doc["text"],
                parsed_doc["metadata"]
            )

        results = {
            "metadata": parsed_doc["metadata"],
            "document_text": parsed_doc["text"],
            "sections": sections,
            "clauses": clauses,
            "nlp_analysis": nlp_results,
            "risk_assessment": risk_results,
            "template_matches": template_matches,
            "contract_summary": contract_summary,
            "contract_classification": contract_classification,
            "analysis_timestamp": datetime.now().isoformat(),
        }

        audit_logger.log_analysis(
            document_info={
                "filename": uploaded_file.name,
                "file_path": tmp_path,
            },
            analysis_results=results,
        )

        Path(tmp_path).unlink(missing_ok=True)
        return results

    except Exception as e:
        st.error(f"Error during analysis: {e}")
        st.exception(e)
        return None


# --------------------------------------------------
# Display Results
# --------------------------------------------------
def display_results(results):
    st.header("Analysis Overview")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Risk", results["risk_assessment"]["overall_risk_level"].upper())
    with col2:
        st.metric("High Risk Clauses", len(results["risk_assessment"]["high_risk_clauses"]))
    with col3:
        st.metric("Total Clauses", len(results["clauses"]))

    st.divider()

    if results.get("contract_summary"):
        st.subheader("Contract Summary")
        st.write(results["contract_summary"])

    st.divider()

    st.subheader("Key Legal Terms")
    for term in results["nlp_analysis"]["key_terms"][:10]:
        st.write(f"- **{term['term']}** ({term['count']})")


# --------------------------------------------------
# Main
# --------------------------------------------------
def main():
    initialize_session_state()
    render_header()

    llm_provider, analysis_depth = render_sidebar()
    uploaded_file = upload_contract()

    if uploaded_file and st.button("Analyze Contract", type="primary"):
        with st.spinner("Analyzing..."):
            results = analyze_contract(uploaded_file, llm_provider, analysis_depth)
            if results:
                st.session_state.analysis_results = results
                st.session_state.analysis_complete = True
                st.rerun()

    if st.session_state.analysis_complete:
        display_results(st.session_state.analysis_results)


if __name__ == "__main__":
    main()
