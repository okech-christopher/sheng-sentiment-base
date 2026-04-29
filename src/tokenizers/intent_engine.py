"""ShengIntentEngine: Logistics intent detection for Sheng text.

This module identifies whether a Sheng message contains logistics-related
information such as police reports, traffic updates, route changes, or obstacles.
"""

import logging
from typing import Tuple, Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Result of logistics intent detection."""
    
    is_logistics: bool
    intent_score: float
    intent_type: str
    severity: str
    description: str


class ShengIntentEngine:
    """Detects logistics intent in Sheng text.
    
    Uses keyword matching and pattern recognition to identify if a message
    is a logistics report (police, traffic, route, obstacle) or general chat.
    
    Attributes:
        logistics_keywords: Dictionary mapping intent types to keywords
        severity_weights: Weights for different intent severities
    """
    
    LOGISTICS_KEYWORDS: Dict[str, List[str]] = {
        "police_report": ["karao", "kanjo", "police", "check", "roadblock", "flyover"],
        "traffic_report": ["jam", "traffic", "congestion", "slow", "gridlock", "stand"],
        "obstacle_report": ["mreki", "breakdown", "mechanical", "stuck", "blocked", "accident"],
        "location_report": ["mabs", "stage", "drop", "pick", "location", "stage"],
        "route_suggestion": ["shorcut", "shortcut", "alternative", "other way"],
        "route_change": ["u-turn", "turn", "change", "redirect", "avoid"],
        "unofficial_route": ["panya", "unofficial", "backroute", "hidden"]
    }
    
    SEVERITY_WEIGHTS: Dict[str, float] = {
        "high": 0.9,
        "medium": 0.6,
        "low": 0.3
    }
    
    INTENT_SEVERITY: Dict[str, str] = {
        "police_report": "medium",
        "traffic_report": "medium",
        "obstacle_report": "high",
        "location_report": "low",
        "route_suggestion": "low",
        "route_change": "low",
        "unofficial_route": "medium"
    }
    
    INTENT_DESCRIPTIONS: Dict[str, str] = {
        "police_report": "Police checkpoint or presence detected",
        "traffic_report": "Traffic congestion or delay detected",
        "obstacle_report": "Vehicle breakdown or obstacle detected",
        "location_report": "Location or transport hub reference detected",
        "route_suggestion": "Alternative route suggestion detected",
        "route_change": "Route change or redirection detected",
        "unofficial_route": "Unofficial or informal route detected"
    }
    
    def __init__(self):
        """Initialize the intent engine."""
        logger.info("ShengIntentEngine initialized with logistics detection")
    
    def detect_intent(
        self,
        text: str,
        slang_terms: List[str]
    ) -> IntentResult:
        """Detect logistics intent from Sheng text.
        
        Args:
            text: Original input text
            slang_terms: List of detected slang terms
            
        Returns:
            IntentResult with detection results
        """
        text_lower = text.lower()
        matched_intents: Dict[str, int] = {}
        
        # Check for logistics keywords in text
        for intent_type, keywords in self.LOGISTICS_KEYWORDS.items():
            keyword_count = 0
            for keyword in keywords:
                if keyword in text_lower:
                    keyword_count += text_lower.count(keyword)
            
            if keyword_count > 0:
                matched_intents[intent_type] = keyword_count
        
        # Check slang terms for logistics intent
        for term in slang_terms:
            for intent_type, keywords in self.LOGISTICS_KEYWORDS.items():
                if term in keywords and intent_type not in matched_intents:
                    matched_intents[intent_type] = 1
        
        if not matched_intents:
            # No logistics intent detected
            return IntentResult(
                is_logistics=False,
                intent_score=0.0,
                intent_type="general",
                severity="none",
                description="General chat - no logistics intent detected"
            )
        
        # Determine primary intent (highest keyword count)
        primary_intent = max(matched_intents, key=matched_intents.get)
        keyword_count = matched_intents[primary_intent]
        
        # Calculate intent score based on keyword frequency
        base_score = self.SEVERITY_WEIGHTS[self.INTENT_SEVERITY[primary_intent]]
        intent_score = min(1.0, base_score + (keyword_count * 0.1))
        
        return IntentResult(
            is_logistics=True,
            intent_score=intent_score,
            intent_type=primary_intent,
            severity=self.INTENT_SEVERITY[primary_intent],
            description=self.INTENT_DESCRIPTIONS[primary_intent]
        )
    
    def get_supported_intents(self) -> List[str]:
        """Return list of supported logistics intent types."""
        return list(self.LOGISTICS_KEYWORDS.keys())


if __name__ == "__main__":
    # Test examples
    engine = ShengIntentEngine()
    
    test_cases = [
        ("Buda niko sapa, nisaidie chapaa.", []),
        ("Traffic imestand stage ya mabs, avoid panya route.", ["traffic", "stage", "mabs", "panya"]),
        ("Leo tunadunda sherehe na mzinga!", []),
        ("Karao wako mabs, jam imetupa", ["karao", "mabs", "jam"]),
        ("Mreki imetoka expressway, tumia shorcut", ["mreki", "shorcut"])
    ]
    
    for text, slang in test_cases:
        result = engine.detect_intent(text, slang)
        print(f"Text: {text}")
        print(f"  Is Logistics: {result.is_logistics}")
        print(f"  Intent: {result.intent_type}")
        print(f"  Score: {result.intent_score}")
        print(f"  Severity: {result.severity}")
        print(f"  Description: {result.description}")
        print()
