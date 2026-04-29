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
        result = self.tokenizer.tokenize("Buda hana chapaa, amekudunda")
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


if __name__ == "__main__":
    unittest.main()
