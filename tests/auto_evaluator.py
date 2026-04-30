"""Auto-evaluator for Sheng-Native API.

This script automatically runs accuracy evaluation after each commit
and updates the repository with the latest metrics.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.evaluate_accuracy import AccuracyEvaluator


class AutoEvaluator:
    """Automatic evaluation runner for CI/CD integration."""
    
    def __init__(self):
        """Initialize the auto-evaluator."""
        self.evaluator = AccuracyEvaluator()
        self.metrics_file = Path("data/metrics/latest_evaluation.json")
        self.github_env_file = Path(".github/workflows/auto-evaluate.yml")
    
    def run_evaluation(self) -> Dict[str, Any]:
        """Run full evaluation pipeline.
        
        Returns:
            Dictionary of evaluation metrics
        """
        print("Running automatic evaluation...")
        
        # Run evaluation
        metrics = self.evaluator.evaluate()
        
        # Convert to serializable format
        metrics_dict = {
            "timestamp": "2026-05-01T00:00:00",
            "sentiment_accuracy": metrics.sentiment_accuracy,
            "sentiment_precision": metrics.sentiment_precision,
            "sentiment_recall": metrics.sentiment_recall,
            "logistics_accuracy": metrics.logistics_accuracy,
            "logistics_precision": metrics.logistics_precision,
            "logistics_recall": metrics.logistics_recall,
            "overall_accuracy": metrics.overall_accuracy,
            "target_met": metrics.overall_accuracy >= 0.91
        }
        
        # Save metrics
        self.save_metrics(metrics_dict)
        
        return metrics_dict
    
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
    
    # Check if this is a CI run
    if "CI" in sys.environ:
        metrics = evaluator.run_evaluation()
        evaluator.update_github_status(metrics)
    else:
        # Local run with change detection
        metrics = evaluator.run_if_needed()
        if metrics:
            print(f"Evaluation complete: {metrics['overall_accuracy']:.4f} overall accuracy")


if __name__ == "__main__":
    main()
