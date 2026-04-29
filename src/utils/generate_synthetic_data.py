"""Synthetic data generator for Sheng golden dataset.

This script generates labeled Sheng sentences for model evaluation
by combining subjects, actions, and contexts with known sentiment/intent labels.
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict

from ..tokenizers.sheng_tokenizer import ShengTokenizer


@dataclass
class SyntheticSample:
    """A labeled synthetic Sheng sample."""
    
    text: str
    sentiment_label: str
    sentiment_score: float
    logistics_intent: str
    logistics_severity: str
    is_logistics: bool
    confidence: float


class ShengSyntheticGenerator:
    """Generate synthetic Sheng data for evaluation.
    
    Creates labeled examples by combining:
    - Subjects: Buda, Boda, Mbogi, etc.
    - Actions: Kudunda, Sapa, Dunda, etc.
    - Contexts: Sherehe, Mtihani, Stage, etc.
    """
    
    # Subject categories
    SUBJECTS = {
        "person": ["Buda", "Bazu", "Msee", "Chali", "Jamaa", "Dem", "Dame"],
        "group": ["Mbogi", "Crew", "Squad", "Genje"],
        "vehicle": ["Boda", "Nganya", "Mathree", "Matatu"]
    }
    
    # Action-verb mappings with sentiment
    ACTIONS = {
        "kudunda": {
            "sentiment": "negative",
            "contexts": {
                "exam": {"text": "mtihani", "sentiment": "negative"},
                "job": {"text": "job", "sentiment": "negative"},
                "party": {"text": "sherehe", "sentiment": "positive"},
                "bottle": {"text": "mzinga", "sentiment": "positive"}
            }
        },
        "sapa": {
            "sentiment": "negative",
            "contexts": {
                "money": {"text": "chapaa", "sentiment": "negative"},
                "cash": {"text": "do", "sentiment": "negative"},
                "wealth": {"text": "mulla", "sentiment": "negative"}
            }
        },
        "dunda": {
            "sentiment": "positive",
            "contexts": {
                "party": {"text": "sherehe", "sentiment": "positive"},
                "waste": {"text": "waste", "sentiment": "negative"}
            }
        },
        "noma": {
            "sentiment": "negative",
            "contexts": {
                "intense": {"text": "intense", "sentiment": "positive"},
                "bad": {"text": "bad", "sentiment": "negative"}
            }
        }
    }
    
    # Logistics-specific templates
    LOGISTICS_TEMPLATES = [
        ("Karao wako {location}", "police_report", "medium"),
        ("Jam imekali {location}", "traffic_report", "medium"),
        ("Mreki imekwa {location}", "obstacle_report", "high"),
        ("Stage ya {location} imejaa", "location_report", "low"),
        ("Tumia {route} kuepuka {location}", "route_suggestion", "low"),
        ("Avoid panya route near {location}", "unofficial_route", "medium"),
        ("U-turn at {location}", "route_change", "low")
    ]
    
    LOCATIONS = ["mabs", "stage", "town", "expressway", "flyover", "CBD", "Westlands"]
    ROUTES = ["shorcut", "main road", "back route", "alternative"]
    
    def __init__(self, tokenizer: ShengTokenizer = None):
        """Initialize the generator.
        
        Args:
            tokenizer: Optional ShengTokenizer instance
        """
        self.tokenizer = tokenizer or ShengTokenizer()
    
    def generate_contextual_sample(self) -> SyntheticSample:
        """Generate a sample with contextual sentiment.
        
        Returns:
            SyntheticSample with labeled sentiment
        """
        # Randomly select action and context
        action = random.choice(list(self.ACTIONS.keys()))
        action_data = self.ACTIONS[action]
        context_name, context_data = random.choice(list(action_data["contexts"].items()))
        
        # Build sentence
        subject = random.choice(self.SUBJECTS["person"])
        sentence = f"{subject} {action} {context_data['text']}"
        
        return SyntheticSample(
            text=sentence,
            sentiment_label=context_data["sentiment"],
            sentiment_score=0.7 if context_data["sentiment"] == "positive" else -0.7,
            logistics_intent="general",
            logistics_severity="none",
            is_logistics=False,
            confidence=0.8
        )
    
    def generate_logistics_sample(self) -> SyntheticSample:
        """Generate a logistics-specific sample.
        
        Returns:
            SyntheticSample with logistics intent
        """
        template = random.choice(self.LOGISTICS_TEMPLATES)
        location = random.choice(self.LOCATIONS)
        
        if "{route}" in template[0]:
            route = random.choice(self.ROUTES)
            sentence = template[0].format(location=location, route=route)
        else:
            sentence = template[0].format(location=location)
        
        return SyntheticSample(
            text=sentence,
            sentiment_label="neutral",
            sentiment_score=0.0,
            logistics_intent=template[1],
            logistics_severity=template[2],
            is_logistics=True,
            confidence=0.9
        )
    
    def generate_general_sample(self) -> SyntheticSample:
        """Generate a general chat sample.
        
        Returns:
            SyntheticSample without logistics intent
        """
        subjects = self.SUBJECTS["person"] + self.SUBJECTS["group"]
        subject = random.choice(subjects)
        
        positive_phrases = [
            "ni fiti sana",
            "amepata chapaa",
            "anadunda proper",
            "poa kabisa"
        ]
        
        negative_phrases = [
            "amekudunda",
            "hana chapaa",
            "ni sapa",
            "amefeli"
        ]
        
        if random.random() > 0.5:
            phrase = random.choice(positive_phrases)
            sentiment = "positive"
            score = 0.7
        else:
            phrase = random.choice(negative_phrases)
            sentiment = "negative"
            score = -0.7
        
        sentence = f"{subject} {phrase}"
        
        return SyntheticSample(
            text=sentence,
            sentiment_label=sentiment,
            sentiment_score=score,
            logistics_intent="general",
            logistics_severity="none",
            is_logistics=False,
            confidence=0.6
        )
    
    def generate_dataset(
        self,
        total_samples: int = 500,
        logistics_ratio: float = 0.3,
        contextual_ratio: float = 0.3
    ) -> List[SyntheticSample]:
        """Generate a complete synthetic dataset.
        
        Args:
            total_samples: Total number of samples to generate
            logistics_ratio: Proportion of logistics samples (0-1)
            contextual_ratio: Proportion of contextual sentiment samples (0-1)
            
        Returns:
            List of SyntheticSample objects
        """
        logistics_count = int(total_samples * logistics_ratio)
        contextual_count = int(total_samples * contextual_ratio)
        general_count = total_samples - logistics_count - contextual_count
        
        dataset = []
        
        # Generate logistics samples
        for _ in range(logistics_count):
            dataset.append(self.generate_logistics_sample())
        
        # Generate contextual sentiment samples
        for _ in range(contextual_count):
            dataset.append(self.generate_contextual_sample())
        
        # Generate general samples
        for _ in range(general_count):
            dataset.append(self.generate_general_sample())
        
        # Shuffle dataset
        random.shuffle(dataset)
        
        return dataset
    
    def save_to_jsonl(
        self,
        dataset: List[SyntheticSample],
        output_path: str = "data/processed/golden_dataset.jsonl"
    ) -> Path:
        """Save dataset to JSONL format.
        
        Args:
            dataset: List of SyntheticSample objects
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in dataset:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        
        print(f"Saved {len(dataset)} samples to {output_file}")
        return output_file


def main():
    """Generate synthetic dataset."""
    generator = ShengSyntheticGenerator()
    
    # Generate dataset
    dataset = generator.generate_dataset(
        total_samples=500,
        logistics_ratio=0.3,
        contextual_ratio=0.3
    )
    
    # Save to JSONL
    output_path = generator.save_to_jsonl(dataset)
    
    # Print statistics
    logistics_count = sum(1 for s in dataset if s.is_logistics)
    positive_count = sum(1 for s in dataset if s.sentiment_label == "positive")
    negative_count = sum(1 for s in dataset if s.sentiment_label == "negative")
    neutral_count = sum(1 for s in dataset if s.sentiment_label == "neutral")
    
    print(f"\nDataset Statistics:")
    print(f"  Total samples: {len(dataset)}")
    print(f"  Logistics samples: {logistics_count} ({logistics_count/len(dataset)*100:.1f}%)")
    print(f"  Positive sentiment: {positive_count} ({positive_count/len(dataset)*100:.1f}%)")
    print(f"  Negative sentiment: {negative_count} ({negative_count/len(dataset)*100:.1f}%)")
    print(f"  Neutral sentiment: {neutral_count} ({neutral_count/len(dataset)*100:.1f}%)")


if __name__ == "__main__":
    main()
