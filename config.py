"""
Configuration settings for Legal Contract Assistant
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
AUDIT_LOG_DIR = DATA_DIR / "audit_logs"
TEMPLATES_DIR = BASE_DIR / "templates"

# Create directories if they don't exist
AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # "anthropic" or "openai"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Model Settings
CLAUDE_MODEL = "claude-3-sonnet-20240229"
GPT_MODEL = "gpt-4-turbo-preview"

# Contract Types
CONTRACT_TYPES = [
    "Employment Agreement",
    "Vendor Contract",
    "Lease Agreement",
    "Partnership Deed",
    "Service Contract",
    "Non-Disclosure Agreement (NDA)",
    "Memorandum of Understanding (MoU)",
    "Purchase Order",
    "Consultancy Agreement",
    "License Agreement"
]

# Risk Categories and Keywords
RISK_CATEGORIES = {
    "manipulative_language": {
        "keywords": [
            # Severe Psychological Manipulation (Weight 1.0)
            "custody", "temporary custody", "relinquishes", "relinquish", "knowingly accepts", 
            "full awareness", "sole responsibility", "personal accountability", "weight of", 
            "responsibility over denial", "no external system", "no permission", "emotional fatigue", 
            "blame circumstances", "resilience is built", "facing what", "scars included", 
            "unknowingly agrees", "illusion of control", "no protection", "no refunds", 
            "no guarantee", "validation may be absent", "disguised as discomfort", "without warning", 
            "uncomfortable truth", "psychological", "emotional manipulation", "mental state"
        ],
        "weight": 1.0
    },
    "emotional_pressure": {
        "keywords": [
            # Moderate Emotional Pressure (Weight 0.55 - ensures Medium Risk cap)
            "unmet expectations", "loneliness", "self-confrontation", "unresolved thoughts", 
            "delayed ambitions", "fear of falling behind", "worthlessness", "self-doubt", 
            "controlled exposure", "consents to", "no reassurance", "no clear timeline", 
            "repeated failure", "comparison may occur", "confidence may dip", "silence from others", 
            "avoiding truth", "prolong uncertainty", "discomfort may be necessary"
        ],
        "weight": 0.55
    },
    "penalty_clause": {
        "keywords": ["penalty", "liquidated damages", "fine", "forfeit", "deduction"],
        "weight": 0.9
    },
    "indemnity_clause": {
        "keywords": ["indemnify", "indemnification", "hold harmless", "defend"],
        "weight": 0.85
    },
    "unilateral_termination": {
        "keywords": ["terminate at will", "without cause", "sole discretion", "unilateral"],
        "weight": 0.95
    },
    "arbitration": {
        "keywords": ["arbitration", "dispute resolution", "jurisdiction", "governing law"],
        "weight": 0.5
    },
    "auto_renewal": {
        "keywords": ["auto-renew", "automatic renewal", "evergreen", "perpetual"],
        "weight": 0.7
    },
    "lock_in": {
        "keywords": ["lock-in", "minimum period", "cannot terminate", "binding period"],
        "weight": 0.8
    },
    "non_compete": {
        "keywords": ["non-compete", "non-competition", "restraint of trade", "exclusivity"],
        "weight": 0.85
    },
    "ip_transfer": {
        "keywords": ["intellectual property", "IP rights", "copyright", "ownership", "assignment of rights"],
        "weight": 0.9
    },
    "liability_cap": {
        "keywords": ["limitation of liability", "liability cap", "maximum liability", "aggregate liability"],
        "weight": 0.6
    },
    "force_majeure": {
        "keywords": ["force majeure", "act of god", "unforeseeable circumstances"],
        "weight": 0.4
    }
}

# NLP Settings
SPACY_MODEL = "en_core_web_lg"
MIN_CLAUSE_LENGTH = 20  # Minimum characters for a valid clause
MAX_CLAUSE_LENGTH = 5000  # Maximum characters for a single clause

# Risk Scoring Thresholds
RISK_THRESHOLDS = {
    "low": (0, 0.3),
    "medium": (0.3, 0.6),
    "high": (0.6, 1.1)
}

# Entity Types to Extract
ENTITY_TYPES = [
    "PERSON",           # Party names
    "ORG",              # Organizations
    "DATE",             # Important dates
    "MONEY",            # Financial amounts
    "GPE",              # Jurisdiction/location
    "CARDINAL",         # Numbers
    "PERCENT",          # Percentages
    "LAW",              # Legal references
]

# Supported Languages
SUPPORTED_LANGUAGES = ["en", "hi"]  # English and Hindi

# Document Processing
MAX_FILE_SIZE_MB = 10
SUPPORTED_FORMATS = [".pdf", ".docx", ".doc", ".txt"]

# UI Configuration
APP_TITLE = "GenAI Legal Contract Assistant"
APP_SUBTITLE = "Smart Contract Analysis for Indian SMEs"
THEME_COLOR = "#1E3A8A"

# Export Settings
EXPORT_FORMATS = ["PDF", "JSON", "TXT"]
REPORT_TEMPLATE = "standard_report"

# Audit Settings
ENABLE_AUDIT_TRAIL = True
AUDIT_LOG_RETENTION_DAYS = 90
