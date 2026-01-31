"""
LLM Processor Module
Integrates with Claude 3 or GPT-4 for legal reasoning and plain language explanations
"""
import os
import json
from typing import Dict, List, Optional
import logging

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProcessor:
    """Processes legal contracts using LLM for reasoning and explanations"""
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize LLM client
        
        Args:
            provider: "anthropic" or "openai". If None, uses config setting
        """
        self.provider = provider or config.LLM_PROVIDER
        
        if self.provider == "anthropic":
            if not Anthropic:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            if not config.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
            self.model = config.CLAUDE_MODEL
        elif self.provider == "openai":
            if not OpenAI:
                raise ImportError("openai package not installed. Run: pip install openai")
            if not config.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.model = config.GPT_MODEL
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        logger.info(f"LLM Processor initialized with {self.provider}")
    
    def classify_contract_type(self, text: str) -> Dict:
        """
        Classify the type of contract
        
        Args:
            text: Contract text (first 2000 chars)
            
        Returns:
            Dictionary with contract type and confidence
        """
        prompt = f"""Analyze the following contract excerpt and classify its type.

Contract Types:
- Employment Agreement
- Vendor Contract
- Lease Agreement
- Partnership Deed
- Service Contract
- Non-Disclosure Agreement (NDA)
- Memorandum of Understanding (MoU)
- Purchase Order
- Consultancy Agreement
- License Agreement

Contract Excerpt:
{text[:2000]}

Respond in JSON format:
{{
    "contract_type": "the most likely type",
    "confidence": "high/medium/low",
    "reasoning": "brief explanation"
}}"""

        response = self._call_llm(prompt, max_tokens=300)
        
        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # Fallback parsing
            return {
                "contract_type": "Unknown",
                "confidence": "low",
                "reasoning": response
            }
    
    def generate_contract_summary(self, text: str, metadata: Dict) -> str:
        """
        Generate a plain language summary of the contract
        
        Args:
            text: Full contract text
            metadata: Contract metadata
            
        Returns:
            Plain language summary
        """
        # Truncate if too long
        text_sample = text[:15000] if len(text) > 15000 else text
        
        prompt = f"""You are a legal expert helping small business owners in India understand contracts.

Generate a concise, plain-language summary of this contract suitable for a small business owner.

Contract Details:
- Word Count: {metadata.get('word_count', 'N/A')}
- Language: {metadata.get('language', 'English')}

Contract Text:
{text_sample}

Provide a summary covering:
1. What type of contract this is
2. Who are the parties involved
3. What is the main purpose/scope
4. Key obligations of each party
5. Important dates or timelines
6. Payment terms (if applicable)
7. Termination conditions

Write in simple business language that a non-lawyer can understand. Use bullet points for clarity."""

        summary = self._call_llm(prompt, max_tokens=1000)
        return summary
    
    def explain_clause(self, clause_content: str, clause_type: str) -> Dict:
        """
        Explain a specific clause in plain language
        
        Args:
            clause_content: The clause text
            clause_type: Type of clause (e.g., "Liability", "Payment")
            
        Returns:
            Dictionary with explanation and key points
        """
        prompt = f"""You are a legal expert helping small business owners understand contract clauses.

Clause Type: {clause_type}

Clause Text:
{clause_content}

Provide:
1. Plain language explanation (what does this clause mean in simple terms?)
2. Key points (what are the most important things to know?)
3. Business impact (how does this affect a small business?)
4. Watch out for (any potential concerns or red flags?)

Write in simple language suitable for someone without legal training. Be concise but thorough."""

        response = self._call_llm(prompt, max_tokens=800)
        
        # Parse response into structured format
        return {
            "explanation": response,
            "clause_type": clause_type
        }
    
    def suggest_alternatives(self, clause_content: str, issue_type: str) -> List[str]:
        """
        Suggest alternative clause language for unfavorable terms
        
        Args:
            clause_content: Original clause text
            issue_type: Type of issue (e.g., "Unilateral Termination")
            
        Returns:
            List of alternative suggestions
        """
        prompt = f"""You are a legal expert advising small business owners in India.

Issue Identified: {issue_type}

Current Clause:
{clause_content}

Suggest 2-3 alternative clause phrasings that would be more balanced and favorable for a small business.
Keep suggestions practical and commonly accepted in Indian business contracts.

Format each suggestion as a numbered point with:
- The suggested clause language
- Brief explanation of why it's better

