"""Real-world data scraper for Nairobi traffic/logistics content.

This module creates realistic mock data representing actual Nairobi traffic
and logistics conversations for testing and validation.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

from .sheng_scraper import ShengPost


@dataclass
class RealWorldSample:
    """A labeled real-world sample for validation."""
    
    text: str
    true_sentiment: str
    true_logistics: bool
    true_intent: str
    source: str
    timestamp: str


class NairobiTrafficScraper:
    """Mock scraper for Nairobi traffic and logistics content.
    
    Generates realistic samples representing actual conversations
    about traffic, police, accidents, and route changes.
    """
    
    # Real Nairobi locations and landmarks
    NAIROBI_LOCATIONS = [
        "CBD", "Westlands", "Kilimani", "Karen", "Langata", "Kasarani",
        "Thika Road", "Mombasa Road", "Waiyaki Way", "Uhuru Highway",
        "Expressway", "Gigiri", "Runda", "Kikuyu", "Limuru"
    ]
    
    # Real traffic/logistics scenarios
    TRAFFIC_SCENARIOS = [
        {
            "text": "Jam imekali {location}, tumetuma saa tatu",
            "sentiment": "negative",
            "logistics": True,
            "intent": "traffic_report"
        },
        {
            "text": "Karao wako {location}, wanawakamata",
            "sentiment": "negative", 
            "logistics": True,
            "intent": "police_report"
        },
        {
            "text": "Mreki imetoka {location}, mat imejaa",
            "sentiment": "negative",
            "logistics": True,
            "intent": "obstacle_report"
        },
        {
            "text": "Stage ya {location} imejaa, tumia shorcut",
            "sentiment": "neutral",
            "logistics": True,
            "intent": "route_suggestion"
        },
        {
            "text": "Avoid panya route karibu {location}",
            "sentiment": "neutral",
            "logistics": True,
            "intent": "unofficial_route"
        },
        {
            "text": "U-turn at {location} imefungwa",
            "sentiment": "negative",
            "logistics": True,
            "intent": "route_change"
        },
        {
            "text": "Boda imekudunda {location}",
            "sentiment": "negative",
            "logistics": True,
            "intent": "obstacle_report"
        },
        {
            "text": "Traffic imetulia {location}",
            "sentiment": "positive",
            "logistics": True,
            "intent": "traffic_report"
        },
        {
            "text": "Road imefungwa {location}",
            "sentiment": "negative",
            "logistics": True,
            "intent": "obstacle_report"
        },
        {
            "text": "Flyover imejaa {location}",
            "sentiment": "negative",
            "logistics": True,
            "intent": "traffic_report"
        }
    ]
    
    # General conversation scenarios
    GENERAL_SCENARIOS = [
        {
            "text": "Buda niko sapa, nisaidie chapaa",
            "sentiment": "negative",
            "logistics": False,
            "intent": "general"
        },
        {
            "text": "Hii mbogi ni fiti sana",
            "sentiment": "positive",
            "logistics": False,
            "intent": "general"
        },
        {
            "text": "Leo tunadunda sherehe",
            "sentiment": "positive",
            "logistics": False,
            "intent": "general"
        },
        {
            "text": "Ame kudunda mtihani",
            "sentiment": "negative",
            "logistics": False,
            "intent": "general"
        },
        {
            "text": "Niko fiti poa",
            "sentiment": "neutral",
            "logistics": False,
            "intent": "general"
        },
        {
            "text": "Chapi hana chapaa",
            "sentiment": "negative",
            "logistics": False,
            "intent": "general"
        },
        {
            "text": "Msee amepata job",
            "sentiment": "positive",
            "logistics": False,
            "intent": "general"
        },
        {
            "text": "Noma hii kitu",
            "sentiment": "negative",
            "logistics": False,
            "intent": "general"
        },
        {
            "text": "Fiti hii dem",
            "sentiment": "positive",
            "logistics": False,
            "intent": "general"
        },
        {
            "text": "Sijui kufanya",
            "sentiment": "negative",
            "logistics": False,
            "intent": "general"
        }
    ]
    
    def __init__(self):
        """Initialize the scraper."""
        self.scenarios = self.TRAFFIC_SCENARIOS + self.GENERAL_SCENARIOS
    
    def generate_sample(self, scenario: Dict[str, Any]) -> RealWorldSample:
        """Generate a single sample from a scenario.
        
        Args:
            scenario: Scenario template
            
        Returns:
            RealWorldSample with filled template
        """
        location = random.choice(self.NAIROBI_LOCATIONS)
        text = scenario["text"].format(location=location)
        
        # Add some variation
        if random.random() > 0.5:
            text = f"{text} sana"
        
        # Generate realistic timestamp (last 24 hours)
        hours_ago = random.randint(0, 24)
        timestamp = (datetime.now() - timedelta(hours=hours_ago)).isoformat()
        
        return RealWorldSample(
            text=text,
            true_sentiment=scenario["sentiment"],
            true_logistics=scenario["logistics"],
            true_intent=scenario["intent"],
            source="nairobi_traffic_mock",
            timestamp=timestamp
        )
    
    def scrape_real_world_data(self, count: int = 200) -> List[RealWorldSample]:
        """Generate real-world samples.
        
        Args:
            count: Number of samples to generate
            
        Returns:
            List of RealWorldSample objects
        """
        samples = []
        
        # 70% traffic/logistics, 30% general
        traffic_count = int(count * 0.7)
        general_count = count - traffic_count
        
        # Generate traffic samples
        traffic_scenarios = [s for s in self.TRAFFIC_SCENARIOS if s["logistics"]]
        for _ in range(traffic_count):
            scenario = random.choice(traffic_scenarios)
            samples.append(self.generate_sample(scenario))
        
        # Generate general samples
        for _ in range(general_count):
            scenario = random.choice(self.GENERAL_SCENARIOS)
            samples.append(self.generate_sample(scenario))
        
        # Shuffle samples
        random.shuffle(samples)
        
        return samples
    
    def save_to_jsonl(
        self,
        samples: List[RealWorldSample],
        output_path: str = "data/raw/real_world_samples.jsonl"
    ) -> Path:
        """Save samples to JSONL format.
        
        Args:
            samples: List of RealWorldSample objects
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in samples:
                f.write(json.dumps(asdict(sample), ensure_ascii=False) + '\n')
        
        print(f"Saved {len(samples)} real-world samples to {output_file}")
        return output_file


def main():
    """Generate real-world samples."""
    scraper = NairobiTrafficScraper()
    
    # Generate samples
    samples = scraper.scrape_real_world_data(count=200)
    
    # Save to JSONL
    output_path = scraper.save_to_jsonl(samples)
    
    # Print statistics
    traffic_count = sum(1 for s in samples if s.true_logistics)
    positive_count = sum(1 for s in samples if s.true_sentiment == "positive")
    negative_count = sum(1 for s in samples if s.true_sentiment == "negative")
    neutral_count = sum(1 for s in samples if s.true_sentiment == "neutral")
    
    print(f"\nReal-World Dataset Statistics:")
    print(f"  Total samples: {len(samples)}")
    print(f"  Traffic/Logistics: {traffic_count} ({traffic_count/len(samples)*100:.1f}%)")
    print(f"  Positive sentiment: {positive_count} ({positive_count/len(samples)*100:.1f}%)")
    print(f"  Negative sentiment: {negative_count} ({negative_count/len(samples)*100:.1f}%)")
    print(f"  Neutral sentiment: {neutral_count} ({neutral_count/len(samples)*100:.1f}%)")


if __name__ == "__main__":
    main()
