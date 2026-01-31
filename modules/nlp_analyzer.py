"""
NLP Analyzer Module
Performs NLP tasks including NER, clause classification, and entity extraction
Cloud-safe for Streamlit Community Cloud
"""

import re
import logging
from typing import Dict, List

import streamlit as st
import spacy
from spacy.matcher import Matcher, PhraseMatcher

import nltk
from nltk.corpus import stopwords

import config

# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Cached loaders (VERY IMPORTANT FOR STREAMLIT CLOUD)
# --------------------------------------------------

@st.cache_resource
def load_spacy_model():
    """
    Load spaCy model once and cache it.
    Must match the model installed via requirements.txt
    """
    return spacy.load("en_core_web_sm")


@st.cache_resource
def load_stopwords():
    """
    Ensure NLTK stopwords are available.
    Download once if missing.
    """
    try:
        return set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords")
        return set(stopwords.words("english"))


# --------------------------------------------------
# NLP Analyzer Class
# --------------------------------------------------

class NLPAnalyzer:
    """Performs comprehensive NLP analysis on legal contracts"""

    def __init__(self):
        logger.info("Initializing NLP Analyzer...")

        # ✅ Always load known, installed spaCy model
        self.nlp = load_spacy_model()

        # Matchers
        self.matcher = Matcher(self.nlp.vocab)
        self.phrase_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        # Stopwords
        self.stop_words = load_stopwords()

        # Setup patterns
        self._setup_patterns()

    # --------------------------------------------------
    # Pattern Setup
    # --------------------------------------------------

    def _setup_patterns(self):
        """Setup spaCy patterns for identifying legal constructs"""

        # Obligations
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

        # Rights
        right_patterns = [
            [{"LOWER": "may"}],
            [{"LOWER": "entitled"}, {"LOWER": "to"}],
            [{"LOWER": "has"}, {"LOWER": "the"}, {"LOWER": "right"}],
            [{"LOWER": "permitted"}, {"LOWER": "to"}],
            [{"LOWER": "authorized"}, {"LOWER": "to"}],
        ]
        self.matcher.add("RIGHT", right_patterns)

        # Prohibitions
        prohibition_patterns = [
            [{"LOWER": "shall"}, {"LOWER": "not"}],
            [{"LOWER": "must"}, {"LOWER": "not"}],
            [{"LOWER": "will"}, {"LOWER": "not"}],
            [{"LOWER": "prohibited"}, {"LOWER": "from"}],
            [{"LOWER": "not"}, {"LOWER": "permitted"}],
            [{"LOWER": "may"}, {"LOWER": "not"}],
        ]
        self.matcher.add("PROHIBITION", prohibition_patterns)

    # --------------------------------------------------
    # Main Analysis
    # --------------------------------------------------

    def analyze_document(self, text: str, clauses: List[Dict]) -> Dict:
        """Perform comprehensive NLP analysis on the contract"""

        logger.info("Starting NLP analysis...")

        doc = self.nlp(text[:1_000_000])  # Safety limit

        results = {
            "entities": self.extract_entities(doc),
            "key_terms": self.extract_key_terms(text),
            "clause_analysis": self.analyze_clauses(clauses),
            "obligations": self.identify_obligations(clauses),
            "rights": self.identify_rights(clauses),
            "prohibitions": self.identify_prohibitions(clauses),
            "ambiguities": self.detect_ambiguities(clauses),
            "dates": self.extract_dates(doc),
            "amounts": self.extract_amounts(doc),
            "parties": self.extract_parties(doc),
        }

        logger.info("NLP analysis completed")
        return results

    # --------------------------------------------------
    # Entity Extraction
    # --------------------------------------------------

    def extract_entities(self, doc) -> List[Dict]:
        entities = []
        for ent in doc.ents:
            if ent.label_ in config.ENTITY_TYPES:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                })
        return entities

    def extract_parties(self, doc) -> List[Dict]:
        parties = []
        seen = set()

        patterns = [
            r"(?i)between\s+([A-Z][A-Za-z\s&.,]+?)\s+(?:and|,)",
            r"(?i)party\s+(?:of\s+the\s+)?(?:first|second|third)\s+part[:\s]+([A-Z][A-Za-z\s&.,]+?)",
            r"(?i)(?:referred\s+to\s+as|called)\s+[\"']([A-Za-z\s&]+)[\"']",
        ]

        text = doc.text
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1).strip()
                if name and name not in seen:
                    parties.append({
                        "name": name,
                        "type": "Organization" if any(
                            k in name.upper()
                            for k in ["LTD", "LLC", "INC", "PVT", "PRIVATE", "LIMITED"]
                        ) else "Person"
                    })
                    seen.add(name)

        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG"] and ent.text not in seen:
                parties.append({
                    "name": ent.text,
                    "type": ent.label_,
                })
                seen.add(ent.text)

        return parties[:10]

    def extract_dates(self, doc) -> List[Dict]:
        return [{"date": ent.text} for ent in doc.ents if ent.label_ == "DATE"]

    def extract_amounts(self, doc) -> List[Dict]:
        return [{
            "amount": ent.text,
            "type": ent.label_
        } for ent in doc.ents if ent.label_ in ["MONEY", "PERCENT", "CARDINAL"]]

    # --------------------------------------------------
    # Clause Analysis
    # --------------------------------------------------

    def analyze_clauses(self, clauses: List[Dict]) -> List[Dict]:
        analyzed = []

        for clause in clauses:
            content = clause["content"]
            doc = self.nlp(content)

            analyzed.append({
                **clause,
                "type": self._classify_clause_type(content),
                "complexity": self._calculate_complexity(content),
                "sentence_count": len(list(doc.sents)),
            })

        return analyzed

    def _classify_clause_type(self, text: str) -> str:
        text = text.lower()
        keywords = {
            "Payment": ["payment", "fee", "compensation"],
            "Termination": ["termination", "terminate"],
            "Liability": ["liability", "indemnify"],
            "Confidentiality": ["confidential", "non-disclosure"],
            "IP": ["intellectual property", "copyright", "patent"],
            "Dispute": ["arbitration", "litigation"],
        }

        scores = {k: sum(t in text for t in v) for k, v in keywords.items()}
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "General"

    def _calculate_complexity(self, text: str) -> Dict:
        doc = self.nlp(text)
        words = [t for t in doc if t.is_alpha]
        sentences = list(doc.sents)

        avg_len = len(words) / len(sentences) if sentences else 0
        unique = len(set(t.lemma_.lower() for t in words))

        score = min(1.0, (avg_len / 30 + (1 - unique / max(len(words), 1))) / 2)

        level = "High" if score > 0.6 else "Medium" if score > 0.3 else "Low"

        return {
            "score": round(score, 2),
            "avg_sentence_length": round(avg_len, 1),
            "lexical_diversity": round(unique / max(len(words), 1), 2),
            "level": level,
        }

    # --------------------------------------------------
    # Legal Pattern Detection
    # --------------------------------------------------

    def identify_obligations(self, clauses: List[Dict]) -> List[Dict]:
        return self._match_clauses(clauses, "OBLIGATION", "Obligation")

    def identify_rights(self, clauses: List[Dict]) -> List[Dict]:
        return self._match_clauses(clauses, "RIGHT", "Right")

    def identify_prohibitions(self, clauses: List[Dict]) -> List[Dict]:
        return self._match_clauses(clauses, "PROHIBITION", "Prohibition")

    def _match_clauses(self, clauses, label, type_name):
        results = []
        for c in clauses:
            doc = self.nlp(c["content"])
            matches = self.matcher(doc)
            if any(self.nlp.vocab.strings[m[0]] == label for m in matches):
                results.append({
                    "clause_id": c["clause_id"],
                    "clause_number": c["clause_number"],
                    "type": type_name,
                    "content": c["content"][:200],
                })
        return results

    # --------------------------------------------------
    # Ambiguity Detection
    # --------------------------------------------------

    def detect_ambiguities(self, clauses: List[Dict]) -> List[Dict]:
        ambiguous_terms = [
            "reasonable", "appropriate", "substantial", "material",
            "promptly", "best efforts", "adequate", "sufficient"
        ]

        results = []
        for c in clauses:
            found = [t for t in ambiguous_terms if t in c["content"].lower()]
            if found:
                results.append({
                    "clause_id": c["clause_id"],
                    "clause_number": c["clause_number"],
                    "ambiguous_terms": found,
                    "severity": "High" if len(found) > 2 else "Medium",
                })
        return results
