"""Auto-evaluator for Sheng-Native API.

This script automatically runs accuracy evaluation after each commit
and updates the repository with the latest metrics.
"""

import json
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.engine.pipeline import ShengInferencePipeline


class AutoEvaluator:
    """Automatic evaluation runner for CI/CD integration."""
    
    def __init__(self):
        """Initialize the auto-evaluator."""
        self.pipeline = ShengInferencePipeline()
        self.metrics_file = Path("data/metrics/latest_evaluation.json")
        self.github_env_file = Path(".github/workflows/auto-evaluate.yml")
    
    def run_evaluation(self, dataset_path: str = "data/processed/golden_dataset.jsonl") -> Dict[str, Any]:
        """Run full evaluation pipeline using ShengInferencePipeline.
        
        Args:
            dataset_path: Path to golden dataset
            
        Returns:
            Dictionary of evaluation metrics
        """
        print("Running automatic evaluation with ShengInferencePipeline...")
        
        # Load golden dataset
        samples = self._load_dataset(dataset_path)
        
        # Extract texts for batch processing
        texts = [sample["text"] for sample in samples]
        
        # Run pipeline prediction batch
        results = self.pipeline.batch_analyze(texts)
        
        # Calculate metrics
        metrics = self._calculate_metrics(samples, results)
        
        # Convert to serializable format
        metrics_dict = {
            "timestamp": "2026-05-01T00:00:00",
            "dataset": dataset_path,
            "total_samples": len(samples),
            "sentiment_accuracy": metrics["sentiment_accuracy"],
            "sentiment_precision": metrics["sentiment_precision"],
            "sentiment_recall": metrics["sentiment_recall"],
            "logistics_accuracy": metrics["logistics_accuracy"],
            "logistics_precision": metrics["logistics_precision"],
            "logistics_recall": metrics["logistics_recall"],
            "overall_accuracy": metrics["overall_accuracy"],
            "target_met": metrics["overall_accuracy"] >= 0.91
        }
        
        # Save metrics
        self.save_metrics(metrics_dict)
        
        return metrics_dict
    
    def _load_dataset(self, dataset_path: str) -> list:
        """Load golden dataset from JSONL file.
        
        Args:
            dataset_path: Path to dataset
            
        Returns:
            List of samples
        """
        samples = []
        with open(dataset_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    samples.append(json.loads(line))
        return samples
    
    def _calculate_metrics(self, samples: list, results: list) -> Dict[str, float]:
        """Calculate evaluation metrics from samples and results.
        
        Args:
            samples: Ground truth samples
            results: Pipeline predictions
            
        Returns:
            Dictionary of metrics
        """
        sentiment_correct = 0
        logistics_correct = 0
        total_samples = len(samples)
        
        sentiment_tp = sentiment_fp = sentiment_fn = 0
        logistics_tp = logistics_fp = logistics_fn = 0
        
        for sample, result in zip(samples, results):
            # Sentiment metrics
            if result.sentiment_label == sample["sentiment_label"]:
                sentiment_correct += 1
                if result.sentiment_label == "positive":
                    sentiment_tp += 1
                elif result.sentiment_label == "negative":
                    sentiment_fn += 1
            else:
                if result.sentiment_label == "positive":
                    sentiment_fp += 1
            
            # Logistics metrics
            predicted_logistics = result.is_logistics
            true_logistics = sample["is_logistics"]
            
            if predicted_logistics == true_logistics:
                logistics_correct += 1
                if predicted_logistics:
                    logistics_tp += 1
            else:
                if predicted_logistics:
                    logistics_fp += 1
                else:
                    logistics_fn += 1
        
        # Calculate metrics
        sentiment_accuracy = sentiment_correct / total_samples
        logistics_accuracy = logistics_correct / total_samples
        overall_accuracy = (sentiment_accuracy + logistics_accuracy) / 2
        
        # Precision and recall
        sentiment_precision = sentiment_tp / (sentiment_tp + sentiment_fp) if (sentiment_tp + sentiment_fp) > 0 else 0
        sentiment_recall = sentiment_tp / (sentiment_tp + sentiment_fn) if (sentiment_tp + sentiment_fn) > 0 else 0
        
        logistics_precision = logistics_tp / (logistics_tp + logistics_fp) if (logistics_tp + logistics_fp) > 0 else 0
        logistics_recall = logistics_tp / (logistics_tp + logistics_fn) if (logistics_tp + logistics_fn) > 0 else 0
        
        return {
            "sentiment_accuracy": sentiment_accuracy,
            "sentiment_precision": sentiment_precision,
            "sentiment_recall": sentiment_recall,
            "logistics_accuracy": logistics_accuracy,
            "logistics_precision": logistics_precision,
            "logistics_recall": logistics_recall,
            "overall_accuracy": overall_accuracy
        }
    
    def save_metrics(self, metrics: Dict[str, Any]):
        """Save evaluation metrics to file.
        
        Args:
            metrics: Metrics dictionary
        """
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print(f"Metrics saved to {self.metrics_file}")
    
    def update_github_status(self, metrics: Dict[str, Any]):
        """Update GitHub status based on evaluation results.
        
        Args:
            metrics: Evaluation metrics
        """
        # This would integrate with GitHub API or Actions
        if metrics["target_met"]:
            print("Target met! GitHub status: SUCCESS")
        else:
            gap = (0.91 - metrics["overall_accuracy"]) * 100
            print(f"Target not met. Gap: {gap:.1f}%")
    
    def create_github_workflow(self):
        """Create GitHub workflow for auto-evaluation."""
        workflow_content = """
name: Auto-Evaluation

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run evaluation
      run: python tests/auto_evaluator.py
    
    - name: Upload metrics
      uses: actions/upload-artifact@v3
      with:
        name: evaluation-metrics
        path: data/metrics/latest_evaluation.json
    
    - name: Check target
      run: |
        python -c "
        import json
        with open('data/metrics/latest_evaluation.json') as f:
            metrics = json.load(f)
        if metrics['overall_accuracy'] >= 0.91:
            print('Target met! Overall accuracy >= 91%')
        else:
            gap = (0.91 - metrics['overall_accuracy']) * 100
            print(f'Target not met. Gap: {gap:.1f}%')
            exit(1)
        "
"""
        
        self.github_env_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.github_env_file, 'w', encoding='utf-8') as f:
            f.write(workflow_content.strip())
        
        print(f"GitHub workflow created: {self.github_env_file}")
    
    def check_for_changes(self) -> bool:
        """Check if there are code changes since last evaluation.
        
        Returns:
            True if changes detected, False otherwise
        """
        try:
            # Get last commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return True  # Assume changes if git command fails
            
            current_hash = result.stdout.strip()
            
            # Check if metrics file exists and compare
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    metrics = json.load(f)
                
                last_hash = metrics.get("commit_hash")
                return last_hash != current_hash
            
            return True  # No previous metrics, run evaluation
            
        except Exception as e:
            print(f"Error checking for changes: {e}")
            return True
    
    def run_if_needed(self):
        """Run evaluation only if changes detected."""
        if self.check_for_changes():
            metrics = self.run_evaluation()
            self.update_github_status(metrics)
            return metrics
        else:
            print("No changes detected, skipping evaluation")
            return None


def main():
    """Main auto-evaluator entry point."""
    evaluator = AutoEvaluator()
    
    # Parse command line arguments
    dataset_path = "data/processed/golden_dataset.jsonl"
    if len(sys.argv) > 1:
        if "--dataset" in sys.argv:
            idx = sys.argv.index("--dataset")
            if idx + 1 < len(sys.argv):
                dataset_path = sys.argv[idx + 1]
    
    # Check if this is a CI run
    if "CI" in os.environ:
        metrics = evaluator.run_evaluation(dataset_path)
        evaluator.update_github_status(metrics)
    else:
        # Local run with dataset
        metrics = evaluator.run_evaluation(dataset_path)
        print(f"Evaluation complete: {metrics['overall_accuracy']:.4f} overall accuracy")
        
        # Check if target met
        if metrics['target_met']:
            print("SUCCESS: 0.91 target achieved!")
        else:
            gap = (0.91 - metrics['overall_accuracy']) * 100
            print(f"Target not met. Gap: {gap:.1f}%")


if __name__ == "__main__":
    main()
