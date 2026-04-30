"""Sheng logic refinements for handling edge cases and ambiguity.

This module implements advanced logic for disambiguating ambiguous Sheng terms,
detecting negation, and scaling intensity based on context.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class RefinementResult:
    """Result of logic refinement."""
    
    sentiment_adjusted: bool
    original_sentiment: str
    refined_sentiment: str
    confidence_adjusted: float
    reasoning: str


class ShengLogicRefiner:
    """Advanced logic for Sheng sentiment disambiguation.
    
    Handles:
    - Negation detection (e.g., "si fiti" → not good)
    - Intensity scaling (e.g., "fiti sana" → very good)
    - Contextual disambiguation (e.g., "niko fiti" → I'm okay vs "fiti" → good)
    """
    
    # Negation patterns in Sheng/Swahili
    NEGATION_PATTERNS = [
        r'\bsi\s+\w+',  # "si fiti" (not good)
        r'\bhapana\b',  # "hapana" (no)
        r'\bhatukufanyi\b',  # "hatukufanyi" (we didn't)
        r'\bhaijui\b',  # "haijui" (doesn't know)
        r'\bhasemi\b',  # "hasemi" (hasn't said)
        r'\bhajarudi\b',  # "hajarudi" (hasn't returned)
        r'\bhanipati\b',  # "hanipati" (doesn't hurt me)
        r'\bhaifai\b',  # "haifai" (not necessary)
    ]
    
    # Intensity modifiers
    INTENSITY_MODIFIERS = {
        "sana": 1.5,  # "fiti sana" (very good)
        "kabisa": 1.4,  # "fiti kabisa" (completely good)
        "mengi": 1.3,  # "fiti mengi" (very good)
        "tu": 0.7,  # "fiti tu" (just okay)
        "kidogo": 0.8,  # "fiti kidogo" (a bit good)
        "hivi": 0.9,  # "fiti hivi" (this good)
    }
    
    # Contextual disambiguation rules
    CONTEXTUAL_RULES = {
        "fiti": {
            "personal_state": {
                "patterns": [r'\bniko\s+fiti\b', r'\bniliko\s+fiti\b', r'\bfiti\s+niko\b'],
                "sentiment": "neutral",
                "reasoning": "Personal state - 'I'm okay'"
            },
            "quality": {
                "patterns": [r'\bfiti\s+\w+', r'\b\w+\s+fiti\b'],
                "sentiment": "positive",
                "reasoning": "Quality assessment - 'good'"
            }
        },
        "noma": {
            "intensifier": {
                "patterns": [r'\bnoma\s+sana\b', r'\bfiti\s+noma\b'],
                "sentiment": "positive",
                "reasoning": "Intensifier - 'very good'"
            },
            "negative": {
                "patterns": [r'\bnoma\b'],
                "sentiment": "negative",
                "reasoning": "Negative - 'bad'"
            }
        }
    }
    
    def __init__(self):
        """Initialize the logic refiner."""
        self.negation_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.NEGATION_PATTERNS]
        
        # Compile contextual patterns
        self.contextual_patterns = {}
        for term, rules in self.CONTEXTUAL_RULES.items():
            self.contextual_patterns[term] = {}
            for rule_name, rule_data in rules.items():
                self.contextual_patterns[term][rule_name] = {
                    'patterns': [re.compile(pattern, re.IGNORECASE) for pattern in rule_data['patterns']],
                    'sentiment': rule_data['sentiment'],
                    'reasoning': rule_data['reasoning']
                }
    
    def detect_negation(self, text: str) -> bool:
        """Detect if text contains negation patterns.
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if negation detected, False otherwise
        """
        for pattern in self.negation_regex:
            if pattern.search(text):
                return True
        return False
    
    def scale_intensity(self, text: str, base_score: float) -> Tuple[float, str]:
        """Scale sentiment based on intensity modifiers.
        
        Args:
            text: Input text to analyze
            base_score: Base sentiment score
            
        Returns:
            Tuple of (adjusted_score, reasoning)
        """
        text_lower = text.lower()
        
        for modifier, factor in self.INTENSITY_MODIFIERS.items():
            if modifier in text_lower:
                adjusted_score = base_score * factor
                # Clamp to valid range
                adjusted_score = max(-1.0, min(1.0, adjusted_score))
                reasoning = f"Intensity scaled by {modifier} (factor: {factor})"
                return adjusted_score, reasoning
        
        return base_score, "No intensity modifier detected"
    
    def disambiguate_context(self, text: str, term: str, current_sentiment: str) -> Tuple[str, str]:
        """Disambiguate term based on context.
        
        Args:
            text: Input text containing the term
            term: Term to disambiguate
            current_sentiment: Current sentiment label
            
        Returns:
            Tuple of (disambiguated_sentiment, reasoning)
        """
        if term not in self.contextual_patterns:
            return current_sentiment, f"No contextual rules for {term}"
        
        for rule_name, rule_data in self.contextual_patterns[term].items():
            for pattern in rule_data['patterns']:
                if pattern.search(text):
                    return rule_data['sentiment'], rule_data['reasoning']
        
        return current_sentiment, f"No context pattern matched for {term}"
    
    def refine_sentiment(
        self,
        text: str,
        base_sentiment: str,
        base_score: float,
        slang_terms: List[str]
    ) -> RefinementResult:
        """Apply all refinement logic to sentiment analysis.
        
        Args:
            text: Input text
            base_sentiment: Base sentiment from tokenizer
            base_score: Base sentiment score from tokenizer
            slang_terms: List of detected slang terms
            
        Returns:
            RefinementResult with adjustments
        """
        refined_sentiment = base_sentiment
        refined_score = base_score
        reasoning = []
        sentiment_adjusted = False
        
        # Check for negation
        if self.detect_negation(text):
            # Flip sentiment for negation
            if refined_sentiment == "positive":
                refined_sentiment = "negative"
                refined_score = -abs(refined_score)
            elif refined_sentiment == "negative":
                refined_sentiment = "positive"
                refined_score = abs(refined_score)
            reasoning.append("Negation detected - sentiment flipped")
            sentiment_adjusted = True
        
        # Check for intensity modifiers
        intensity_score, intensity_reasoning = self.scale_intensity(text, refined_score)
        if intensity_score != refined_score:
            refined_score = intensity_score
            reasoning.append(intensity_reasoning)
            sentiment_adjusted = True
        
        # Check for contextual disambiguation
        for term in slang_terms:
            if term in self.contextual_patterns:
                context_sentiment, context_reasoning = self.disambiguate_context(text, term, refined_sentiment)
                if context_sentiment != refined_sentiment:
                    refined_sentiment = context_sentiment
                    reasoning.append(context_reasoning)
                    sentiment_adjusted = True
                    break
        
        # Calculate confidence adjustment
        confidence_adjustment = 0.0
        if sentiment_adjusted:
            confidence_adjustment = 0.1  # Boost confidence for refined predictions
        
        return RefinementResult(
            sentiment_adjusted=sentiment_adjusted,
            original_sentiment=base_sentiment,
            refined_sentiment=refined_sentiment,
            confidence_adjusted=confidence_adjustment,
            reasoning="; ".join(reasoning) if reasoning else "No refinements applied"
        )


if __name__ == "__main__":
    # Test examples
    refiner = ShengLogicRefiner()
    
    test_cases = [
        ("Si fiti hii kitu", "negative", -0.5, ["fiti"]),
        ("Fiti sana", "positive", 0.5, ["fiti"]),
        ("Niko fiti", "neutral", 0.5, ["fiti"]),
        ("Hii mbogi ni noma sana", "positive", 0.5, ["noma"]),
        ("Noma hii kitu", "negative", -0.5, ["noma"]),
    ]
    
    for text, sentiment, score, slang in test_cases:
        result = refiner.refine_sentiment(text, sentiment, score, slang)
        print(f"Text: {text}")
        print(f"  Original: {result.original_sentiment} ({score})")
        print(f"  Refined: {result.refined_sentiment} ({refined_score if 'refined_score' in result.__dict__ else 'N/A'})")
        print(f"  Reasoning: {result.reasoning}")
        print()
