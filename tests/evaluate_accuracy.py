"""Accuracy evaluation suite for Sheng-Native API.

This script evaluates the accuracy, precision, and recall of the
sentiment analysis and logistics intent detection on a golden dataset.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tokenizers.sheng_tokenizer import ShengTokenizer
from src.tokenizers.intent_engine import ShengIntentEngine
from src.engine.logic import ShengLogicRefiner


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for model performance."""
    
    sentiment_accuracy: float
    sentiment_precision: Dict[str, float]
    sentiment_recall: Dict[str, float]
    logistics_accuracy: float
    logistics_precision: float
    logistics_recall: float
    overall_accuracy: float


class AccuracyEvaluator:
    """Evaluate Sheng-Native API accuracy against golden dataset."""
    
    def __init__(self, tokenizer: ShengTokenizer = None, intent_engine: ShengIntentEngine = None, logic_refiner: ShengLogicRefiner = None):
        """Initialize the evaluator.
        
        Args:
            tokenizer: Optional ShengTokenizer instance
            intent_engine: Optional ShengIntentEngine instance
            logic_refiner: Optional ShengLogicRefiner instance
        """
        self.tokenizer = tokenizer or ShengTokenizer()
        self.intent_engine = intent_engine or ShengIntentEngine()
        self.logic_refiner = logic_refiner or ShengLogicRefiner()
    
    def load_golden_dataset(self, path: str = "data/processed/golden_dataset.jsonl") -> List[Dict[str, Any]]:
        """Load golden dataset from JSONL file.
        
        Args:
            path: Path to golden dataset file
            
        Returns:
            List of sample dictionaries
        """
        dataset_path = Path(path)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Golden dataset not found at {path}")
        
        dataset = []
        with open(dataset_path, 'r', encoding='utf-8') as f:
            for line in f:
                dataset.append(json.loads(line))
        
        print(f"Loaded {len(dataset)} samples from golden dataset")
        return dataset
    
    def evaluate_sample(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single sample against the API logic.
        
        Args:
            sample: Golden dataset sample
            
        Returns:
            Evaluation result with predictions and labels
        """
        text = sample["text"]
        
        # Tokenize
        result = self.tokenizer.tokenize(text)
        
        # Apply logic refinements
        refinement_result = self.logic_refiner.refine_sentiment(
            text, 
            result.sentiment_label, 
            result.sentiment_score, 
            result.slang_terms
        )
        
        # Update sentiment if refined
        predicted_sentiment = refinement_result.refined_sentiment if refinement_result.sentiment_adjusted else result.sentiment_label
        
        # Run intent engine
        intent_result = self.intent_engine.detect_intent(text, result.slang_terms)
        
        return {
            "text": text,
            "predicted_sentiment": predicted_sentiment,
            "predicted_logistics": intent_result.is_logistics,
            "predicted_intent": intent_result.intent_type,
            "true_sentiment": sample["sentiment_label"],
            "true_logistics": sample["is_logistics"],
            "true_intent": sample["logistics_intent"],
            "sentiment_correct": predicted_sentiment == sample["sentiment_label"],
            "logistics_correct": intent_result.is_logistics == sample["is_logistics"]
        }
    
    def calculate_metrics(self, results: List[Dict[str, Any]]) -> EvaluationMetrics:
        """Calculate evaluation metrics.
        
        Args:
            results: List of evaluation results
            
        Returns:
            EvaluationMetrics object
        """
        total = len(results)
        
        # Sentiment metrics
        sentiment_correct = sum(1 for r in results if r["sentiment_correct"])
        sentiment_accuracy = sentiment_correct / total if total > 0 else 0.0
        
        # Per-class sentiment precision/recall
        sentiment_classes = ["positive", "negative", "neutral"]
        sentiment_precision = {}
        sentiment_recall = {}
        
        for cls in sentiment_classes:
            true_positives = sum(
                1 for r in results 
                if r["predicted_sentiment"] == cls and r["true_sentiment"] == cls
            )
            predicted_positives = sum(
                1 for r in results 
                if r["predicted_sentiment"] == cls
            )
            actual_positives = sum(
                1 for r in results 
                if r["true_sentiment"] == cls
            )
            
            sentiment_precision[cls] = (
                true_positives / predicted_positives if predicted_positives > 0 else 0.0
            )
            sentiment_recall[cls] = (
                true_positives / actual_positives if actual_positives > 0 else 0.0
            )
        
        # Logistics metrics
        logistics_correct = sum(1 for r in results if r["logistics_correct"])
        logistics_accuracy = logistics_correct / total if total > 0 else 0.0
        
        # Logistics precision/recall
        logistics_true_positives = sum(
            1 for r in results 
            if r["predicted_logistics"] and r["true_logistics"]
        )
        logistics_predicted_positives = sum(1 for r in results if r["predicted_logistics"])
        logistics_actual_positives = sum(1 for r in results if r["true_logistics"])
        
        logistics_precision = (
            logistics_true_positives / logistics_predicted_positives 
            if logistics_predicted_positives > 0 else 0.0
        )
        logistics_recall = (
            logistics_true_positives / logistics_actual_positives 
            if logistics_actual_positives > 0 else 0.0
        )
        
        # Overall accuracy (both sentiment and logistics must be correct)
        overall_correct = sum(
            1 for r in results 
            if r["sentiment_correct"] and r["logistics_correct"]
        )
        overall_accuracy = overall_correct / total if total > 0 else 0.0
        
        return EvaluationMetrics(
            sentiment_accuracy=sentiment_accuracy,
            sentiment_precision=sentiment_precision,
            sentiment_recall=sentiment_recall,
            logistics_accuracy=logistics_accuracy,
            logistics_precision=logistics_precision,
            logistics_recall=logistics_recall,
            overall_accuracy=overall_accuracy
        )
    
    def evaluate(self, dataset_path: str = "data/processed/golden_dataset.jsonl") -> EvaluationMetrics:
        """Run full evaluation pipeline.
        
        Args:
            dataset_path: Path to golden dataset
            
        Returns:
            EvaluationMetrics object
        """
        # Load dataset
        dataset = self.load_golden_dataset(dataset_path)
        
        # Evaluate each sample
        results = []
        for sample in dataset:
            result = self.evaluate_sample(sample)
            results.append(result)
        
        # Calculate metrics
        metrics = self.calculate_metrics(results)
        
        return metrics
    
    def print_report(self, metrics: EvaluationMetrics):
        """Print evaluation report.
        
        Args:
            metrics: EvaluationMetrics object
        """
        print("\n" + "="*60)
        print("SHENG-NATIVE API ACCURACY EVALUATION")
        print("="*60)
        
        print(f"\nSentiment Analysis:")
        print(f"  Accuracy: {metrics.sentiment_accuracy:.4f} ({metrics.sentiment_accuracy*100:.2f}%)")
        print(f"  Precision:")
        for cls, score in metrics.sentiment_precision.items():
            print(f"    {cls}: {score:.4f} ({score*100:.2f}%)")
        print(f"  Recall:")
        for cls, score in metrics.sentiment_recall.items():
            print(f"    {cls}: {score:.4f} ({score*100:.2f}%)")
        
        print(f"\nLogistics Intent Detection:")
        print(f"  Accuracy: {metrics.logistics_accuracy:.4f} ({metrics.logistics_accuracy*100:.2f}%)")
        print(f"  Precision: {metrics.logistics_precision:.4f} ({metrics.logistics_precision*100:.2f}%)")
        print(f"  Recall: {metrics.logistics_recall:.4f} ({metrics.logistics_recall*100:.2f}%)")
        
        print(f"\nOverall Performance:")
        print(f"  Combined Accuracy: {metrics.overall_accuracy:.4f} ({metrics.overall_accuracy*100:.2f}%)")
        
        # Target check
        target = 0.91
        if metrics.overall_accuracy >= target:
            print(f"\n✅ TARGET MET: {metrics.overall_accuracy*100:.2f}% >= {target*100:.2f}%")
        else:
            print(f"\n⚠️  TARGET NOT MET: {metrics.overall_accuracy*100:.2f}% < {target*100:.2f}%")
            print(f"   Gap: {(target - metrics.overall_accuracy)*100:.2f}%")
        
        print("="*60 + "\n")


def main():
    """Run evaluation."""
    evaluator = AccuracyEvaluator()
    
    # Evaluate
    metrics = evaluator.evaluate()
    
    # Print report
    evaluator.print_report(metrics)


if __name__ == "__main__":
    main()
