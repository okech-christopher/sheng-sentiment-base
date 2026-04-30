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


class RecursiveSlangResolver:
    """Advanced resolver for multi-intent Sheng sentences.
    
    Handles complex sentences with multiple intents using:
    - Weighting matrix for intent prioritization
    - Verb proximity analysis
    - Contextual intent resolution
    """
    
    # Intent categories and their weights
    INTENT_WEIGHTS = {
        "financial": 0.8,
        "logistics": 0.7,
        "social": 0.6,
        "emotional": 0.5
    }
    
    # Financial distress keywords
    FINANCIAL_KEYWORDS = {
        "sapa", "chapaa", "do", "doh", "luku", "kuset", "ganji", "mullah",
        "mulla", "pesa", "mali", "fedha", "kash", "cash", "money", "bill",
        "debt", "loan", "advance", "salary", "pay", "stima", "kplc"
    }
    
    # Logistics keywords
    LOGISTICS_KEYWORDS = {
        "boda", "stage", "route", "traffic", "jam", "karao", "mreki", "mabs",
        "expressway", "flyover", "cbd", "westlands", "thika", "mombasa", "road"
    }
    
    # Social commerce keywords
    SOCIAL_KEYWORDS = {
        "mboga", "genge", "squad", "crew", "team", "gang", "fam", "family",
        "sherehe", "party", "celebration", "birthday", "wedding", "event"
    }
    
    def __init__(self):
        """Initialize the resolver."""
        self.all_keywords = {
            "financial": self.FINANCIAL_KEYWORDS,
            "logistics": self.LOGISTICS_KEYWORDS,
            "social": self.SOCIAL_KEYWORDS
        }
    
    def detect_intents(self, text: str) -> Dict[str, float]:
        """Detect multiple intents in text with confidence scores.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary of intent -> confidence score
        """
        text_lower = text.lower()
        intents = {}
        
        # Count keyword occurrences for each intent
        for intent, keywords in self.all_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if count > 0:
                # Base confidence from keyword frequency
                base_confidence = min(1.0, count * 0.3)
                # Apply intent weight
                weighted_confidence = base_confidence * self.INTENT_WEIGHTS.get(intent, 0.5)
                intents[intent] = weighted_confidence
        
        return intents
    
    def resolve_primary_intent(self, intents: Dict[str, float], text: str) -> Tuple[str, float]:
        """Resolve primary intent using weighting matrix.
        
        Args:
            intents: Dictionary of intent -> confidence scores
            text: Original text for context
            
        Returns:
            Tuple of (primary_intent, confidence)
        """
        if not intents:
            return "general", 0.0
        
        # Sort by confidence score
        sorted_intents = sorted(intents.items(), key=lambda x: x[1], reverse=True)
        
        # If there's a clear winner
        if len(sorted_intents) == 1 or sorted_intents[0][1] > sorted_intents[1][1] + 0.2:
            return sorted_intents[0]
        
        # Use verb proximity for tie-breaking
        return self._verb_proximity_resolution(sorted_intents[:2], text)
    
    def _verb_proximity_resolution(self, top_intents: List[Tuple[str, float]], text: str) -> Tuple[str, float]:
        """Resolve ties using verb proximity analysis.
        
        Args:
            top_intents: Top 2 intents with their scores
            text: Original text
            
        Returns:
            Tuple of (resolved_intent, confidence)
        """
        tokens = text.lower().split()
        
        # Find positions of keywords for each intent
        intent_positions = {}
        for intent, _ in top_intents:
            keywords = self.all_keywords[intent]
            positions = []
            for i, token in enumerate(tokens):
                if token in keywords:
                    positions.append(i)
            if positions:
                intent_positions[intent] = min(positions)  # First occurrence
        
        # Choose intent with earliest keyword occurrence
        if intent_positions:
            primary_intent = min(intent_positions, key=intent_positions.get)
            # Use the original confidence score
            original_confidence = dict(top_intents)[primary_intent]
            return primary_intent, original_confidence
        
        # Fallback to highest confidence
        return top_intents[0]


class ShengLogicRefiner:
    """Advanced logic for Sheng sentiment disambiguation.
    
    Handles:
    - Negation detection (e.g., "si fiti" -> not good)
    - Intensity scaling (e.g., "fiti sana" -> very good)
    - Contextual disambiguation (e.g., "niko fiti" -> I'm okay vs "fiti" -> good)
    - Multi-intent resolution with RecursiveSlangResolver
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
        
        # Initialize recursive resolver
        self.intent_resolver = RecursiveSlangResolver()
        
        # Initialize intensity modifiers
        self.INTENSITY_MODIFIERS = {
            "sana": 1.5,  # "fiti sana" (very good)
            "kabisa": 1.4,  # "fiti kabisa" (completely good)
            "mengi": 1.3,  # "fiti mengi" (very good)
            "tu": 0.7,  # "fiti tu" (just okay)
            "kidogo": 0.8,  # "fiti kidogo" (a bit good)
            "hivi": 0.9,  # "fiti hivi" (this good)
        }
    
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
        
        # Apply fintech boost weighting logic
        text_lower = text.lower()
        tokens = text_lower.split()
        
        # Financial context boost
        financial_tokens = ['sapa', 'kuset', 'ganji']
        for token in tokens:
            if token in financial_tokens and intents.get("financial", 0) > 0:
                # Apply 0.25 boost to sentiment score
                score = min(1.0, score + 0.25)
                base_confidence = min(1.0, base_confidence + 0.25)
                if sentiment == "neutral":
                    sentiment = "negative"
                    score = -abs(score)  # Ensure negative for financial distress
                break
        
        # Logistics context boost
        logistics_tokens = ['boda', 'nduthi', 'package']
        for token in tokens:
            if token in logistics_tokens and intents.get("logistics", 0) > 0:
                # Apply 0.20 boost to logistics intent
                base_confidence = min(1.0, base_confidence + 0.20)
                break
        
        # Apply weighting logic for financial distress
        if intents.get("financial", 0) > 0:
            financial_confidence = intents["financial"]
            
            # WEIGHTING: If 'Sapa' or 'Kuset' detected and logistics score < 0.7, FORCE re-classification
            if financial_confidence > self.LOGISTICS_CONFIDENCE_THRESHOLD and logistics_result.intent_score < self.FINANCIAL_RECLASSIFICATION_THRESHOLD:
                # Check for specific financial distress keywords
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
        
        # Check for multi-intent resolution first
        intents = self.intent_resolver.detect_intents(text)
        if intents:
            primary_intent, confidence = self.intent_resolver.resolve_primary_intent(intents, text)
            
            # Adjust sentiment based on primary intent
            if primary_intent == "financial":
                # Financial distress is usually negative
                if refined_sentiment == "neutral":
                    refined_sentiment = "negative"
                    refined_score = -0.6
                    reasoning.append("Financial intent detected - adjusted to negative")
                    sentiment_adjusted = True
            elif primary_intent == "social":
                # Social context is usually positive
                if refined_sentiment == "neutral":
                    refined_sentiment = "positive"
                    refined_score = 0.6
                    reasoning.append("Social intent detected - adjusted to positive")
                    sentiment_adjusted = True
        
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
            confidence_adjustment = 0.15  # Boost confidence for refined predictions
        
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
