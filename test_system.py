"""
Test Suite for Legal Contract Assistant
Run basic tests to verify installation and functionality
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    
    try:
        import streamlit
        print("✓ Streamlit installed")
    except ImportError:
        print("✗ Streamlit not found")
        return False
    
    try:
        import spacy
        print("✓ spaCy installed")
    except ImportError:
        print("✗ spaCy not found")
        return False
    
    try:
        import nltk
        print("✓ NLTK installed")
    except ImportError:
        print("✗ NLTK not found")
        return False
    
    try:
        import PyPDF2
        import pdfplumber
        print("✓ PDF libraries installed")
    except ImportError:
        print("✗ PDF libraries not found")
        return False
    
    try:
        from docx import Document
        print("✓ python-docx installed")
    except ImportError:
        print("✗ python-docx not found")
        return False
    
    try:
        from reportlab.lib.pagesizes import letter
        print("✓ ReportLab installed")
    except ImportError:
        print("✗ ReportLab not found")
        return False
    
    return True


def test_spacy_model():
    """Test if spaCy model is available"""
    print("\nTesting spaCy model...")
    
    try:
        import spacy
        nlp = spacy.load("en_core_web_lg")
        print("✓ spaCy en_core_web_lg model loaded")
        return True
    except OSError:
        print("✗ spaCy model not found")
        print("  Run: python -m spacy download en_core_web_lg")
        
        # Try smaller model
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✓ spaCy en_core_web_sm model loaded (fallback)")
            return True
        except OSError:
            print("✗ No spaCy model found")
            return False


def test_nltk_data():
    """Test if NLTK data is available"""
    print("\nTesting NLTK data...")
    
    try:
        import nltk
        nltk.data.find('tokenizers/punkt')
        print("✓ NLTK punkt tokenizer available")
    except LookupError:
        print("✗ NLTK punkt not found")
        print("  Run: python -c \"import nltk; nltk.download('punkt')\"")
        return False
    
    try:
        nltk.data.find('corpora/stopwords')
        print("✓ NLTK stopwords available")
    except LookupError:
        print("✗ NLTK stopwords not found")
        print("  Run: python -c \"import nltk; nltk.download('stopwords')\"")
        return False
    
    return True


def test_modules():
    """Test if custom modules can be imported"""
    print("\nTesting custom modules...")
    
    try:
        from modules.document_parser import DocumentParser
        print("✓ DocumentParser module")
    except Exception as e:
        print(f"✗ DocumentParser failed: {e}")
        return False
    
    try:
        from modules.nlp_analyzer import NLPAnalyzer
        print("✓ NLPAnalyzer module")
    except Exception as e:
        print(f"✗ NLPAnalyzer failed: {e}")
        return False
    
    try:
        from modules.risk_assessor import RiskAssessor
        print("✓ RiskAssessor module")
    except Exception as e:
        print(f"✗ RiskAssessor failed: {e}")
        return False
    
    try:
        from modules.template_matcher import TemplateMatcher
        print("✓ TemplateMatcher module")
    except Exception as e:
        print(f"✗ TemplateMatcher failed: {e}")
        return False
    
    try:
        from modules.export_manager import ExportManager
        print("✓ ExportManager module")
    except Exception as e:
        print(f"✗ ExportManager failed: {e}")
        return False
    
    try:
        from utils.text_processor import TextProcessor
        print("✓ TextProcessor utility")
    except Exception as e:
        print(f"✗ TextProcessor failed: {e}")
        return False
    
    try:
        from utils.audit_logger import AuditLogger
        print("✓ AuditLogger utility")
    except Exception as e:
        print(f"✗ AuditLogger failed: {e}")
        return False
    
    return True


def test_config():
    """Test configuration file"""
    print("\nTesting configuration...")
    
    try:
        import config
        print("✓ Config file loaded")
        print(f"  - Risk categories: {len(config.RISK_CATEGORIES)}")
        print(f"  - Contract types: {len(config.CONTRACT_TYPES)}")
        print(f"  - Supported formats: {config.SUPPORTED_FORMATS}")
        return True
    except Exception as e:
        print(f"✗ Config failed: {e}")
        return False


def test_llm_connection():
    """Test LLM API connection (optional)"""
    print("\nTesting LLM connection (optional)...")
    
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
            print("✓ Anthropic API key configured")
        elif openai_key and openai_key != "your_openai_api_key_here":
            print("✓ OpenAI API key configured")
        else:
            print("⚠ No LLM API key configured (NLP-only mode available)")
            print("  Create .env file with ANTHROPIC_API_KEY or OPENAI_API_KEY")
        
        return True
    except Exception as e:
        print(f"⚠ Could not check LLM configuration: {e}")
        return True  # Not critical


def test_sample_contract():
    """Test parsing of sample contract"""
    print("\nTesting sample contract parsing...")
    
    sample_path = Path(__file__).parent / "sample_contracts" / "unfavorable_service_agreement.txt"
    
    if not sample_path.exists():
        print("✗ Sample contract not found")
        return False
    
    try:
        from modules.document_parser import DocumentParser
        parser = DocumentParser()
        
        result = parser.parse_document(str(sample_path))
        print("✓ Sample contract parsed successfully")
        print(f"  - Word count: {result['metadata']['word_count']}")
        print(f"  - Language: {result['metadata']['language']}")
        
        clauses = parser.extract_clauses(result['text'])
        print(f"  - Clauses extracted: {len(clauses)}")
        
        return True
    except Exception as e:
        print(f"✗ Sample parsing failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Legal Contract Assistant - System Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Package Imports", test_imports()))
    results.append(("spaCy Model", test_spacy_model()))
    results.append(("NLTK Data", test_nltk_data()))
    results.append(("Custom Modules", test_modules()))
    results.append(("Configuration", test_config()))
    results.append(("LLM Connection", test_llm_connection()))
    results.append(("Sample Contract", test_sample_contract()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<40} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready to use.")
        print("\nRun the application with: streamlit run app.py")
    else:
        print("\n⚠ Some tests failed. Please install missing dependencies.")
        print("See SETUP_GUIDE.md for installation instructions.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
