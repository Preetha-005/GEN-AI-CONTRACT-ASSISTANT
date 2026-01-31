#!/bin/bash
# Quick Setup Script for GenAI Legal Contract Assistant (Linux/Mac)

echo "========================================"
echo "GenAI Legal Contract Assistant Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/"
    exit 1
fi

echo "Python found!"
python3 --version
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "ERROR: pip is not available"
    exit 1
fi

echo "========================================"
echo "Step 1: Installing Python packages..."
echo "========================================"
echo ""

pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install packages"
    exit 1
fi

echo ""
echo "========================================"
echo "Step 2: Downloading spaCy model..."
echo "========================================"
echo ""

python3 -m spacy download en_core_web_lg
if [ $? -ne 0 ]; then
    echo "WARNING: Large model failed, trying smaller model..."
    python3 -m spacy download en_core_web_sm
fi

echo ""
echo "========================================"
echo "Step 3: Downloading NLTK data..."
echo "========================================"
echo ""

python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"

echo ""
echo "========================================"
echo "Step 4: Setting up configuration..."
echo "========================================"
echo ""

if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env file and add your API keys!"
    echo "- For Anthropic Claude: Get key from https://console.anthropic.com/"
    echo "- For OpenAI GPT-4: Get key from https://platform.openai.com/"
    echo ""
else
    echo ".env file already exists"
fi

echo ""
echo "========================================"
echo "Step 5: Running system tests..."
echo "========================================"
echo ""

python3 test_system.py
if [ $? -ne 0 ]; then
    echo ""
    echo "WARNING: Some tests failed. Check the output above."
    echo "You may still be able to run the application."
    echo ""
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To start the application, run:"
echo "    streamlit run app.py"
echo ""
echo "For more information, see:"
echo "    - README.md"
echo "    - SETUP_GUIDE.md"
echo "    - TECHNICAL_DOCS.md"
echo ""
echo "Don't forget to configure your API keys in .env file!"
echo ""
