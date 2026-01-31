"""
NLP Analyzer Module
Cloud-safe for Streamlit Community Cloud
"""

import re
import logging
from typing import Dict, List

import streamlit as st
import spacy
from spacy.matcher import Matcher

import nltk
from nltk.corpus import stopwords

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Cached Loaders
# --------------------------------------------------
@st.cache_resource
def load_spacy_model():
    return spacy.load("en_core_web_sm")


@st.cache_resource
def load_stopwords():
    try:
        return set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords")
        return set(stopwords.words("english"))


# --------------------------------------------------
# NLP Analyzer
# --------------------------------------------------
class NLPAnalyzer:
    def __init__(self):
        self.nlp = load_spacy_model()
        self.stop_words = load_stopwords()
        self.matcher = Matcher(self.nlp.vocab)
        self._setup_patterns()

    def _setup_patterns(self):
        self.matcher.add("OBLIGATION", [[{"LOWER": "shall"}], [{"LOWER": "must"}]])
        self.matcher.add("RIGHT", [[{"LOWER": "may"}]])
        self.matcher.add("PROHIBITION", [[{"LOWER": "shall"}, {"LOWER": "not"}]])

    # --------------------------------------------------
    # Main Entry
    # --------------------------------------------------
    def analyze_document(self, text: str, clauses: List[Dict]) -> Dict:
        doc = self.nlp(text[:1_000_000])
        return {
            "entities": self.extract_entities(doc),
            "key_terms": self.extract_key_terms(text),
            "obligations": self.identify_obligations(clauses),
            "rights": self.identify_rights(clauses),
            "prohibitions": self.identify_prohibitions(clauses),
            "dates": self.extract_dates(doc),
            "amounts": self.extract_amounts(doc),
            "parties": self.extract_parties(doc),
        }

    # --------------------------------------------------
    # Extractors
    # --------------------------------------------------
    def extract_entities(self, doc):
        return [
            {"text": e.text, "label": e.label_}
            for e in doc.ents
            if e.label_ in config.ENTITY_TYPES
        ]

    def extract_dates(self, doc):
        return [{"date": e.text} for e in doc.ents if e.label_ == "DATE"]

    def extract_amounts(self, doc):
        return [{"amount": e.text} for e in doc.ents if e.label_ in ["MONEY", "PERCENT"]]

    def extract_parties(self, doc):
        parties = []
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PERSON"]:
                parties.append({"name": ent.text, "type": ent.label_})
        return parties[:10]

    # --------------------------------------------------
    # Key Terms (FIXED)
    # --------------------------------------------------
    def extract_key_terms(self, text: str) -> List[Dict]:
        legal_terms = [
            "liability", "indemnity", "termination", "confidentiality",
            "arbitration", "jurisdiction", "payment", "damages", "warranty"
        ]

        text_lower = text.lower()
        results = []

        for term in legal_terms:
            count = text_lower.count(term)
            if count > 0:
                results.append({"term": term, "count": count})

        return sorted(results, key=lambda x: x["count"], reverse=True)

    # --------------------------------------------------
    # Pattern Matching
    # --------------------------------------------------
    def _match(self, clauses, label):
        matches = []
        for c in clauses:
            doc = self.nlp(c["content"])
            if any(self.nlp.vocab.strings[m[0]] == label for m in self.matcher(doc)):
                matches.append(c)
        return matches

    def identify_obligations(self, clauses):
        return self._match(clauses, "OBLIGATION")

    def identify_rights(self, clauses):
        return self._match(clauses, "RIGHT")

    def identify_prohibitions(self, clauses):
        return self._match(clauses, "PROHIBITION")
