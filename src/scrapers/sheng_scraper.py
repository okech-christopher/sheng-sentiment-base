"""ShengScraper: Rate-limited data collection for Sheng content.

This module provides robust scraping capabilities for X (Twitter) and TikTok
content targeting Nairobi-based Sheng language usage.
"""

import json
import time
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional, Dict, List, Any
from dataclasses import dataclass, asdict

import requests
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ShengPost:
    """Data structure for a Sheng language post."""
    
    id: str
    platform: str
    text: str
    author: str
    timestamp: str
    location_tag: Optional[str] = None
    engagement_score: int = 0
    hashtags: List[str] = None
    raw_metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.hashtags is None:
            self.hashtags = []
        if self.raw_metadata is None:
            self.raw_metadata = {}


class RateLimiter:
    """Token bucket rate limiter for polite scraping."""
    
    def __init__(self, requests_per_minute: int = 30):
        self.min_delay = 60.0 / requests_per_minute
        self.last_request = 0.0
    
    def wait(self) -> None:
        """Wait appropriate time between requests."""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_delay:
            sleep_time = self.min_delay - elapsed + random.uniform(0.5, 2.0)
            time.sleep(sleep_time)
        self.last_request = time.time()


class ShengScraper:
    """Primary scraper for Sheng language content.
    
    Targets Nairobi-centric social media content with Sheng hashtags
    and code-switching patterns.
    
    Attributes:
        output_dir: Directory to store scraped data
        rate_limiter: Rate limiting controller
        user_agent: Rotating user agent generator
    """
    
    # High-value Sheng hashtags for Nairobi
    TARGET_HASHTAGS = [
        "sheng", "nairobian", "mbogigenje", "shengnative",
        "254", "nairobilife", "shengword", "shengmemes",
        "kenyantrends", "shengke", "shengculture"
    ]
    
    # Nairobi location indicators
    LOCATION_INDICATORS = [
        "nairobi", "mombasa", "kisumu", "nakuru", "eldoret",
        "rongai", "karen", "westlands", "eastleigh", "gikomba",
        "kibera", "mathare", "kawangware", "umoja", "buruburu"
    ]
    
    def __init__(
        self,
        output_dir: str = "data/raw",
        requests_per_minute: int = 20,
        platform: str = "x"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.user_agent = UserAgent()
        self.platform = platform.lower()
        self.session = requests.Session()
        self.collected_posts: List[ShengPost] = []
        
    def _get_headers(self) -> Dict[str, str]:
        """Generate request headers with rotating user agent."""
        return {
            "User-Agent": self.user_agent.random,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from post text."""
        import re
        return re.findall(r'#(\w+)', text.lower())
    
    def _contains_sheng_indicators(self, text: str) -> bool:
        """Check if text contains Sheng language indicators."""
        text_lower = text.lower()
        
        # Common Sheng terms (this will be expanded)
        sheng_terms = [
            "mbogi", "genje", "sheng", "rongai", "ronga",
            "chapaa", "mulla", "do", "msee", "mjango",
            "budaa", "mdosi", "madhee", "rieng", "dunda"
        ]
        
        return any(term in text_lower for term in sheng_terms)
    
    def _mock_scrape_x(self, hashtag: str, count: int = 100) -> Iterator[ShengPost]:
        """Mock scraper for X (Twitter) - production uses official API."""
        # This simulates API response structure
        mock_posts = [
            {
                "id": f"x_{hashtag}_{i}",
                "text": f"Sample {hashtag} content with Sheng slang #sheng #nairobi",
                "author": f"user_{random.randint(1000, 9999)}",
                "timestamp": datetime.now().isoformat(),
                "engagement": random.randint(0, 500)
            }
            for i in range(count)
        ]
        
        for post in mock_posts:
            self.rate_limiter.wait()
            
            # Simulate API delay
            time.sleep(random.uniform(0.1, 0.3))
            
            yield ShengPost(
                id=post["id"],
                platform="x",
                text=post["text"],
                author=post["author"],
                timestamp=post["timestamp"],
                engagement_score=post["engagement"],
                hashtags=self._extract_hashtags(post["text"]),
                raw_metadata=post
            )
    
    def scrape_by_hashtag(
        self,
        hashtag: str,
        count: int = 100,
        save_immediately: bool = True
    ) -> List[ShengPost]:
        """Scrape posts by hashtag.
        
        Args:
            hashtag: Target hashtag (without #)
            count: Number of posts to collect
            save_immediately: Save to disk after collection
            
        Returns:
            List of collected ShengPost objects
        """
        logger.info(f"Scraping {count} posts for hashtag: #{hashtag}")
        
        posts = []
        
        if self.platform == "x":
            for post in self._mock_scrape_x(hashtag, count):
                posts.append(post)
                self.collected_posts.append(post)
                
                if len(posts) % 10 == 0:
                    logger.info(f"Collected {len(posts)}/{count} posts")
        
        if save_immediately:
            self.save_posts(posts, f"{self.platform}_{hashtag}_{datetime.now():%Y%m%d_%H%M%S}.jsonl")
        
        logger.info(f"Completed: {len(posts)} posts collected for #{hashtag}")
        return posts
    
    def scrape_multiple_hashtags(
        self,
        hashtags: Optional[List[str]] = None,
        count_per_tag: int = 50
    ) -> List[ShengPost]:
        """Scrape multiple hashtags efficiently."""
        if hashtags is None:
            hashtags = self.TARGET_HASHTAGS
        
        all_posts = []
        for hashtag in hashtags:
            posts = self.scrape_by_hashtag(hashtag, count_per_tag)
            all_posts.extend(posts)
            logger.info(f"Total collected: {len(all_posts)} posts")
        
        return all_posts
    
    def save_posts(
        self,
        posts: List[ShengPost],
        filename: Optional[str] = None
    ) -> Path:
        """Save posts to JSONL file.
        
        Args:
            posts: List of posts to save
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"sheng_data_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for post in posts:
                f.write(json.dumps(asdict(post), ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(posts)} posts to {filepath}")
        return filepath
    
    def get_stats(self) -> Dict[str, Any]:
        """Return scraping statistics."""
        return {
            "total_collected": len(self.collected_posts),
            "platform": self.platform,
            "unique_authors": len(set(p.author for p in self.collected_posts)),
            "hashtag_coverage": len(set(
                tag for p in self.collected_posts for tag in p.hashtags
            ))
        }


if __name__ == "__main__":
    # Quick test
    scraper = ShengScraper()
    posts = scraper.scrape_by_hashtag("sheng", count=10)
    print(f"Stats: {scraper.get_stats()}")
