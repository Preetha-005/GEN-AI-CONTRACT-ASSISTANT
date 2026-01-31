"""
Template Matcher Module
Matches contract clauses against standard templates and suggests improvements
"""
import json
from typing import Dict, List, Tuple
from pathlib import Path
import logging
from difflib import SequenceMatcher

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TemplateMatcher:
    """Matches clauses against standard contract templates"""
    
    def __init__(self):
        """Initialize with standard templates"""
        self.templates_file = config.TEMPLATES_DIR / "contract_templates.json"
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load standard contract templates"""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load templates: {e}")
                return self._get_default_templates()
        else:
            # Create default templates
            templates = self._get_default_templates()
            self._save_templates(templates)
            return templates
    
    def _save_templates(self, templates: Dict):
        """Save templates to file"""
        config.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2)
    
    def _get_default_templates(self) -> Dict:
        """Get default SME-friendly template clauses"""
        return {
            "payment_terms": {
                "title": "Balanced Payment Terms",
                "template": "Payment shall be made within [30/60] days of receipt of invoice. Late payments shall accrue interest at [X]% per month. The Client reserves the right to withhold payment for defective deliverables until rectified.",
                "key_points": [
                    "Clear payment timeline",
                    "Reasonable interest on late payment",
                    "Right to withhold for non-performance"
                ]
            },
            "termination": {
                "title": "Mutual Termination Rights",
                "template": "Either party may terminate this Agreement by providing [30/60/90] days' written notice to the other party. In case of material breach, the non-breaching party may terminate immediately upon written notice, with opportunity to cure within [15] days.",
                "key_points": [
                    "Equal termination rights for both parties",
                    "Reasonable notice period",
                    "Opportunity to cure breaches"
                ]
            },
            "liability": {
                "title": "Limited Liability Clause",
                "template": "Total liability of either party shall not exceed the total amount paid under this Agreement in the [12] months preceding the claim, or [specified amount], whichever is lower. Neither party shall be liable for indirect, incidental, or consequential damages.",
                "key_points": [
                    "Capped liability amount",
                    "Mutual limitation",
                    "Exclusion of consequential damages"
                ]
            },
            "indemnification": {
                "title": "Mutual Indemnification",
                "template": "Each party shall indemnify the other against third-party claims arising from: (i) breach of this Agreement, (ii) negligence or willful misconduct, (iii) violation of applicable laws. Indemnification shall be limited to direct damages and shall not exceed the liability cap defined herein.",
                "key_points": [
                    "Mutual indemnification",
                    "Specific triggering events",
                    "Limited to direct damages"
                ]
            },
            "confidentiality": {
                "title": "Standard Confidentiality Clause",
                "template": "Each party agrees to maintain confidentiality of the other party's Confidential Information for a period of [2/3/5] years. Confidential Information shall not include information that: (i) is publicly available, (ii) was independently developed, (iii) is required to be disclosed by law.",
                "key_points": [
                    "Defined confidentiality period",
                    "Clear exclusions",
                    "Mutual obligations"
                ]
            },
            "ip_rights": {
                "title": "IP Rights Retention",
                "template": "Each party retains ownership of its pre-existing intellectual property. New IP created during this Agreement shall be owned by [specify party], with the other party receiving a non-exclusive license for [defined purposes].",
                "key_points": [
                    "Pre-existing IP remains with creator",
                    "Clear ownership of new IP",
                    "License rights defined"
                ]
            },
            "dispute_resolution": {
                "title": "Tiered Dispute Resolution",
                "template": "Disputes shall first be resolved through good faith negotiation for [30] days. If unresolved, parties shall attempt mediation. If mediation fails, disputes shall be resolved through arbitration under [Indian Arbitration Act] in [City], India.",
                "key_points": [
                    "Negotiation first approach",
                    "Mediation option",
                    "Arbitration in India"
                ]
            },
            "force_majeure": {
                "title": "Reasonable Force Majeure",
                "template": "Neither party shall be liable for failure to perform due to circumstances beyond reasonable control (Force Majeure), including natural disasters, war, government actions, or pandemic. The affected party must notify the other within [7] days and make reasonable efforts to mitigate impact.",
                "key_points": [
                    "Clear definition of Force Majeure",
                    "Notice requirement",
                    "Mitigation obligation"
                ]
            },
            "warranty": {
                "title": "Basic Warranties",
                "template": "The Service Provider warrants that services will be performed in a professional and workmanlike manner, consistent with industry standards. Services shall substantially conform to specifications for [90] days from delivery. Client's exclusive remedy is re-performance of deficient services.",
                "key_points": [
                    "Professional standard commitment",
                    "Conformance to specifications",
                    "Limited warranty period"
                ]
            },
            "amendment": {
                "title": "Mutual Amendment Rights",
                "template": "This Agreement may only be amended by written agreement signed by authorized representatives of both parties. No oral modifications shall be binding.",
                "key_points": [
                    "Written amendments only",
                    "Mutual consent required",
                    "No oral modifications"
                ]
            }
        }
    
    def match_clauses_to_templates(self, clauses: List[Dict]) -> List[Dict]:
        """
        Match contract clauses to standard templates
        
        Args:
            clauses: List of analyzed clauses
            
        Returns:
            List of matches with similarity scores
        """
        matches = []
        
        for clause in clauses:
            clause_type = clause.get('type', 'General').lower()
            
            # Find best matching template
            best_match = None
            best_score = 0
            
            for template_key, template_data in self.templates.items():
                # Calculate similarity
                similarity = self._calculate_similarity(
                    clause['content'].lower(),
                    template_data['template'].lower()
                )
                
                # Check if clause type matches template key
                type_match = template_key in clause_type or clause_type in template_key
                
                if type_match:
                    similarity += 0.2  # Boost for type match
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = {
                        'template_key': template_key,
                        'template_data': template_data
                    }
            
            if best_match and best_score > 0.3:  # Minimum threshold
                matches.append({
                    'clause_id': clause['clause_id'],
                    'clause_number': clause['clause_number'],
                    'clause_type': clause.get('type'),
                    'template_key': best_match['template_key'],
                    'template_title': best_match['template_data']['title'],
                    'similarity_score': round(best_score, 2),
                    'template_text': best_match['template_data']['template'],
                    'key_points': best_match['template_data']['key_points']
                })
        
        return matches
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def suggest_template_improvements(self, clause: Dict, template_match: Dict) -> Dict:
        """
        Suggest improvements based on template comparison
        
        Args:
            clause: Original clause dictionary
            template_match: Matched template information
            
        Returns:
            Dictionary with improvement suggestions
        """
        suggestions = []
        
        template_text = template_match['template_text'].lower()
        clause_text = clause['content'].lower()
        
        # Check for key elements in template that are missing in clause
        key_elements = [
            ('timeline', ['days', 'within', 'period', 'term']),
            ('cap', ['limit', 'maximum', 'not exceed', 'cap']),
            ('notice', ['notice', 'notify', 'notification']),
            ('mutual', ['both parties', 'either party', 'mutual']),
            ('specific amounts', ['₹', 'rs.', 'inr', 'dollars', '%']),
        ]
        
        for element_name, keywords in key_elements:
            in_template = any(kw in template_text for kw in keywords)
            in_clause = any(kw in clause_text for kw in keywords)
            
            if in_template and not in_clause:
                suggestions.append(f"Consider adding {element_name} specification")
        
        return {
            'clause_id': clause['clause_id'],
            'template_title': template_match['template_title'],
            'suggestions': suggestions,
            'template_reference': template_match['template_text']
        }
    
    def generate_sme_friendly_templates(self, contract_type: str) -> Dict:
        """
        Generate a complete SME-friendly contract template
        
        Args:
            contract_type: Type of contract to generate
            
        Returns:
            Dictionary with template sections
        """
        # Map contract types to relevant template clauses
        contract_templates = {
            "Employment Agreement": [
                'payment_terms', 'termination', 'confidentiality', 
                'ip_rights', 'dispute_resolution'
            ],
            "Vendor Contract": [
                'payment_terms', 'liability', 'warranty', 'termination',
                'indemnification', 'dispute_resolution'
            ],
            "Service Contract": [
                'payment_terms', 'liability', 'warranty', 'termination',
                'ip_rights', 'dispute_resolution'
            ],
            "Lease Agreement": [
                'payment_terms', 'termination', 'liability', 
                'dispute_resolution', 'force_majeure'
            ],
            "NDA": [
                'confidentiality', 'termination', 'dispute_resolution'
            ]
        }
        
        relevant_clauses = contract_templates.get(
            contract_type,
            ['payment_terms', 'termination', 'liability', 'dispute_resolution']
        )
        
        template = {
            'contract_type': contract_type,
            'title': f"SME-Friendly {contract_type} Template",
            'sections': []
        }
        
        for clause_key in relevant_clauses:
            if clause_key in self.templates:
                template['sections'].append({
                    'section_name': self.templates[clause_key]['title'],
                    'template_text': self.templates[clause_key]['template'],
                    'key_points': self.templates[clause_key]['key_points']
                })
        
        return template


if __name__ == "__main__":
    # Test the template matcher
    matcher = TemplateMatcher()
    print("Template Matcher initialized successfully")
    print(f"Loaded {len(matcher.templates)} template categories")
