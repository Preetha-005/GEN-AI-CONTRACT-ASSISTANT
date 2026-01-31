"""
NLP Analyzer Module
Performs NLP tasks including NER, clause classification, and entity extraction
"""
import re
from typing import Dict, List, Tuple, Optional
import logging

import spacy
from spacy.matcher import Matcher, PhraseMatcher
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NLPAnalyzer:
    """Performs comprehensive NLP analysis on legal contracts"""
    
    def __init__(self):
        """Initialize NLP models and tools"""
        try:
            self.nlp = spacy.load(config.SPACY_MODEL)
        except OSError:
            logger.warning(f"{config.SPACY_MODEL} not found, using smaller model")
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                raise OSError("No spaCy model found. Please run: python -m spacy download en_core_web_lg")
        
        # Initialize matchers
        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        
        # Initialize NLTK
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            nltk.download('stopwords')
            self.stop_words = set(stopwords.words('english'))
        
        # Setup patterns for obligations, rights, and prohibitions
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Setup spaCy patterns for identifying legal constructs"""
        
        # Obligation patterns (SHALL, MUST, WILL, AGREE TO)
        obligation_patterns = [
            [{"LOWER": "shall"}],
            [{"LOWER": "must"}],
            [{"LOWER": "will"}],
            [{"LOWER": "agrees"}, {"LOWER": "to"}],
            [{"LOWER": "obligated"}, {"LOWER": "to"}],
            [{"LOWER": "required"}, {"LOWER": "to"}],
            [{"LOWER": "responsible"}, {"LOWER": "for"}],
        ]
        self.matcher.add("OBLIGATION", obligation_patterns)
        
        # Right patterns (MAY, ENTITLED TO, HAS THE RIGHT)
        right_patterns = [
            [{"LOWER": "may"}],
            [{"LOWER": "entitled"}, {"LOWER": "to"}],
            [{"LOWER": "has"}, {"LOWER": "the"}, {"LOWER": "right"}],
            [{"LOWER": "permitted"}, {"LOWER": "to"}],
            [{"LOWER": "authorized"}, {"LOWER": "to"}],
        ]
        self.matcher.add("RIGHT", right_patterns)
        
        # Prohibition patterns (SHALL NOT, MUST NOT, PROHIBITED)
        prohibition_patterns = [
            [{"LOWER": "shall"}, {"LOWER": "not"}],
            [{"LOWER": "must"}, {"LOWER": "not"}],
            [{"LOWER": "will"}, {"LOWER": "not"}],
            [{"LOWER": "prohibited"}, {"LOWER": "from"}],
            [{"LOWER": "not"}, {"LOWER": "permitted"}],
            [{"LOWER": "may"}, {"LOWER": "not"}],
        ]
        self.matcher.add("PROHIBITION", prohibition_patterns)
    
    def analyze_document(self, text: str, clauses: List[Dict]) -> Dict:
        """
        Perform comprehensive NLP analysis on the contract
        
        Args:
            text: Full contract text
            clauses: List of extracted clauses
            
        Returns:
            Dictionary containing all NLP analysis results
        """
        logger.info("Starting NLP analysis...")
        
        # Process full document
        doc = self.nlp(text[:1000000])  # Limit to 1M chars for memory
        
        results = {
            'entities': self.extract_entities(doc),
            'key_terms': self.extract_key_terms(text),
            'clause_analysis': self.analyze_clauses(clauses),
            'obligations': self.identify_obligations(clauses),
            'rights': self.identify_rights(clauses),
            'prohibitions': self.identify_prohibitions(clauses),
            'ambiguities': self.detect_ambiguities(clauses),
            'dates': self.extract_dates(doc),
            'amounts': self.extract_amounts(doc),
            'parties': self.extract_parties(doc)
        }
        
        logger.info("NLP analysis completed")
        return results
    
    def extract_entities(self, doc) -> List[Dict]:
        """Extract named entities from the document"""
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in config.ENTITY_TYPES:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        
        return entities
    
    def extract_parties(self, doc) -> List[Dict]:
        """Extract party names from the contract"""
        parties = []
        seen = set()
        
        # Look for party indicators
        party_patterns = [
            r'(?i)between\s+([A-Z][A-Za-z\s&.,]+?)\s+(?:and|,)',
            r'(?i)party\s+(?:of\s+the\s+)?(?:first|second|third)\s+part[:\s]+([A-Z][A-Za-z\s&.,]+?)(?:\s+and|\s+,|\s+\()',
            r'(?i)(?:hereinafter\s+)?(?:referred\s+to\s+as|called)\s+["\']([A-Za-z\s&]+)["\']',
        ]
        
        text = doc.text
        for pattern in party_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                party_name = match.group(1).strip()
                if party_name and party_name not in seen and len(party_name) > 3:
                    parties.append({
                        'name': party_name,
                        'type': 'Organization' if any(word in party_name.upper() for word in ['LTD', 'LLC', 'INC', 'PVT', 'PRIVATE', 'LIMITED']) else 'Person'
                    })
                    seen.add(party_name)
        
        # Also extract from entities
        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'ORG'] and ent.text not in seen:
                parties.append({
                    'name': ent.text,
                    'type': ent.label_
                })
                seen.add(ent.text)
        
        return parties[:10]  # Limit to top 10
    
    def extract_dates(self, doc) -> List[Dict]:
        """Extract important dates from the contract"""
        dates = []
        
        for ent in doc.ents:
            if ent.label_ == 'DATE':
                # Get context
                start = max(0, ent.start - 10)
                end = min(len(doc), ent.end + 10)
                context = doc[start:end].text
                
                dates.append({
                    'date': ent.text,
                    'context': context
                })
        
        return dates
    
    def extract_amounts(self, doc) -> List[Dict]:
        """Extract financial amounts from the contract"""
        amounts = []
        
        for ent in doc.ents:
            if ent.label_ in ['MONEY', 'CARDINAL', 'PERCENT']:
                # Get context
                start = max(0, ent.start - 10)
                end = min(len(doc), ent.end + 10)
                context = doc[start:end].text
                
                amounts.append({
                    'amount': ent.text,
                    'type': ent.label_,
                    'context': context
                })
        
        return amounts
    
    def extract_key_terms(self, text: str) -> List[str]:
        """Extract key legal terms and concepts"""
        # Common legal terms
        legal_terms = [
            'indemnify', 'indemnification', 'liability', 'warranty', 'guarantee',
            'termination', 'breach', 'default', 'force majeure', 'arbitration',
            'jurisdiction', 'governing law', 'confidentiality', 'non-disclosure',
            'intellectual property', 'assignment', 'subcontract', 'amendment',
            'renewal', 'penalty', 'damages', 'compensation', 'payment terms'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in legal_terms:
            if term in text_lower:
                # Count occurrences
                count = text_lower.count(term)
                found_terms.append({
                    'term': term,
                    'count': count
                })
        
        # Sort by frequency
        found_terms.sort(key=lambda x: x['count'], reverse=True)
        return found_terms
    
    def analyze_clauses(self, clauses: List[Dict]) -> List[Dict]:
        """Analyze each clause for type and characteristics"""
        analyzed_clauses = []
        
        for clause in clauses:
            content = clause['content']
            doc = self.nlp(content)
            
            # Classify clause type
            clause_type = self._classify_clause_type(content)
            
            # Calculate complexity metrics
            complexity = self._calculate_complexity(content)
            
            # Extract entities from clause
            clause_entities = []
            for ent in doc.ents:
                clause_entities.append({
                    'text': ent.text,
                    'label': ent.label_
                })
            
            analyzed_clauses.append({
                **clause,
                'type': clause_type,
                'complexity': complexity,
                'entities': clause_entities,
                'sentence_count': len(list(doc.sents))
            })
        
        return analyzed_clauses
    
    def _classify_clause_type(self, clause_text: str) -> str:
        """Classify the type of legal clause"""
        text_lower = clause_text.lower()
        
        # Define clause type keywords
        clause_types = {
            'Payment': ['payment', 'fee', 'compensation', 'invoice', 'remuneration'],
            'Termination': ['termination', 'terminate', 'end the agreement', 'cancel'],
            'Liability': ['liability', 'liable', 'indemnify', 'indemnification'],
            'Confidentiality': ['confidential', 'non-disclosure', 'secret', 'proprietary'],
            'Intellectual Property': ['intellectual property', 'ip', 'copyright', 'patent', 'trademark'],
            'Warranty': ['warranty', 'warrants', 'guarantee', 'representation'],
            'Dispute Resolution': ['dispute', 'arbitration', 'mediation', 'litigation'],
            'Governing Law': ['governing law', 'jurisdiction', 'applicable law'],
            'Force Majeure': ['force majeure', 'act of god', 'unforeseeable'],
            'Assignment': ['assignment', 'assign', 'transfer'],
            'Amendment': ['amendment', 'modify', 'change', 'alter'],
            'Non-Compete': ['non-compete', 'non-competition', 'restraint of trade'],
            'Renewal': ['renewal', 'renew', 'extend', 'auto-renew'],
        }
        
        # Score each type
        scores = {}
        for clause_type, keywords in clause_types.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[clause_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        else:
            return 'General'
    
    def _calculate_complexity(self, text: str) -> Dict:
        """Calculate complexity metrics for a clause"""
        doc = self.nlp(text)
        
        sentences = list(doc.sents)
        words = [token for token in doc if not token.is_punct and not token.is_space]
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Lexical diversity
        unique_words = set([token.lemma_.lower() for token in words if token.is_alpha])
        lexical_diversity = len(unique_words) / len(words) if words else 0
        
        # Complexity score (0-1)
        complexity_score = min(1.0, (avg_sentence_length / 30 + (1 - lexical_diversity)) / 2)
        
        # Determine complexity level
        if complexity_score > 0.6:
            level = 'High'
        elif complexity_score > 0.3:
            level = 'Medium'
        else:
            level = 'Low'
        
        return {
            'score': round(complexity_score, 2),
            'avg_sentence_length': round(avg_sentence_length, 1),
            'lexical_diversity': round(lexical_diversity, 2),
            'level': level
        }
    
    def identify_obligations(self, clauses: List[Dict]) -> List[Dict]:
        """Identify obligation clauses (SHALL, MUST, WILL)"""
        obligations = []
        
        for clause in clauses:
            doc = self.nlp(clause['content'])
            matches = self.matcher(doc)
            
            has_obligation = any(self.nlp.vocab.strings[match_id] == "OBLIGATION" for match_id, _, _ in matches)
            
            if has_obligation:
                obligations.append({
                    'clause_id': clause['clause_id'],
                    'clause_number': clause['clause_number'],
                    'content': clause['content'][:200] + '...' if len(clause['content']) > 200 else clause['content'],
                    'type': 'Obligation'
                })
        
        return obligations
    
    def identify_rights(self, clauses: List[Dict]) -> List[Dict]:
        """Identify rights clauses (MAY, ENTITLED TO)"""
        rights = []
        
        for clause in clauses:
            doc = self.nlp(clause['content'])
            matches = self.matcher(doc)
            
            has_right = any(self.nlp.vocab.strings[match_id] == "RIGHT" for match_id, _, _ in matches)
            
            if has_right:
                rights.append({
                    'clause_id': clause['clause_id'],
                    'clause_number': clause['clause_number'],
                    'content': clause['content'][:200] + '...' if len(clause['content']) > 200 else clause['content'],
                    'type': 'Right'
                })
        
        return rights
    
    def identify_prohibitions(self, clauses: List[Dict]) -> List[Dict]:
        """Identify prohibition clauses (SHALL NOT, MUST NOT)"""
        prohibitions = []
        
        for clause in clauses:
            doc = self.nlp(clause['content'])
            matches = self.matcher(doc)
            
            has_prohibition = any(self.nlp.vocab.strings[match_id] == "PROHIBITION" for match_id, _, _ in matches)
            
            if has_prohibition:
                prohibitions.append({
                    'clause_id': clause['clause_id'],
                    'clause_number': clause['clause_number'],
                    'content': clause['content'][:200] + '...' if len(clause['content']) > 200 else clause['content'],
                    'type': 'Prohibition'
                })
        
        return prohibitions
    
    def detect_ambiguities(self, clauses: List[Dict]) -> List[Dict]:
        """Detect ambiguous or vague language in clauses"""
        ambiguities = []
        
        # Ambiguous terms
        ambiguous_terms = [
            'reasonable', 'appropriate', 'substantial', 'material', 'significant',
            'promptly', 'timely', 'as soon as possible', 'best efforts',
            'adequate', 'sufficient', 'necessary', 'proper', 'satisfactory'
        ]
        
        for clause in clauses:
            content_lower = clause['content'].lower()
            found_terms = []
            
            for term in ambiguous_terms:
                if term in content_lower:
                    found_terms.append(term)
            
            if found_terms:
                ambiguities.append({
                    'clause_id': clause['clause_id'],
                    'clause_number': clause['clause_number'],
                    'ambiguous_terms': found_terms,
                    'content': clause['content'][:200] + '...' if len(clause['content']) > 200 else clause['content'],
                    'severity': 'High' if len(found_terms) > 2 else 'Medium'
                })
        
        return ambiguities


if __name__ == "__main__":
    # Test the analyzer
    analyzer = NLPAnalyzer()
    print("NLP Analyzer initialized successfully")
