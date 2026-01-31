@echo off
REM Quick Setup Script for GenAI Legal Contract Assistant (Windows)

echo ========================================
echo GenAI Legal Contract Assistant Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

echo Python found!
python --version
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    pause
    exit /b 1
)

echo ========================================
echo Step 1: Installing Python packages...
echo ========================================
echo.

pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install packages
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 2: Downloading spaCy model...
echo ========================================
echo.

python -m spacy download en_core_web_lg
if errorlevel 1 (
    echo WARNING: Large model failed, trying smaller model...
    python -m spacy download en_core_web_sm
)

echo.
echo ========================================
echo Step 3: Downloading NLTK data...
echo ========================================
echo.

python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"

echo.
echo ========================================
echo Step 4: Setting up configuration...
echo ========================================
echo.

if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env file and add your API keys!
    echo - For Anthropic Claude: Get key from https://console.anthropic.com/
    echo - For OpenAI GPT-4: Get key from https://platform.openai.com/
    echo.
) else (
    echo .env file already exists
)

echo.
echo ========================================
echo Step 5: Running system tests...
echo ========================================
echo.

python test_system.py
if errorlevel 1 (
    echo.
    echo WARNING: Some tests failed. Check the output above.
    echo You may still be able to run the application.
    echo.
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application, run:
echo     streamlit run app.py
echo.
echo For more information, see:
echo     - README.md
echo     - SETUP_GUIDE.md
echo     - TECHNICAL_DOCS.md
echo.
echo Don't forget to configure your API keys in .env file!
echo.

pause
