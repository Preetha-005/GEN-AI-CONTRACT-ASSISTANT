"""
Risk Assessor Module
Evaluates legal and business risks in contracts
"""
import re
from typing import Dict, List, Tuple
import logging
from collections import defaultdict

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskAssessor:
    """Assesses risks in legal contracts at clause and document level"""
    
    def __init__(self, language: str = "English"):
        """Initialize risk assessment parameters"""
        self.risk_categories = config.RISK_CATEGORIES
        self.risk_thresholds = config.RISK_THRESHOLDS
        self.language = language or "English"
        self._setup_hindi_strings()
        
    def _setup_hindi_strings(self):
        """Setup Hindi translations for common strings"""
        self.hindi_translations = {
            'Psychological Manipulation': {
                'title': '🚨 अत्यंत महत्वपूर्ण: मनोवैज्ञानिक हेरफेर पाया गया',
                'explanation': '🚨 अत्यंत महत्वपूर्ण: यह खंड आपकी मानसिक और भावनात्मक स्थिति में हेरफेर करने के लिए शिकारी मनोवैज्ञानिक रणनीति का उपयोग करता है। किसी भी कानूनी अनुबंध में आपके विचारों या भावनाओं का उल्लेख नहीं होना चाहिए।',
                'recommendation': 'इस दस्तावेज़ पर हस्ताक्षर न करें। यह एक वैध अनुबंध नहीं है। उचित अधिकारियों को रिपोर्ट करें। कानूनी सलाह लें।'
            },
            'Emotional Manipulation': {
                'title': '⚠️ चेतावनी: भावनात्मक हेरफेर पाया गया',
                'explanation': '⚠️ चेतावनी: यह खंड भावनात्मक रूप से आवेशित भाषा का उपयोग करता है। अनुबंधों में आत्म-मूल्य और भावनात्मक स्थितियों का उल्लेख अनुचित है।',
                'recommendation': 'भावनात्मक हेरफेर वाली भाषा को हटाने का अनुरोध करें। अनुबंधों में निष्पक्ष भाषा का उपयोग होना चाहिए।'
            },
            'Unlimited Liability': {
                'title': 'असीमित दायित्व',
                'explanation': 'यह आपको बिना किसी सीमा या सुरक्षा के असीमित वित्तीय जोखिम में डालता है।',
                'recommendation': 'अनुबंध मूल्य के बराबर या एक विशिष्ट राशि की देयता सीमा (liability cap) पर बातचीत करें।'
            },
            'Waiver of Rights': {
                'title': 'अधिकारों का त्याग',
                'explanation': 'आप महत्वपूर्ण कानूनी अधिकारों या सुरक्षा को छोड़ सकते हैं।',
                'recommendation': 'अधिकारों के त्याग वाले खंड को हटा दें या इसे सीमित करें।'
            },
            'Unilateral Amendment': {
                'title': 'एकतरफा संशोधन',
                'explanation': 'दूसरी पार्टी आपकी सहमति के बिना शर्तों को बदल सकती है।',
                'recommendation': 'किसी भी संशोधन के लिए आपसी सहमति की आवश्यकता की शर्त जोड़ें।'
            },
            'Ambiguous Payment Terms': {
                'title': 'अस्पष्ट भुगतान शर्तें',
                'description': 'भुगतान की शर्तों में विशिष्ट राशि या समय सीमा की कमी हो सकती है।',
                'recommendation': 'विशिष्ट भुगतान राशि, समय सारिणी और तरीकों को स्पष्ट करें।'
            }
        }
    
    def assess_contract_risk(self, clauses: List[Dict], nlp_analysis: Dict) -> Dict:
        """
        Perform comprehensive risk assessment on the contract
        
        Args:
            clauses: List of analyzed clauses
            nlp_analysis: NLP analysis results
            
        Returns:
            Dictionary containing risk assessment results
        """
        logger.info("Starting risk assessment...")
        
        # Assess each clause for risks
        clause_risks = self.assess_clause_risks(clauses)
        
        # Calculate overall contract risk score
        overall_risk = self.calculate_overall_risk(clause_risks)
        
        # Identify high-risk clauses
        high_risk_clauses = [c for c in clause_risks if c['risk_level'] == 'high']
        
        # Categorize risks
        risk_summary = self.categorize_risks(clause_risks)
        
        # Generate risk flags
        risk_flags = self.generate_risk_flags(clauses, nlp_analysis)
        
        # Unfavorable terms detection
        unfavorable_terms = self.detect_unfavorable_terms(clauses)
        
        results = {
            'overall_risk_score': overall_risk['score'],
            'overall_risk_level': overall_risk['level'],
            'risk_distribution': overall_risk['distribution'],
            'clause_risks': clause_risks,
            'high_risk_clauses': high_risk_clauses,
            'risk_summary': risk_summary,
            'risk_flags': risk_flags,
            'unfavorable_terms': unfavorable_terms,
            'recommendations': self.generate_recommendations(clause_risks, risk_flags)
        }
        
        logger.info("Risk assessment completed")
        return results
    
    def assess_clause_risks(self, clauses: List[Dict]) -> List[Dict]:
        """Assess risk level for each clause"""
        clause_risks = []
        
        for clause in clauses:
            content = clause['content']
            content_lower = content.lower()
            
            # Initialize risk scores for each category
            category_scores = {}
            detected_risks = []
            
            # Check each risk category
            for category, config_data in self.risk_categories.items():
                keywords = config_data['keywords']
                weight = config_data['weight']
                
                # Count keyword matches
                matches = sum(1 for keyword in keywords if keyword in content_lower)
                
                if matches > 0:
                    # Calculate category score based on ABSOLUTE match count, not percentage
                    # This ensures categories with many keywords still trigger properly
                    if matches >= 5:
                        # 5+ matches = HIGH risk for this category
                        score = min(1.0, 0.7 + (matches * 0.05)) * weight
                    elif matches >= 3:
                        # 3-4 matches = MEDIUM risk
                        score = min(1.0, 0.4 + (matches * 0.05)) * weight
                    else:
                        # 1-2 matches = detected but lower score
                        score = min(1.0, 0.15 + (matches * 0.05)) * weight
                    
                    category_scores[category] = score
                    detected_risks.append({
                        'category': category,
                        'score': round(score, 2),
                        'matched_keywords': [kw for kw in keywords if kw in content_lower]
                    })
            
            # Calculate overall clause risk score
            if category_scores:
                clause_risk_score = max(category_scores.values())
            else:
                clause_risk_score = 0.0
            
            # Determine risk level
            risk_level = self._get_risk_level(clause_risk_score)
            
            clause_risks.append({
                'clause_id': clause['clause_id'],
                'clause_number': clause['clause_number'],
                'content': content,
                'risk_score': round(clause_risk_score, 2),
                'risk_level': risk_level,
                'detected_risks': detected_risks,
                'risk_categories': list(category_scores.keys())
            })
        
        return clause_risks
    
    def _get_risk_level(self, score: float) -> str:
        """Determine risk level based on score"""
        for level, (min_score, max_score) in self.risk_thresholds.items():
            if min_score <= score < max_score:
                return level
        return 'low'
    
    def calculate_overall_risk(self, clause_risks: List[Dict]) -> Dict:
        """Calculate overall contract risk score"""
        if not clause_risks:
            return {
                'score': 0.0,
                'level': 'low',
                'distribution': {'low': 0, 'medium': 0, 'high': 0}
            }
        
        # Weighted average of clause risks
        risk_scores = [c['risk_score'] for c in clause_risks]
        overall_score = sum(risk_scores) / len(risk_scores)
        
        # Count distribution
        distribution = {
            'low': sum(1 for c in clause_risks if c['risk_level'] == 'low'),
            'medium': sum(1 for c in clause_risks if c['risk_level'] == 'medium'),
            'high': sum(1 for c in clause_risks if c['risk_level'] == 'high')
        }
        
        # Boost score if there are many high-risk clauses
        high_risk_ratio = distribution['high'] / len(clause_risks)
        if high_risk_ratio > 0.3:  # More than 30% high risk
            overall_score = min(1.0, overall_score * 1.2)
        
        overall_level = self._get_risk_level(overall_score)
        
        return {
            'score': round(overall_score, 2),
            'level': overall_level,
            'distribution': distribution
        }
    
    def categorize_risks(self, clause_risks: List[Dict]) -> Dict:
        """Summarize risks by category"""
        category_summary = defaultdict(list)
        
        for clause in clause_risks:
            for risk in clause['detected_risks']:
                category_summary[risk['category']].append({
                    'clause_id': clause['clause_id'],
                    'clause_number': clause['clause_number'],
                    'score': risk['score'],
                    'keywords': risk['matched_keywords']
                })
        
        # Calculate category-level statistics
        category_stats = {}
        for category, risks in category_summary.items():
            avg_score = sum(r['score'] for r in risks) / len(risks)
            category_stats[category] = {
                'count': len(risks),
                'avg_score': round(avg_score, 2),
                'severity': self._get_risk_level(avg_score),
                'clauses': risks
            }
        
        return dict(category_stats)
    
    def generate_risk_flags(self, clauses: List[Dict], nlp_analysis: Dict) -> List[Dict]:
        """Generate specific risk flags and warnings"""
        flags = []
        
        # Check for manipulative psychological language (CRITICAL)
        # Load keywords dynamically from config to ensure sync with scoring
        severe_manipulation = self.risk_categories.get('manipulative_language', {}).get('keywords', [])
        moderate_manipulation = self.risk_categories.get('emotional_pressure', {}).get('keywords', [])
        
        # Benign keywords are not in risk categories anymore, so we don't count them for risk
        
        for clause in clauses:
            content_lower = clause['content'].lower()
            
            # Count matches by severity
            severe_count = sum(1 for kw in severe_manipulation if kw in content_lower)
            moderate_count = sum(1 for kw in moderate_manipulation if kw in content_lower)
            
            # Determine severity
            if severe_count >= 3:
                # HIGH RISK: Predatory manipulation
                flags.append({
                    'type': 'psychological_manipulation',
                    'severity': 'high',
                    'title': '🚨 CRITICAL: Psychological Manipulation Detected',
                    'description': f'This clause contains predatory psychological language designed to extract emotional compliance. '
                                   f'Found {severe_count} severe manipulation phrases that attempt to claim custody of your thoughts, '
                                   f'emotions, or mental state. This is HIGHLY INAPPROPRIATE for any legitimate contract.',
                    'clause_id': clause['clause_id'],
                    'recommendation': 'DO NOT SIGN. This document uses predatory psychological tactics. '
                                      'Legitimate contracts do not claim custody of your emotions, thoughts, or psychological state. '
                                      'Seek immediate legal counsel and report this to appropriate authorities.'
                })
            elif moderate_count >= 3:  # Trigger on 3+ moderate keywords
                # MEDIUM RISK: Emotional manipulation
                flags.append({
                    'type': 'emotional_manipulation',
                    'severity': 'medium',
                    'title': '⚠️ WARNING: Emotional Manipulation Detected',
                    'description': f'This clause uses emotionally manipulative language that may pressure you psychologically. '
                                   f'Found {moderate_count} concerning phrases related to self-worth, comparison, and emotional state. '
                                   f'While not as severe as predatory tactics, this is still inappropriate for standard contracts.',
                    'clause_id': clause['clause_id'],
                    'recommendation': 'Exercise caution. Request removal of emotionally manipulative language. '
                                      'Legitimate contracts should be neutral and not reference your psychological state. '
                                      'Consider seeking legal advice before signing.'
                })

        
        # Check for missing critical clauses
        critical_clauses = [
            'termination', 'liability', 'indemnification', 'dispute resolution',
            'payment', 'confidentiality'
        ]
        
        found_clauses = set()
        for clause in clauses:
            content_lower = clause['content'].lower()
            for critical in critical_clauses:
                if critical.replace(' ', '') in content_lower.replace(' ', ''):
                    found_clauses.add(critical)
        
        missing_clauses = set(critical_clauses) - found_clauses
        if missing_clauses:
            flags.append({
                'type': 'missing_critical_clause',
                'severity': 'high',
                'title': 'Missing Critical Clauses',
                'description': f"Contract may be missing: {', '.join(missing_clauses)}",
                'recommendation': 'Ensure all critical clauses are present or explicitly excluded.'
            })
        
        # Check for one-sided termination rights
        termination_clauses = [c for c in clauses if 'termination' in c['content'].lower()]
        for clause in termination_clauses:
            if 'at will' in clause['content'].lower() or 'sole discretion' in clause['content'].lower():
                flags.append({
                    'type': 'unilateral_termination',
                    'severity': 'high',
                    'title': 'Unilateral Termination Rights',
                    'description': 'One party has broad termination rights',
                    'clause_id': clause['clause_id'],
                    'recommendation': 'Negotiate for mutual termination rights or notice period.'
                })
        
        # Check for excessive penalties
        penalty_keywords = ['penalty', 'liquidated damages', 'fine']
        penalty_clauses = [c for c in clauses if any(kw in c['content'].lower() for kw in penalty_keywords)]
        if penalty_clauses:
            flags.append({
                'type': 'penalty_clause',
                'severity': 'medium',
                'title': 'Penalty Clauses Present',
                'description': f'Found {len(penalty_clauses)} clause(s) with penalty provisions',
                'recommendation': 'Review penalty amounts and ensure they are reasonable and proportionate.'
            })
        
        # Check for auto-renewal
        auto_renewal_keywords = ['auto-renew', 'automatic renewal', 'automatically renew']
        for clause in clauses:
            if any(kw in clause['content'].lower() for kw in auto_renewal_keywords):
                flags.append({
                    'type': 'auto_renewal',
                    'severity': 'medium',
                    'title': 'Auto-Renewal Clause',
                    'description': 'Contract may automatically renew without notice',
                    'clause_id': clause['clause_id'],
                    'recommendation': 'Ensure there is adequate notice period before auto-renewal.'
                })
        
        # Check for IP transfer
        ip_keywords = ['assigns all', 'transfers all', 'ownership of intellectual property']
        for clause in clauses:
            if any(kw in clause['content'].lower() for kw in ip_keywords):
                flags.append({
                    'type': 'ip_transfer',
                    'severity': 'high',
                    'title': 'Intellectual Property Transfer',
                    'description': 'Clause transfers IP ownership',
                    'clause_id': clause['clause_id'],
                    'recommendation': 'Carefully review IP ownership terms and consider retaining rights.'
                })
        
        # Check for broad indemnification
        indemnity_clauses = [c for c in clauses if 'indemnif' in c['content'].lower()]
        for clause in indemnity_clauses:
            if 'any and all' in clause['content'].lower() or 'unlimited' in clause['content'].lower():
                flags.append({
                    'type': 'broad_indemnity',
                    'severity': 'high',
                    'title': 'Broad Indemnification Clause',
                    'description': 'Indemnification obligations may be overly broad',
                    'clause_id': clause['clause_id'],
                    'recommendation': 'Negotiate for limited indemnification scope and caps.'
                })
        
        # Check for non-compete clauses
        non_compete_keywords = ['non-compete', 'non-competition', 'restraint of trade']
        for clause in clauses:
            if any(kw in clause['content'].lower() for kw in non_compete_keywords):
                flags.append({
                    'type': 'non_compete',
                    'severity': 'high',
                    'title': 'Non-Compete Clause',
                    'description': 'Clause restricts future business activities',
                    'clause_id': clause['clause_id'],
                    'recommendation': 'Ensure geographical and temporal scope are reasonable.'
                })
        
        # Check for ambiguous payment terms
        payment_clauses = [c for c in clauses if any(kw in c['content'].lower() for kw in ['payment', 'fee', 'compensation'])]
        for clause in payment_clauses:
            # Check if specific amounts or dates are mentioned
            has_amount = bool(re.search(r'₹|Rs\.?|\$|USD|INR|[0-9,]+', clause['content']))
            has_date = bool(re.search(r'\d+\s*days?|within|by|before|after', clause['content']))
            
            if not has_amount or not has_date:
                flags.append({
                    'type': 'ambiguous_payment',
                    'severity': 'medium',
                    'title': 'Ambiguous Payment Terms',
                    'description': 'Payment terms may lack specific amounts or timelines',
                    'clause_id': clause['clause_id'],
                    'recommendation': 'Clarify specific payment amounts, schedules, and methods.'
                })
        
        return flags
    
    def detect_unfavorable_terms(self, clauses: List[Dict]) -> List[Dict]:
        """Identify potentially unfavorable terms for SMEs"""
        unfavorable = []
        
        # Patterns indicating unfavorable terms
        unfavorable_patterns = {
            'Psychological Manipulation': r'(?i)(custody.*(?:doubts|fears|thoughts|emotions)|unknowingly agrees|knowingly accepts|temporary custody|mental state|self-blame|illusion of control|relinquish|personal accountability|weight of|no external system|resilience is built)',
            'Emotional Manipulation': r'(?i)(unresolved thoughts|delayed ambitions|fear of falling behind|worthlessness|self-doubt|controlled exposure|comparison may occur|confidence may dip|silence from others|avoiding truth|discomfort may be necessary|no reassurance)',
            'Unlimited Liability': r'(?i)(unlimited liability|without limit|no cap on liability)',
            'Waiver of Rights': r'(?i)(waives all|waiver of rights|foregoes any right)',
            'Unilateral Amendment': r'(?i)(may amend|can modify|right to change)(?!.*mutual|.*both parties)',
            'Exclusive Remedy': r'(?i)(sole and exclusive remedy|only remedy|limited to)',
            'No Warranty': r'(?i)(as is|without warranty|no warranties|disclaims all warranties)',
            'Indefinite Term': r'(?i)(perpetual|indefinite|no expiration|in perpetuity)',
            'Broad Assignment': r'(?i)(freely assign|without consent|may assign)',
            'Excessive Notice': r'(?i)(90 days|120 days|six months|one year)(?=.*notice)',
        }
        
        for clause in clauses:
            for term_name, pattern in unfavorable_patterns.items():
                if re.search(pattern, clause['content']):
                    unfavorable.append({
                        'clause_id': clause['clause_id'],
                        'clause_number': clause['clause_number'],
                        'term_type': term_name,
                        'content': clause['content'][:200] + '...' if len(clause['content']) > 200 else clause['content'],
                        'explanation': self._get_unfavorable_explanation(term_name),
                        'alternative': self._get_alternative_suggestion(term_name)
                    })
        
        return unfavorable
    
    def _get_unfavorable_explanation(self, term_type: str) -> str:
        """Get explanation for why a term is unfavorable"""
        if "Hindi" in self.language and term_type in self.hindi_translations:
            return self.hindi_translations[term_type]['explanation']
            
        explanations = {
            'Psychological Manipulation': '🚨 CRITICAL: This clause uses predatory psychological tactics to manipulate your mental and emotional state. NO legitimate contract should ever reference custody of your thoughts, emotions, fears, or psychological well-being.',
            'Emotional Manipulation': '⚠️ WARNING: This clause uses emotionally charged language that may pressure you psychologically. References to self-worth, comparison, and emotional states are inappropriate in contracts.',
            'Unlimited Liability': 'Exposes you to unlimited financial risk without any cap or protection.',
            'Waiver of Rights': 'You may be giving up important legal rights or protections.',
            'Unilateral Amendment': 'Other party can change terms without your consent.',
            'Exclusive Remedy': 'Limits your options if things go wrong.',
            'No Warranty': 'No guarantees about quality or fitness for purpose.',
            'Indefinite Term': 'No clear end date may make it difficult to exit.',
            'Broad Assignment': 'Other party can transfer obligations to unknown third parties.',
            'Excessive Notice': 'Very long notice period required for termination.',
        }
        return explanations.get(term_type, 'Potentially unfavorable term for your business.')
    
    def _get_alternative_suggestion(self, term_type: str) -> str:
        """Get alternative clause suggestions"""
        if "Hindi" in self.language and term_type in self.hindi_translations:
            return self.hindi_translations[term_type]['recommendation']
            
        alternatives = {
            'Psychological Manipulation': 'DO NOT SIGN THIS DOCUMENT. This is not a legitimate contract. Report to appropriate authorities. Seek immediate legal counsel. No negotiation is possible with manipulative psychological clauses - they must be completely removed.',
            'Emotional Manipulation': 'Request removal of all emotionally manipulative language. Contracts should use neutral, objective language. If the other party refuses, reconsider the relationship and seek legal advice.',
            'Unlimited Liability': 'Negotiate a liability cap equal to contract value or a specific amount.',
            'Waiver of Rights': 'Remove waiver clause or limit to specific, known rights.',
            'Unilateral Amendment': 'Require mutual consent for any amendments.',
            'Exclusive Remedy': 'Retain right to pursue additional remedies for material breaches.',
            'No Warranty': 'Request basic warranties about quality and fitness for purpose.',
            'Indefinite Term': 'Add a fixed term with renewal option or termination rights.',
            'Broad Assignment': 'Require your written consent for any assignment.',
            'Excessive Notice': 'Negotiate shorter notice period (30-60 days).',
        }
        return alternatives.get(term_type, 'Consult legal advisor for specific alternatives.')
    
    def generate_recommendations(self, clause_risks: List[Dict], risk_flags: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on risk assessment"""
        recommendations = []
        
        # High-risk clause recommendations
        high_risk_count = sum(1 for c in clause_risks if c['risk_level'] == 'high')
        if high_risk_count > 0:
            if "Hindi" in self.language:
                recommendations.append(
                    f"⚠️ {high_risk_count} उच्च-जोखिम वाले खंडों की पहचान की गई है। हस्ताक्षर करने से पहले इन्हें प्राथमिकता से देखें।"
                )
            else:
                recommendations.append(
                    f"⚠️ {high_risk_count} high-risk clause(s) identified. Prioritize reviewing these before signing."
                )
        
        # Category-specific recommendations
        risk_categories = set()
        for clause in clause_risks:
            risk_categories.update(clause['risk_categories'])
        
        if 'penalty_clause' in risk_categories:
            if "Hindi" in self.language:
                recommendations.append(
                    "💰 दंड खंडों (penalty clauses) की सावधानीपूर्वक समीक्षा करें। सुनिश्चित करें कि राशि उचित है।"
                )
            else:
                recommendations.append(
                    "💰 Review penalty clauses carefully. Ensure amounts are reasonable and proportionate."
                )
        
        if 'indemnity_clause' in risk_categories:
            if "Hindi" in self.language:
                recommendations.append(
                    "🛡️ क्षतिपूर्ति खंड (indemnity clause) की जांच करें। अपने दायित्व को सीमित करने का प्रयास करें।"
                )
            else:
                recommendations.append(
                    "🛡️ Check indemnity clauses. Try to limit your own liability."
                )
                recommendations.append(
                    "🛡️ Negotiate indemnity caps and ensure mutual indemnification where appropriate."
                )
        
        if 'unilateral_termination' in risk_categories:
            recommendations.append(
                "⏰ Request balanced termination rights with adequate notice periods for both parties."
            )
        
        if 'ip_transfer' in risk_categories:
            recommendations.append(
                "📝 Carefully review IP ownership terms. Consider retaining rights to pre-existing IP."
            )
        
        # Flag-based recommendations
        critical_flags = [f for f in risk_flags if f['severity'] == 'high']
        if len(critical_flags) >= 3:
            recommendations.append(
                "🚨 Multiple critical issues detected. Strongly recommend legal review before proceeding."
            )
        
        # General recommendation
        if not recommendations:
            recommendations.append(
                "✅ Overall risk appears manageable. Still recommend careful review of all terms."
            )
        
        return recommendations


if __name__ == "__main__":
    # Test the risk assessor
    assessor = RiskAssessor()
    print("Risk Assessor initialized successfully")
    print(f"Monitoring {len(assessor.risk_categories)} risk categories")
