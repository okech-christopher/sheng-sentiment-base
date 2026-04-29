"""Unit tests for ShengTokenizer."""

import unittest
from src.tokenizers.sheng_tokenizer import ShengTokenizer


class TestShengTokenizer(unittest.TestCase):
    """Test cases for ShengTokenizer."""
    
    @classmethod
    def setUpClass(cls):
        cls.tokenizer = ShengTokenizer()
    
    def test_normalize_repeated_chars(self):
        """Test excessive character normalization."""
        result = self.tokenizer.normalize_repeated_chars("soooo good")
        self.assertEqual(result, "soo good")
    
    def test_normalize_slang_variants(self):
        """Test slang variant normalization."""
        text, slang = self.tokenizer.normalize_slang("Ronga dem wangu")
        self.assertIn("ronga", slang)
        self.assertIn("rongai", text)
    
    def test_detect_slang_terms(self):
        """Test slang term detection."""
        text = "Buda hana chapaa"
        _, detected = self.tokenizer.normalize_slang(text)
        self.assertIn("buda", detected)
        self.assertIn("chapaa", detected)
    
    def test_sentiment_analysis_negative(self):
        """Test negative sentiment detection."""
        result = self.tokenizer.tokenize("Ame kudunda job, hata pesa")
        self.assertEqual(result.sentiment_label, "negative")
    
    def test_sentiment_analysis_positive(self):
        """Test positive sentiment detection."""
        result = self.tokenizer.tokenize("Hii mbogi ni fiti sana")
        self.assertEqual(result.sentiment_label, "positive")
    
    def test_empty_input(self):
        """Test handling of empty input."""
        result = self.tokenizer.tokenize("")
        self.assertEqual(result.sentiment_label, "neutral")
        self.assertEqual(len(result.tokens), 0)
    
    def test_tokenization_output(self):
        """Test complete tokenization output structure."""
        result = self.tokenizer.tokenize("Nairobi life ni noma")
        
        self.assertIsNotNone(result.original_text)
        self.assertIsNotNone(result.normalized_text)
        self.assertIsInstance(result.tokens, list)
        self.assertIsInstance(result.slang_terms, list)
        self.assertIsInstance(result.sentiment_score, float)
    
    def test_kudunda_negative_context_exam(self):
        """Test 'kudunda' with negative context (exam/job)."""
        result = self.tokenizer.tokenize("Ali kudunda mtihani, amefeli")
        self.assertEqual(result.sentiment_label, "negative")
        self.assertIn("kudunda", result.slang_terms)
    
    def test_kudunda_positive_context_party(self):
        """Test 'kudunda' with positive context (party/sherehe)."""
        result = self.tokenizer.tokenize("Kudunda sherehe, mzinga full!")
        self.assertEqual(result.sentiment_label, "positive")
        self.assertIn("kudunda", result.slang_terms)
    
    def test_sapa_negative_context_money(self):
        """Test 'sapa' with negative context (money/chapaa)."""
        result = self.tokenizer.tokenize("Niko sapa, hata chapaa sina")
        self.assertEqual(result.sentiment_label, "negative")
        self.assertIn("sapa", result.slang_terms)
    
    def test_lookahead_window_accuracy(self):
        """Test 3-token look-ahead window for context detection."""
        # Positive: kudunda near sherehe
        result_pos = self.tokenizer.tokenize("Tulikwenda kudunda sherehe")
        self.assertEqual(result_pos.sentiment_label, "positive")
        
        # Negative: kudunda near mtihani
        result_neg = self.tokenizer.tokenize("Ame kudunda mtihani ya kwanza")
        self.assertEqual(result_neg.sentiment_label, "negative")
    
    def test_code_switching_sentiment_flip(self):
        """Test sentiment flip based on code-switching context."""
        # Same slang term, different contexts
        text1 = "Kudunda job, hata chapaa"  # Negative
        text2 = "Kudunda mzinga, sherehe"  # Positive
        
        result1 = self.tokenizer.tokenize(text1)
        result2 = self.tokenizer.tokenize(text2)
        
        self.assertEqual(result1.sentiment_label, "negative")
        self.assertEqual(result2.sentiment_label, "positive")


if __name__ == "__main__":
    unittest.main()
