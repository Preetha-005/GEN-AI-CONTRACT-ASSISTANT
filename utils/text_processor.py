"""
Text Processor Utilities
Preprocessing and text manipulation functions
"""
import re
import string
from typing import List, Dict
import unicodedata


class TextProcessor:
    """Utility class for text processing operations"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters (keep basic punctuation)
        text = re.sub(r'[^\w\s.,;:!?()\-\'"₹$%]', '', text)
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        return text.strip()
    
    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """
        Extract sentences from text
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Simple sentence splitter
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """
        Extract numbers from text
        
        Args:
            text: Input text
            
        Returns:
            List of numbers found
        """
        # Match integers, decimals, and formatted numbers
        numbers = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', text)
        return numbers
    
    @staticmethod
    def extract_amounts(text: str) -> List[Dict]:
        """
        Extract monetary amounts from text
        
        Args:
            text: Input text
            
        Returns:
            List of amount dictionaries
        """
        amounts = []
        
        # Patterns for Indian and international currencies
        patterns = [
            (r'₹\s*(\d+(?:,\d{3})*(?:\.\d+)?)', 'INR'),
            (r'Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d+)?)', 'INR'),
            (r'INR\s*(\d+(?:,\d{3})*(?:\.\d+)?)', 'INR'),
            (r'\$\s*(\d+(?:,\d{3})*(?:\.\d+)?)', 'USD'),
            (r'USD\s*(\d+(?:,\d{3})*(?:\.\d+)?)', 'USD'),
        ]
        
        for pattern, currency in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amounts.append({
                    'amount': match.group(1),
                    'currency': currency,
                    'full_text': match.group(0)
                })
        
        return amounts
    
    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """
        Extract date patterns from text
        
        Args:
            text: Input text
            
        Returns:
            List of date strings
        """
        dates = []
        
        # Common date patterns
        patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # DD-MM-YYYY or MM/DD/YYYY
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',    # YYYY-MM-DD
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',  # DD Month YYYY
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return dates
    
    @staticmethod
    def extract_emails(text: str) -> List[str]:
        """
        Extract email addresses from text
        
        Args:
            text: Input text
            
        Returns:
            List of email addresses
        """
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(pattern, text)
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """
        Extract phone numbers (Indian format)
        
        Args:
            text: Input text
            
        Returns:
            List of phone numbers
        """
        patterns = [
            r'\+91[-\s]?\d{10}',  # +91 format
            r'\d{10}',  # 10 digit number
            r'\d{5}[-\s]?\d{5}',  # With separator
            r'\(\d{3}\)[-\s]?\d{7}',  # With area code
        ]
        
        phone_numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            phone_numbers.extend(matches)
        
        return phone_numbers
    
    @staticmethod
    def normalize_hindi_text(text: str) -> str:
        """
        Normalize Hindi text for processing
        
        Args:
            text: Hindi text
            
        Returns:
            Normalized text
        """
        # Remove zero-width characters
        text = re.sub(r'[\u200b\u200c\u200d]', '', text)
        
        # Normalize unicode
        text = unicodedata.normalize('NFC', text)
        
        return text
    
    @staticmethod
    def highlight_text(text: str, keywords: List[str], max_length: int = 200) -> str:
        """
        Highlight keywords in text with context
        
        Args:
            text: Full text
            keywords: Keywords to highlight
            max_length: Maximum context length
            
        Returns:
            Highlighted text snippet
        """
        for keyword in keywords:
            # Find keyword position
            pattern = re.compile(re.escape(keyword), re.IGNORECASE)
            match = pattern.search(text)
            
            if match:
                start = max(0, match.start() - max_length // 2)
                end = min(len(text), match.end() + max_length // 2)
                
                snippet = text[start:end]
                
                # Add ellipsis if truncated
                if start > 0:
                    snippet = '...' + snippet
                if end < len(text):
                    snippet = snippet + '...'
                
                return snippet
        
        # If no keywords found, return beginning
        return text[:max_length] + ('...' if len(text) > max_length else '')
    
    @staticmethod
    def calculate_readability_score(text: str) -> Dict:
        """
        Calculate basic readability metrics
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with readability metrics
        """
        sentences = TextProcessor.extract_sentences(text)
        words = text.split()
        
        # Calculate metrics
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Simple readability score (0-100, higher is easier)
        readability = max(0, 100 - (avg_sentence_length * 2) - (avg_word_length * 5))
        
        # Determine readability level
        if readability > 70:
            level = 'Easy'
        elif readability > 40:
            level = 'Medium'
        else:
            level = 'Difficult'
        
        return {
            'score': round(readability, 1),
            'avg_sentence_length': round(avg_sentence_length, 1),
            'avg_word_length': round(avg_word_length, 1),
            'level': level
        }
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
        """
        Truncate text to maximum length
        
        Args:
            text: Input text
            max_length: Maximum length
            suffix: Suffix to add when truncated
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)].strip() + suffix


if __name__ == "__main__":
    # Test text processor
    processor = TextProcessor()
    test_text = "Payment of ₹50,000 must be made by 31st December 2024."
    
    print("Amounts found:", processor.extract_amounts(test_text))
    print("Dates found:", processor.extract_dates(test_text))
