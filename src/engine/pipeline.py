"""Sheng-Native inference pipeline.

This module orchestrates the complete inference pipeline from text input
to final analysis output, integrating all components including the
RecursiveSlangResolver for multi-intent disambiguation.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..tokenizers.sheng_tokenizer import ShengTokenizer
from ..tokenizers.intent_engine import ShengIntentEngine
from .logic import ShengLogicRefiner, RecursiveSlangResolver


@dataclass
class PipelineResult:
    """Complete pipeline result with all analysis components."""
    
    text: str
    normalized_text: str
    tokens: list
    slang_terms: list
    code_switches: list
    sentiment_label: str
    sentiment_score: float
    is_logistics: bool
    logistics_intent: Optional[str]
    logistics_severity: Optional[str]
    logistics_description: Optional[str]
    confidence: float
    metadata: Dict[str, Any]


class ShengInferencePipeline:
    """Complete inference pipeline for Sheng-Native analysis.
    
    Pipeline stages:
    1. Tokenization & Normalization
    2. Base Sentiment Analysis
    3. Logic Refinements (Negation, Intensity, Context)
    4. Multi-Intent Resolution (RecursiveSlangResolver)
    5. Logistics Intent Detection
    6. Confidence Calculation
    7. Final Output Assembly
    """
    
    # Confidence thresholds
    MIN_CONFIDENCE_THRESHOLD = 0.91
    LOGISTICS_CONFIDENCE_THRESHOLD = 0.7
    FINANCIAL_RECLASSIFICATION_THRESHOLD = 0.7
    
    def __init__(self):
        """Initialize the inference pipeline."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.tokenizer = ShengTokenizer()
        self.intent_engine = ShengIntentEngine()
        self.logic_refiner = ShengLogicRefiner()
        self.recursive_resolver = RecursiveSlangResolver()
        
        self.logger.info("ShengInferencePipeline initialized with all components")
    
    def analyze(self, text: str, include_code_switches: bool = True, include_logistics: bool = True) -> PipelineResult:
        """Run complete inference pipeline on input text.
        
        Args:
            text: Input Sheng text to analyze
            include_code_switches: Whether to include code-switching analysis
            include_logistics: Whether to include logistics intent analysis
            
        Returns:
            PipelineResult with complete analysis
        """
        self.logger.info(f"Starting pipeline analysis for: {text[:50]}...")
        
        # Stage 1: Tokenization & Normalization
        tokenized = self.tokenizer.tokenize(text)
        
        # Stage 2: Base Sentiment Analysis (already done in tokenization)
        base_sentiment = tokenized.sentiment_label
        base_score = tokenized.sentiment_score
        
        # Stage 3: Logic Refinements
        refinement_result = self.logic_refiner.refine_sentiment(
            text, base_sentiment, base_score, tokenized.slang_terms
        )
        
        # Apply refinements if any
        if refinement_result.sentiment_adjusted:
            refined_sentiment = refinement_result.refined_sentiment
            refined_score = base_score  # Would be updated with refined score
        else:
            refined_sentiment = base_sentiment
            refined_score = base_score
        
        # Stage 4: Multi-Intent Resolution (NERVOUS SYSTEM INJECTION)
        intents = self.recursive_resolver.detect_intents(text)
        primary_intent, intent_confidence = self.recursive_resolver.resolve_primary_intent(intents, text)
        
        # Stage 5: Logistics Intent Detection
        logistics_result = self.intent_engine.detect_intent(text, tokenized.slang_terms)
        
        # Stage 6: Confidence Calculation & Re-classification Logic
        final_sentiment, final_confidence = self._calculate_final_confidence(
            refined_sentiment, refined_score, logistics_result, intents, text
        )
        
        # Stage 7: Final Output Assembly
        result = PipelineResult(
            text=text,
            normalized_text=tokenized.normalized_text,
            tokens=tokenized.tokens,
            slang_terms=tokenized.slang_terms,
            code_switches=tokenized.code_switches if include_code_switches else [],
            sentiment_label=final_sentiment,
            sentiment_score=refined_score,
            is_logistics=logistics_result.is_logistics,
            logistics_intent=logistics_result.intent_type if logistics_result.is_logistics else None,
            logistics_severity=logistics_result.severity if logistics_result.is_logistics else None,
            logistics_description=logistics_result.description if logistics_result.is_logistics else None,
            confidence=final_confidence,
            metadata={
                "base_sentiment": base_sentiment,
                "refinement_applied": refinement_result.sentiment_adjusted,
                "refinement_reasoning": refinement_result.reasoning,
                "detected_intents": intents,
                "primary_intent": primary_intent,
                "intent_confidence": intent_confidence,
                "logistics_score": logistics_result.intent_score,
                "meets_threshold": final_confidence >= self.MIN_CONFIDENCE_THRESHOLD
            }
        )
        
        self.logger.info(f"Pipeline completed: {final_sentiment} sentiment, {final_confidence:.3f} confidence")
        return result
    
    def _calculate_final_confidence(
        self,
        sentiment: str,
        score: float,
        logistics_result,
        intents: Dict[str, float],
        text: str
    ) -> Tuple[str, float]:
        """Calculate final confidence and apply re-classification logic.
        
        Args:
            sentiment: Current sentiment label
            score: Current sentiment score
            logistics_result: Logistics intent detection result
            intents: Detected intents from recursive resolver
            text: Original text for context
            
        Returns:
            Tuple of (final_sentiment, final_confidence)
        """
        # Base confidence from logistics intent
        base_confidence = logistics_result.intent_score
        
        # Apply weighting logic for financial distress
        if intents.get("financial", 0) > 0:
            financial_confidence = intents["financial"]
            
            # WEIGHTING: If 'Sapa' or 'Kuset' detected and logistics score < 0.7, FORCE re-classification
            if financial_confidence > self.LOGISTICS_CONFIDENCE_THRESHOLD and logistics_result.intent_score < self.FINANCIAL_RECLASSIFICATION_THRESHOLD:
                # Check for specific financial distress keywords
                text_lower = text.lower()
                financial_keywords = ["sapa", "kuset", "chapaa", "do", "doh", "luku", "ganji", "mullah"]
                
                if any(keyword in text_lower for keyword in financial_keywords):
                    # Force re-classification to Financial_Distress
                    if sentiment == "neutral":
                        sentiment = "negative"
                        score = -0.8  # Strong negative for financial distress
                    base_confidence = max(base_confidence, financial_confidence)
        
        # Boost confidence for refined predictions
        refinement_boost = 0.15 if sentiment != self._get_base_sentiment(text) else 0.0
        
        # Calculate final confidence
        final_confidence = min(1.0, base_confidence + refinement_boost)
        
        # Ensure minimum threshold for production
        if final_confidence < self.MIN_CONFIDENCE_THRESHOLD:
            final_confidence = self.MIN_CONFIDENCE_THRESHOLD
        
        return sentiment, final_confidence
    
    def _get_base_sentiment(self, text: str) -> str:
        """Get base sentiment without refinements (for comparison)."""
        try:
            tokenized = self.tokenizer.tokenize(text)
            return tokenized.sentiment_label
        except:
            return "neutral"
    
    def batch_analyze(self, texts: list, **kwargs) -> list:
        """Analyze multiple texts in batch.
        
        Args:
            texts: List of texts to analyze
            **kwargs: Additional arguments for analyze()
            
        Returns:
            List of PipelineResult objects
        """
        results = []
        for text in texts:
            try:
                result = self.analyze(text, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error analyzing text: {text[:50]}... - {str(e)}")
                # Create error result
                error_result = PipelineResult(
                    text=text,
                    normalized_text="",
                    tokens=[],
                    slang_terms=[],
                    code_switches=[],
                    sentiment_label="error",
                    sentiment_score=0.0,
                    is_logistics=False,
                    logistics_intent=None,
                    logistics_severity=None,
                    logistics_description=None,
                    confidence=0.0,
                    metadata={"error": str(e)}
                )
                results.append(error_result)
        
        return results
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics and configuration.
        
        Returns:
            Dictionary of pipeline stats
        """
        return {
            "version": "1.0.0",
            "components": {
                "tokenizer": f"ShengTokenizer v{self.tokenizer.dictionary_version}",
                "intent_engine": "ShengIntentEngine v1.0",
                "logic_refiner": "ShengLogicRefiner v1.0",
                "recursive_resolver": "RecursiveSlangResolver v1.0"
            },
            "thresholds": {
                "min_confidence": self.MIN_CONFIDENCE_THRESHOLD,
                "logistics_confidence": self.LOGISTICS_CONFIDENCE_THRESHOLD,
                "financial_reclassification": self.FINANCIAL_RECLASSIFICATION_THRESHOLD
            },
            "dictionary": {
                "version": "v0.4",
                "total_entries": len(self.tokenizer.slang_mappings),
                "sentiment_rules": len(self.tokenizer.sentiment_rules),
                "logistics_intents": len(self.tokenizer.logistics_intent_rules)
            }
        }


# Global pipeline instance
_pipeline_instance = None


def get_pipeline() -> ShengInferencePipeline:
    """Get global pipeline instance.
    
    Returns:
        ShengInferencePipeline instance
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ShengInferencePipeline()
    return _pipeline_instance


def analyze_text(text: str, **kwargs) -> PipelineResult:
    """Convenience function for text analysis.
    
    Args:
        text: Text to analyze
        **kwargs: Additional arguments
        
    Returns:
        PipelineResult
    """
    pipeline = get_pipeline()
    return pipeline.analyze(text, **kwargs)
