"""ShengPipeline: End-to-end data processing workflow.

Orchestrates the scraper and tokenizer to provide a complete
Sheng NLP data processing pipeline from collection to analysis.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from ..scrapers.sheng_scraper import ShengScraper, ShengPost
from ..tokenizers.sheng_tokenizer import ShengTokenizer, TokenizedOutput

logger = logging.getLogger(__name__)


class ShengPipeline:
    """End-to-end pipeline for Sheng NLP processing.
    
    Combines scraping and tokenization into a unified workflow
    for building Sheng language datasets.
    
    Attributes:
        scraper: ShengScraper instance for data collection
        tokenizer: ShengTokenizer instance for text processing
        processed_data: Accumulator for processed outputs
    """
    
    def __init__(
        self,
        output_dir: str = "data/processed",
        raw_dir: str = "data/raw",
        dictionary_path: Optional[str] = None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.scraper = ShengScraper(output_dir=raw_dir)
        self.tokenizer = ShengTokenizer(dictionary_path=dictionary_path)
        self.processed_data: List[Dict[str, Any]] = []
        
        logger.info("ShengPipeline initialized")
    
    def process_posts(
        self,
        posts: List[ShengPost],
        save_intermediate: bool = True
    ) -> List[TokenizedOutput]:
        """Process a list of scraped posts through tokenization.
        
        Args:
            posts: List of ShengPost objects from scraper
            save_intermediate: Save results to disk immediately
            
        Returns:
            List of TokenizedOutput with full analysis
        """
        results = []
        
        for post in posts:
            # Tokenize the post text
            tokenized = self.tokenizer.tokenize(post.text)
            
            # Combine with post metadata
            enriched = {
                "post_id": post.id,
                "platform": post.platform,
                "author": post.author,
                "timestamp": post.timestamp,
                "engagement_score": post.engagement_score,
                "hashtags": post.hashtags,
                "location_tag": post.location_tag,
                "tokenized": asdict(tokenized)
            }
            
            results.append(tokenized)
            self.processed_data.append(enriched)
        
        if save_intermediate:
            self._save_checkpoint()
        
        logger.info(f"Processed {len(posts)} posts")
        return results
    
    def scrape_and_process(
        self,
        hashtag: str,
        count: int = 100
    ) -> List[TokenizedOutput]:
        """One-step scrape and process for a hashtag.
        
        Args:
            hashtag: Target hashtag (without #)
            count: Number of posts to collect
            
        Returns:
            List of fully processed outputs
        """
        logger.info(f"Starting scrape-and-process for #{hashtag}")
        
        # Step 1: Scrape
        posts = self.scraper.scrape_by_hashtag(hashtag, count=count)
        
        # Step 2: Process
        results = self.process_posts(posts)
        
        # Step 3: Generate summary
        stats = self._generate_stats(results)
        logger.info(f"Pipeline complete. Stats: {stats}")
        
        return results
    
    def batch_process_hashtags(
        self,
        hashtags: List[str],
        count_per_tag: int = 50
    ) -> Dict[str, Any]:
        """Batch process multiple hashtags efficiently.
        
        Args:
            hashtags: List of hashtags to process
            count_per_tag: Posts to collect per hashtag
            
        Returns:
            Summary statistics for entire batch
        """
        batch_results = {}
        
        for hashtag in hashtags:
            results = self.scrape_and_process(hashtag, count=count_per_tag)
            batch_results[hashtag] = {
                "count": len(results),
                "avg_sentiment": sum(r.sentiment_score for r in results) / len(results) if results else 0,
                "slang_frequency": self.tokenizer.extract_slang_vocabulary([r.original_text for r in results])
            }
        
        # Save batch summary
        self._save_batch_report(batch_results)
        
        return batch_results
    
    def _generate_stats(self, results: List[TokenizedOutput]) -> Dict[str, Any]:
        """Generate processing statistics."""
        if not results:
            return {"error": "no_results"}
        
        total_slang = sum(len(r.slang_terms) for r in results)
        total_switches = sum(len(r.code_switches) for r in results)
        
        sentiment_dist = {"positive": 0, "negative": 0, "neutral": 0}
        for r in results:
            sentiment_dist[r.sentiment_label] += 1
        
        return {
            "total_processed": len(results),
            "avg_tokens_per_post": sum(len(r.tokens) for r in results) / len(results),
            "total_slang_detected": total_slang,
            "total_code_switches": total_switches,
            "sentiment_distribution": sentiment_dist,
            "avg_sentiment_score": sum(r.sentiment_score for r in results) / len(results)
        }
    
    def _save_checkpoint(self) -> None:
        """Save intermediate results to disk."""
        if not self.processed_data:
            return
        
        from datetime import datetime
        filename = f"pipeline_checkpoint_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in self.processed_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        logger.info(f"Checkpoint saved: {filepath}")
    
    def _save_batch_report(self, batch_results: Dict[str, Any]) -> None:
        """Save batch processing report."""
        from datetime import datetime
        filename = f"batch_report_{datetime.now():%Y%m%d_%H%M%S}.json"
        filepath = self.output_dir / filename
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "hashtags_processed": list(batch_results.keys()),
            "results": batch_results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Batch report saved: {filepath}")
    
    def export_to_training_format(
        self,
        output_file: str = "sheng_training_data.jsonl"
    ) -> Path:
        """Export processed data in LLM training format.
        
        Format compatible with fine-tuning frameworks.
        """
        if not self.processed_data:
            logger.warning("No data to export")
            return None
        
        filepath = self.output_dir / output_file
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in self.processed_data:
                training_record = {
                    "text": item["tokenized"]["normalized_text"],
                    "metadata": {
                        "sentiment": item["tokenized"]["sentiment_label"],
                        "sentiment_score": item["tokenized"]["sentiment_score"],
                        "slang_terms": item["tokenized"]["slang_terms"],
                        "code_switches": item["tokenized"]["code_switches"],
                        "original_text": item["tokenized"]["original_text"],
                        "platform": item["platform"],
                        "timestamp": item["timestamp"]
                    }
                }
                f.write(json.dumps(training_record, ensure_ascii=False) + '\n')
        
        logger.info(f"Training data exported: {filepath}")
        return filepath
    
    def get_corpus_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for the entire corpus."""
        if not self.processed_data:
            return {"error": "no_data"}
        
        all_texts = [item["tokenized"]["original_text"] for item in self.processed_data]
        all_slang = [item["tokenized"]["slang_terms"] for item in self.processed_data]
        
        # Flatten slang lists
        slang_freq = {}
        for slang_list in all_slang:
            for term in slang_list:
                slang_freq[term] = slang_freq.get(term, 0) + 1
        
        return {
            "total_posts": len(self.processed_data),
            "unique_slang_terms": len(slang_freq),
            "top_slang": dict(sorted(slang_freq.items(), key=lambda x: x[1], reverse=True)[:10]),
            "platform_distribution": self._count_by_key("platform"),
            "sentiment_distribution": self._count_sentiment()
        }
    
    def _count_by_key(self, key: str) -> Dict[str, int]:
        """Count occurrences by a metadata key."""
        counts = {}
        for item in self.processed_data:
            value = item.get(key, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def _count_sentiment(self) -> Dict[str, int]:
        """Count sentiment labels."""
        counts = {"positive": 0, "negative": 0, "neutral": 0}
        for item in self.processed_data:
            label = item["tokenized"].get("sentiment_label", "neutral")
            counts[label] = counts.get(label, 0) + 1
        return counts


if __name__ == "__main__":
    # Example usage
    pipeline = ShengPipeline()
    
    # Process a single hashtag
    results = pipeline.scrape_and_process("sheng", count=5)
    
    # Export for training
    pipeline.export_to_training_format()
    
    # Print stats
    print(pipeline.get_corpus_statistics())