Be concise and practical."""

        response = self._call_llm(prompt, max_tokens=800)
        
        # Split into list of suggestions
        suggestions = [s.strip() for s in response.split('\n\n') if s.strip()]
        return suggestions
    
    def explain_legal_terms(self, terms: List[str]) -> Dict[str, str]:
        """
        Explain legal jargon in simple language
        
        Args:
            terms: List of legal terms to explain
            
        Returns:
            Dictionary mapping terms to explanations
        """
        terms_list = ', '.join(terms[:10])  # Limit to 10 terms
        
        prompt = f"""Explain the following legal terms in simple language that a small business owner can understand.

Terms: {terms_list}

For each term, provide a one-sentence explanation in plain English.
Format as JSON:
{{
    "term1": "explanation",
    "term2": "explanation",
    ...
}}"""

        response = self._call_llm(prompt, max_tokens=600)
        
        try:
            explanations = json.loads(response)
            return explanations
        except json.JSONDecodeError:
            # Fallback: return raw response
            return {"explanation": response}
    
    def assess_compliance(self, text: str, contract_type: str) -> Dict:
        """
        Assess basic compliance considerations for Indian SMEs
        
        Args:
            text: Contract text sample
            contract_type: Type of contract
            
        Returns:
            Dictionary with compliance observations
        """
        prompt = f"""You are a legal expert advising Indian small and medium businesses.

Contract Type: {contract_type}

Contract Excerpt:
{text[:10000]}

Identify key compliance considerations for this type of contract in India:
1. Is there mention of governing law? (Indian law is generally preferable)
2. Are there any concerning jurisdiction clauses? (Indian jurisdiction preferred)
3. For employment contracts: Any issues with labor law compliance?
4. For vendor contracts: GST and tax implications mentioned?
5. Are there proper dispute resolution mechanisms?

Provide observations in simple bullet points. Focus on what a small business should verify."""

        response = self._call_llm(prompt, max_tokens=800)
        
        return {
            "compliance_notes": response,
            "contract_type": contract_type
        }
    
    def generate_redline_suggestions(self, high_risk_clauses: List[Dict]) -> List[Dict]:
        """
        Generate specific suggestions for modifying high-risk clauses
        
        Args:
            high_risk_clauses: List of high-risk clause dictionaries
            
        Returns:
            List of redline suggestions
        """
        suggestions = []
        
        for clause in high_risk_clauses[:5]:  # Limit to top 5
            prompt = f"""You are a legal advisor helping a small business negotiate a contract.

High-Risk Clause:
{clause['content'][:500]}

Risk Level: {clause['risk_level']}
Risk Categories: {', '.join(clause.get('risk_categories', []))}

Suggest specific redlines (modifications) to make this clause more balanced.
Provide:
1. What to remove or soften
2. What to add for protection
3. Specific alternative wording

Be practical and concise."""

            response = self._call_llm(prompt, max_tokens=500)
            
            suggestions.append({
                'clause_id': clause['clause_id'],
                'clause_number': clause['clause_number'],
                'suggestion': response
            })
        
        return suggestions
    
    def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """
        Call the configured LLM provider
        
        Args:
            prompt: The prompt text
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response text
        """
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.content[0].text
            
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            return f"Error: Unable to process request - {str(e)}"
    
    def batch_explain_clauses(self, clauses: List[Dict], limit: int = 10) -> List[Dict]:
        """
        Explain multiple clauses efficiently
        
        Args:
            clauses: List of clause dictionaries
            limit: Maximum number of clauses to explain
            
        Returns:
            List of clause explanations
        """
        explanations = []
        
        # Prioritize high-risk and complex clauses
        sorted_clauses = sorted(
            clauses,
            key=lambda x: (x.get('risk_score', 0), x.get('complexity', {}).get('score', 0)),
            reverse=True
        )
        
        for clause in sorted_clauses[:limit]:
            try:
                explanation = self.explain_clause(
                    clause['content'],
                    clause.get('type', 'General')
                )
                explanations.append({
                    'clause_id': clause['clause_id'],
                    'clause_number': clause['clause_number'],
                    'explanation': explanation
                })
            except Exception as e:
                logger.error(f"Failed to explain clause {clause['clause_id']}: {e}")
                explanations.append({
                    'clause_id': clause['clause_id'],
                    'clause_number': clause['clause_number'],
                    'explanation': {'explanation': 'Unable to generate explanation'}
                })
        
        return explanations


if __name__ == "__main__":
    # Test the processor (requires API key)
    try:
        processor = LLMProcessor()
        print(f"LLM Processor initialized successfully with {processor.provider}")
    except Exception as e:
        print(f"Note: LLM Processor requires API keys to be configured: {e}")
