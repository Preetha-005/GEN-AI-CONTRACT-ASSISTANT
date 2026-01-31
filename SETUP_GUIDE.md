# GenAI Legal Contract Assistant - Setup Guide

## Quick Start

### Step 1: Create and Activate Virtual Environment
It is highly recommended to use a virtual environment to avoid dependency conflicts.

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
.\venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

### Step 2: Install Python Packages
Once the environment is activated, install the required packages.

```bash
# Install requirements
pip install -r requirements.txt

# Handle click version compatibility (if needed)
pip uninstall click -y
pip install click==8.1.7
```

### Step 3: Download NLP Assets
Download the language models and datasets required for contract analysis.

```bash
# Download spaCy language model
python -m spacy download en_core_web_lg

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"
```

### Step 4: Configure API Keys
Create a `.env` file in the project root :

```bash
ANTHROPIC_API_KEY=your_anthropic_key_here
# OR
OPENAI_API_KEY=your_openai_key_here

LLM_PROVIDER=anthropic  # or "openai"
```

### Step 5: Run the Application
Start the Streamlit server to launch the assistant.

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Testing the System

### Test with Sample Contract

A sample unfavorable service agreement is provided in `sample_contracts/unfavorable_service_agreement.txt`

This contract intentionally contains multiple high-risk clauses for testing:
- Unlimited liability
- Unilateral termination rights
- Broad IP transfer
- Excessive non-compete period
- Auto-renewal clauses
- One-sided indemnification

Upload this file to test the risk detection capabilities.

## Features Demonstration

### 1. Contract Analysis
- Upload any PDF, DOCX, or TXT contract
- System extracts and analyzes clauses
- NLP identifies obligations, rights, and prohibitions

### 2. Risk Assessment
- Multi-level risk scoring (clause and contract level)
- Detection of 10+ risk categories
- Identification of unfavorable terms

### 3. Plain Language Explanations
- AI-powered clause explanations
- Business-friendly summaries
- Legal term glossary

### 4. Template Matching
- Comparison with SME-friendly templates
- Suggested improvements
- Alternative clause recommendations

### 5. Export Options
- PDF report for legal review
- JSON data export
- Plain text summary

## Architecture Overview

```
app.py (Main Streamlit UI)
├── modules/
│   ├── document_parser.py      # PDF/DOCX/TXT parsing
│   ├── nlp_analyzer.py          # spaCy-based NLP analysis
│   ├── risk_assessor.py         # Risk scoring engine
│   ├── llm_processor.py         # Claude/GPT-4 integration
│   ├── template_matcher.py      # Template comparison
│   └── export_manager.py        # PDF/JSON export
├── utils/
│   ├── text_processor.py        # Text preprocessing
│   └── audit_logger.py          # Audit trail management
├── templates/
│   └── contract_templates.json  # SME-friendly templates
└── data/
    └── audit_logs/              # Analysis audit trails
```

## Key Components

### NLP Analysis (spaCy)
- Named Entity Recognition (NER)
- Clause classification
- Obligation/Right/Prohibition detection
- Ambiguity detection

### Risk Assessment
- 10 risk categories with weighted scoring
- Pattern matching for problematic clauses
- Unfavorable term detection
- Compliance checking

### LLM Integration
- Contract type classification
- Plain language summaries
- Clause-by-clause explanations
- Alternative clause suggestions

### Template System
- Standard SME-friendly clauses
- Similarity matching
- Gap analysis
- Best practice recommendations

## Customization

### Adding Custom Risk Categories

Edit `config.py` to add new risk patterns:

```python
RISK_CATEGORIES = {
    "custom_risk": {
        "keywords": ["keyword1", "keyword2"],
        "weight": 0.8
    }
}
```

### Adding Contract Templates

Edit `templates/contract_templates.json` to add new template clauses.

### Multilingual Support

The system detects Hindi contracts and normalizes them. To enhance Hindi support:
- Use appropriate spaCy models
- Customize text_processor.py for Hindi normalization

## Troubleshooting

### spaCy Model Not Found
```bash
python -m spacy download en_core_web_lg
```

### NLTK Data Missing
```bash
python -c "import nltk; nltk.download('all')"
```

### LLM API Errors
- Verify API key in `.env` file
- Check API key permissions
- Ensure sufficient API credits

### PDF Parsing Issues
- Ensure PDF is text-based (not scanned image)
- Try using pdfplumber or PyPDF2 separately
- Convert to DOCX if needed

## Performance Optimization

### For Large Contracts
- Increase max_tokens in llm_processor.py
- Adjust MAX_CLAUSE_LENGTH in config.py
- Use "Quick" analysis mode

### For Better Accuracy
- Use "Comprehensive" analysis mode
- Ensure good quality input documents
- Review and adjust risk category weights

## Security & Privacy

- All processing is done locally
- Documents are not stored permanently
- Audit logs can be disabled in config.py
- API calls to LLM are encrypted in transit

## Limitations

- LLM usage requires active internet connection
- Analysis quality depends on document format
- Not a substitute for legal advice
- Indian context focused (modify for other jurisdictions)

## Support & Contributing

For issues or enhancements:
1. Check documentation
2. Review sample contracts
3. Test with different file formats
4. Adjust configuration settings

## Legal Disclaimer

This tool provides AI-assisted analysis and should NOT be considered legal advice. 
Always consult with a qualified legal professional before making contract decisions.

## License

For educational and commercial use by Indian SMEs.
