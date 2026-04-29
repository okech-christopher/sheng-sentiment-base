"""Export training data for LLM fine-tuning.

This utility converts processed Sheng data into training-ready formats
compatible with Llama-3, Mistral, and other transformer models.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..tokenizers.sheng_tokenizer import ShengTokenizer, TokenizedOutput

logger = logging.getLogger(__name__)


class TrainingDataExporter:
    """Export processed Sheng data for LLM fine-tuning.
    
    Supports multiple output formats:
    - JSONL: Standard for HuggingFace datasets
    - JSON: Complete dataset with metadata
    - CSV: Tabular format for analysis
    """
    
    def __init__(
        self,
        output_dir: str = "data/processed",
        tokenizer: Optional[ShengTokenizer] = None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tokenizer = tokenizer or ShengTokenizer()
        
        logger.info(f"TrainingDataExporter initialized: {self.output_dir}")
    
    def export_to_jsonl(
        self,
        texts: List[str],
        output_file: str = "sheng_training_data.jsonl",
        include_metadata: bool = True
    ) -> Path:
        """Export texts to JSONL format for LLM training.
        
        Args:
            texts: List of raw text strings
            output_file: Output filename
            include_metadata: Include sentiment and slang metadata
            
        Returns:
            Path to exported file
        """
        filepath = self.output_dir / output_file
        count = 0
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for text in texts:
                # Tokenize to get analysis
                result = self.tokenizer.tokenize(text)
                
                if include_metadata:
                    record = {
                        "text": result.normalized_text,
                        "metadata": {
                            "sentiment": result.sentiment_label,
                            "sentiment_score": result.sentiment_score,
                            "slang_terms": result.slang_terms,
                            "code_switches": result.code_switches,
                            "original_text": result.original_text,
                            "token_count": result.metadata.get("token_count", 0)
                        }
                    }
                else:
                    record = {"text": result.normalized_text}
                
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
                count += 1
        
        logger.info(f"Exported {count} records to {filepath}")
        return filepath
    
    def export_to_json(
        self,
        texts: List[str],
        output_file: str = "sheng_dataset.json"
    ) -> Path:
        """Export complete dataset to JSON format.
        
        Args:
            texts: List of raw text strings
            output_file: Output filename
            
        Returns:
            Path to exported file
        """
        filepath = self.output_dir / output_file
        
        dataset = {
            "metadata": {
                "name": "Sheng-Native Training Dataset",
                "version": "0.2",
                "created": datetime.now().isoformat(),
                "total_samples": len(texts)
            },
            "data": []
        }
        
        for text in texts:
            result = self.tokenizer.tokenize(text)
            dataset["data"].append({
                "id": f"sample_{len(dataset['data'])}",
                "original_text": result.original_text,
                "normalized_text": result.normalized_text,
                "tokens": result.tokens,
                "slang_terms": result.slang_terms,
                "code_switches": result.code_switches,
                "sentiment": {
                    "label": result.sentiment_label,
                    "score": result.sentiment_score
                },
                "metadata": result.metadata
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(texts)} samples to {filepath}")
        return filepath
    
    def export_for_instruction_tuning(
        self,
        texts: List[str],
        output_file: str = "sheng_instruction_tuning.jsonl"
    ) -> Path:
        """Export in instruction-tuning format for Llama-3/Mistral.
        
        Format:
        {
            "instruction": "Analyze the sentiment of this Sheng text",
            "input": "Hii mbogi ni fiti",
            "output": "positive"
        }
        
        Args:
            texts: List of raw text strings
            output_file: Output filename
            
        Returns:
            Path to exported file
        """
        filepath = self.output_dir / output_file
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for text in texts:
                result = self.tokenizer.tokenize(text)
                
                record = {
                    "instruction": "Analyze the sentiment of this Sheng text",
                    "input": result.original_text,
                    "output": result.sentiment_label
                }
                
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        logger.info(f"Exported {len(texts)} instruction-tuning samples to {filepath}")
        return filepath
    
    def export_sentiment_dataset(
        self,
        texts: List[str],
        output_file: str = "sheng_sentiment_classification.jsonl"
    ) -> Path:
        """Export for sentiment classification fine-tuning.
        
        Format:
        {
            "text": "normalized text",
            "label": 0  # 0=negative, 1=neutral, 2=positive
        }
        
        Args:
            texts: List of raw text strings
            output_file: Output filename
            
        Returns:
            Path to exported file
        """
        filepath = self.output_dir / output_file
        
        label_map = {"negative": 0, "neutral": 1, "positive": 2}
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for text in texts:
                result = self.tokenizer.tokenize(text)
                
                record = {
                    "text": result.normalized_text,
                    "label": label_map.get(result.sentiment_label, 1)
                }
                
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        logger.info(f"Exported {len(texts)} sentiment samples to {filepath}")
        return filepath
    
    def export_slang_detection_dataset(
        self,
        texts: List[str],
        output_file: str = "sheng_slang_detection.jsonl"
    ) -> Path:
        """Export for slang term detection task.
        
        Format:
        {
            "text": "normalized text",
            "slang_terms": ["buda", "chapaa"]
        }
        
        Args:
            texts: List of raw text strings
            output_file: Output filename
            
        Returns:
            Path to exported file
        """
        filepath = self.output_dir / output_file
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for text in texts:
                result = self.tokenizer.tokenize(text)
                
                record = {
                    "text": result.normalized_text,
                    "slang_terms": result.slang_terms
                }
                
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        logger.info(f"Exported {len(texts)} slang detection samples to {filepath}")
        return filepath
    
    def create_train_test_split(
        self,
        texts: List[str],
        test_ratio: float = 0.2,
        random_seed: int = 42
    ) -> tuple[List[str], List[str]]:
        """Split data into training and test sets.
        
        Args:
            texts: List of raw text strings
            test_ratio: Proportion for test set
            random_seed: Random seed for reproducibility
            
        Returns:
            Tuple of (train_texts, test_texts)
        """
        import random
        random.seed(random_seed)
        
        shuffled = texts.copy()
        random.shuffle(shuffled)
        
        split_idx = int(len(shuffled) * (1 - test_ratio))
        train_texts = shuffled[:split_idx]
        test_texts = shuffled[split_idx:]
        
        logger.info(f"Split: {len(train_texts)} train, {len(test_texts)} test")
        return train_texts, test_texts


def main():
    """Example usage of TrainingDataExporter."""
    exporter = TrainingDataExporter()
    
    # Sample texts
    sample_texts = [
        "Hii mbogi ni fiti sana, wanadunda proper!",
        "Buda hana chapaa, amekudunda mtihani",
        "Kudunda sherehe, mzinga full!",
        "Niko sapa, hata chapaa sina",
        "Nairobi life ni noma tu"
    ]
    
    # Export in multiple formats
    exporter.export_to_jsonl(sample_texts, "demo_training.jsonl")
    exporter.export_to_json(sample_texts, "demo_dataset.json")
    exporter.export_for_instruction_tuning(sample_texts, "demo_instruction.jsonl")
    exporter.export_sentiment_dataset(sample_texts, "demo_sentiment.jsonl")
    exporter.export_slang_detection_dataset(sample_texts, "demo_slang.jsonl")
    
    print("Demo exports complete. Check data/processed/")


if __name__ == "__main__":
    main()
