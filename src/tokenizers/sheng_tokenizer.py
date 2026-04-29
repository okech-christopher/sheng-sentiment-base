"""ShengTokenizer: NLP preprocessing for Sheng language content.

This module provides tokenization, normalization, and contextual sentiment
analysis for Sheng code-switching text. It handles the unique linguistic
patterns of Nairobi's urban slang.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TokenizedOutput:
    """Structured output from tokenization process."""
    
    original_text: str
    normalized_text: str
    tokens: List[str]
    slang_terms: List[str]
    code_switches: List[str]
    sentiment_score: float
    sentiment_label: str
    logistics_intent: Optional[str] = None
    logistics_severity: Optional[str] = None
    logistics_description: Optional[str] = None
    metadata: Dict[str, Any] = None


class ShengTokenizer:
    """Primary tokenizer for Sheng language preprocessing.
    
    Handles text normalization, slang standardization, code-switching detection,
    and contextual sentiment analysis specific to Kenyan urban language.
    
    Attributes:
        dictionary_path: Path to Sheng dictionary JSON
        slang_mappings: Dictionary of slang -> standard mappings
        sentiment_rules: Contextual sentiment rules for ambiguous terms
    """
    
    def __init__(
        self,
        dictionary_path: Optional[str] = None
    ):
        if dictionary_path is None:
            dictionary_path = Path(__file__).parent.parent.parent / \
                              "data" / "dictionaries" / "sheng_dictionary.json"
        else:
            dictionary_path = Path(dictionary_path)
        
        self.dictionary_path = dictionary_path
        self.slang_mappings: Dict[str, str] = {}
        self.sentiment_rules: Dict[str, Dict] = {}
        self.code_switch_patterns: Dict[str, List[str]] = {}
        
        self._load_dictionary()
        self._compile_patterns()
        
        logger.info(f"ShengTokenizer initialized with {len(self.slang_mappings)} slang terms")
    
    def _load_dictionary(self) -> None:
        """Load slang dictionary from JSON file."""
        try:
            with open(self.dictionary_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.slang_mappings = data.get("slang_mappings", {})
            self.sentiment_rules = data.get("contextual_sentiment", {})
            self.code_switch_patterns = data.get("code_switching_patterns", {})
            self.logistics_intent_rules = data.get("logistics_intent", {})
            self.logistics_keywords = data.get("logistics_keywords", {})
            
            logger.info(f"Loaded dictionary: {data.get('metadata', {}).get('name', 'Unknown')}")
        except FileNotFoundError:
            logger.error(f"Dictionary not found at {self.dictionary_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in dictionary: {e}")
            raise
    
    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        # Pattern for repeated characters (e.g., "soooo" -> "so")
        self.repeat_pattern = re.compile(r'(.)\1{2,}')
        
        # Pattern for common informal spellings
        self.informal_patterns = [
            (r'\bxaxa\b', 'haha'),
            (r'\bxixixi\b', 'hihi'),
            (r'\blolz\b', 'lol'),
            (r'\blmao\b', 'lmao'),
        ]
        
        # Pattern for code-switching indicators
        self.sheng_english_words: Set[str] = set(
            self.code_switch_patterns.get("sheng_english", [])
        )
        self.sheng_swahili_words: Set[str] = set(
            self.code_switch_patterns.get("sheng_swahili", [])
        )
    
    def normalize_repeated_chars(self, text: str) -> str:
        """Normalize excessive character repetition.
        
        Examples:
            "soooo good" -> "so good"
            "yeeees" -> "yes"
        """
        return self.repeat_pattern.sub(r'\1\1', text)
    
    def normalize_informal_spellings(self, text: str) -> str:
        """Standardize common informal spellings."""
        for pattern, replacement in self.informal_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    
    def normalize_slang(self, text: str) -> str:
        """Normalize Sheng slang to standard forms.
        
        Handles:
            - Variant spellings ('ronga', 'rongaa' -> 'rongai')
            - Common misspellings
            - Regional variations
        """
        words = text.lower().split()
        normalized_words = []
        detected_slang = []
        
        for word in words:
            # Clean word of punctuation for lookup
            clean_word = re.sub(r'[^\w]', '', word)
            
            if clean_word in self.slang_mappings:
                normalized = self.slang_mappings[clean_word]
                detected_slang.append(clean_word)
                # Preserve original punctuation
                word = word.replace(clean_word, normalized)
            
            normalized_words.append(word)
        
        return ' '.join(normalized_words), detected_slang
    
    def detect_code_switching(self, text: str) -> List[str]:
        """Detect code-switching between Sheng, Swahili, and English.
        
        Returns list of detected language indicators.
        """
        words = text.lower().split()
        switches = []
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            
            if clean_word in self.sheng_english_words:
                switches.append(f"{clean_word}:sheng-english")
            elif clean_word in self.sheng_swahili_words:
                switches.append(f"{clean_word}:sheng-swahili")
        
        return switches
    
    def _get_token_window(
        self,
        tokens: List[str],
        target_index: int,
        window_size: int = 3
    ) -> List[str]:
        """Get tokens within a window around the target index.
        
        Args:
            tokens: List of all tokens
            target_index: Index of the target token
            window_size: Number of tokens to look ahead/behind
            
        Returns:
            List of tokens within the window
        """
        start = max(0, target_index - window_size)
        end = min(len(tokens), target_index + window_size + 1)
        return tokens[start:end]
    
    def analyze_contextual_sentiment(
        self,
        text: str,
        slang_terms: List[str],
        use_lookahead: bool = True
    ) -> Tuple[float, str]:
        """Analyze sentiment with Sheng-specific context and look-ahead window.
        
        Many Sheng terms have context-dependent sentiment (e.g., 'kudunda').
        This method applies contextual rules with a 3-token look-ahead window
        to determine accurate sentiment based on neighboring words.
        
        Args:
            text: Original input text
            slang_terms: List of detected slang terms
            use_lookahead: Whether to use look-ahead window analysis
            
        Returns:
            Tuple of (sentiment_score, sentiment_label)
            Score range: -1.0 (negative) to 1.0 (positive)
        """
        text_lower = text.lower()
        tokens = re.findall(r'\b\w+\b', text_lower)
        
        # Base sentiment
        sentiment_score = 0.0
        sentiment_indicators = []
        
        # Analyze each slang term in context
        for term in slang_terms:
            if term in self.sentiment_rules:
                rule = self.sentiment_rules[term]
                default = rule.get("default", "neutral")
                contexts = rule.get("contexts", {})
                
                matched_context = None
                
                if use_lookahead:
                    # Find all indices where this term appears
                    term_indices = [i for i, t in enumerate(tokens) if t == term]
                    
                    # Check context within 3-token window for each occurrence
                    for idx in term_indices:
                        window = self._get_token_window(tokens, idx, window_size=3)
                        window_text = ' '.join(window)
                        
                        for context_word, sentiment in contexts.items():
                            if context_word in window_text:
                                matched_context = sentiment
                                sentiment_indicators.append(f"{term}:{sentiment} (window: {window_text})")
                                break
                        if matched_context:
                            break
                else:
                    # Fallback to simple keyword matching
                    for context_word, sentiment in contexts.items():
                        if context_word in text_lower:
                            matched_context = sentiment
                            sentiment_indicators.append(f"{term}:{sentiment}")
                            break
                
                # Apply sentiment
                if matched_context:
                    if matched_context == "positive":
                        sentiment_score += 0.5
                    elif matched_context == "negative":
                        sentiment_score -= 0.5
                else:
                    if default == "positive":
                        sentiment_score += 0.3
                    elif default == "negative":
                        sentiment_score -= 0.3
        
        # Normalize score to [-1, 1]
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
        
        # Determine label
        if sentiment_score > 0.1:
            label = "positive"
        elif sentiment_score < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        return sentiment_score, label
    
    def tokenize(self, text: str) -> TokenizedOutput:
        """Main tokenization pipeline.
        
        Executes full preprocessing:
            1. Text normalization
            2. Slang standardization
            3. Tokenization
            4. Code-switching detection
            5. Contextual sentiment analysis
        
        Args:
            text: Raw input text
            
        Returns:
            TokenizedOutput with full analysis
        """
        if not text or not text.strip():
            return TokenizedOutput(
                original_text=text,
                normalized_text="",
                tokens=[],
                slang_terms=[],
                code_switches=[],
                sentiment_score=0.0,
                sentiment_label="neutral",
                logistics_intent=None,
                logistics_severity=None,
                logistics_description=None,
                metadata={"error": "empty_input"}
            )
        
        original = text
        
        # Step 1: Normalize repeated characters
        text = self.normalize_repeated_chars(text)
        
        # Step 2: Normalize informal spellings
        text = self.normalize_informal_spellings(text)
        
        # Step 3: Normalize slang
        text, detected_slang = self.normalize_slang(text)
        
        # Step 4: Basic tokenization
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Step 5: Detect code-switching
        code_switches = self.detect_code_switching(text)
        
        # Step 6: Analyze sentiment
        sentiment_score, sentiment_label = self.analyze_contextual_sentiment(
            original, detected_slang
        )
        
        # Step 7: Detect logistics intent
        logistics_intent, logistics_severity, logistics_description = self.detect_logistics_intent(
            original, detected_slang
        )
        
        return TokenizedOutput(
            original_text=original,
            normalized_text=text,
            tokens=tokens,
            slang_terms=detected_slang,
            code_switches=code_switches,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            logistics_intent=logistics_intent,
            logistics_severity=logistics_severity,
            logistics_description=logistics_description,
            metadata={
                "token_count": len(tokens),
                "slang_count": len(detected_slang),
                "switch_count": len(code_switches),
                "has_logistics_intent": logistics_intent is not None
            }
        )
    
    def batch_tokenize(
        self,
        texts: List[str]
    ) -> List[TokenizedOutput]:
        """Process multiple texts efficiently."""
        return [self.tokenize(text) for text in texts]
    
    def extract_slang_vocabulary(
        self,
        texts: List[str]
    ) -> Dict[str, int]:
        """Extract and count slang frequency across corpus.
        
        Useful for identifying emerging slang terms.
        """
        slang_counts: Dict[str, int] = {}
        
        for text in texts:
            _, detected = self.normalize_slang(text)
            for term in detected:
                slang_counts[term] = slang_counts.get(term, 0) + 1
        
        return dict(sorted(slang_counts.items(), key=lambda x: x[1], reverse=True))
    
    def detect_logistics_intent(
        self,
        text: str,
        slang_terms: List[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Detect logistics intent from Sheng text.
        
        Identifies if the text contains logistics-related information
        such as police reports, traffic reports, route suggestions, etc.
        
        Args:
            text: Original input text
            slang_terms: List of detected slang terms
            
        Returns:
            Tuple of (intent, severity, description)
        """
        text_lower = text.lower()
        
        # Check each slang term for logistics intent
        for term in slang_terms:
            if term in self.logistics_intent_rules:
                rule = self.logistics_intent_rules[term]
                return (
                    rule.get("intent"),
                    rule.get("severity"),
                    rule.get("description")
                )
        
        # Check for logistics keywords
        for intent, keywords in self.logistics_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return (intent, "medium", f"Detected logistics keyword: {keyword}")
        
        return None, None, None


if __name__ == "__main__":
    # Test examples
    tokenizer = ShengTokenizer()
    
    test_texts = [
        "Hii mbogi ni fiti sana, wanadunda proper!",
        "Buda hana chapaa, amekudunda",
        "Ronga dem wangu anataka do",
        "Nairobi life ni noma tu!"
    ]
    
    for text in test_texts:
        result = tokenizer.tokenize(text)
        print(f"\nOriginal: {result.original_text}")
        print(f"Normalized: {result.normalized_text}")
        print(f"Slang: {result.slang_terms}")
        print(f"Sentiment: {result.sentiment_label} ({result.sentiment_score:.2f})")
