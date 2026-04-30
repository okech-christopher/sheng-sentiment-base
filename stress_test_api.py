"""API stress test for Sheng-Native service.

Tests API performance under load to ensure it can handle
10 requests per second target for production use.
"""

import time
import requests
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import statistics


class APIStressTest:
    """Stress test for Sheng-Native API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize stress test.
        
        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url
        self.results = []
    
    def single_request(self, text: str) -> Dict[str, Any]:
        """Make a single API request.
        
        Args:
            text: Text to analyze
            
        Returns:
            Response with timing data
        """
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/analyze",
                json={
                    "text": text,
                    "include_logistics": True,
                    "include_code_switches": True
                },
                timeout=10
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "duration": duration,
                    "status_code": response.status_code,
                    "text": text
                }
            else:
                return {
                    "success": False,
                    "duration": duration,
                    "status_code": response.status_code,
                    "error": response.text,
                    "text": text
                }
                
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "duration": end_time - start_time,
                "error": str(e),
                "text": text
            }
    
    def health_check(self) -> bool:
        """Check if API is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def run_stress_test(
        self,
        requests_per_second: int = 10,
        duration_seconds: int = 30,
        concurrent_workers: int = 20
    ) -> Dict[str, Any]:
        """Run stress test.
        
        Args:
            requests_per_second: Target RPS
            duration_seconds: Test duration
            concurrent_workers: Number of concurrent workers
            
        Returns:
            Test results summary
        """
        print(f"Starting stress test: {requests_per_second} RPS for {duration_seconds} seconds")
        print(f"Concurrent workers: {concurrent_workers}")
        
        # Test data
        test_texts = [
            "Jam imekali CBD, tumetuma saa tatu",
            "Karao wako Westlands, wanawakamata",
            "Mreki imetoka Thika Road, mat imejaa",
            "Buda niko sapa, nisaidie chapaa",
            "Hii mbogi ni fiti sana",
            "Leo tunadunda sherehe",
            "Ame kudunda mtihani",
            "Niko fiti poa",
            "Avoid panya route karibu Gigiri",
            "Stage ya Karen imejaa, tumia shorcut"
        ]
        
        # Calculate total requests
        total_requests = requests_per_second * duration_seconds
        
        # Run stress test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            futures = []
            
            for i in range(total_requests):
                # Calculate delay to maintain RPS
                delay = i / requests_per_second
                text = test_texts[i % len(test_texts)]
                
                future = executor.submit(self._delayed_request, delay, start_time, text)
                futures.append(future)
            
            # Collect results
            results = []
            for future in futures:
                result = future.result()
                results.append(result)
        
        # Calculate metrics
        end_time = time.time()
        actual_duration = end_time - start_time
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        if successful:
            durations = [r["duration"] for r in successful]
            avg_response_time = statistics.mean(durations)
            min_response_time = min(durations)
            max_response_time = max(durations)
            median_response_time = statistics.median(durations)
            p95_response_time = statistics.quantiles(durations, n=20)[18] if len(durations) > 20 else max(durations)
        else:
            avg_response_time = min_response_time = max_response_time = median_response_time = p95_response_time = 0
        
        actual_rps = len(successful) / actual_duration if actual_duration > 0 else 0
        success_rate = len(successful) / len(results) if results else 0
        
        summary = {
            "total_requests": total_requests,
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": success_rate,
            "actual_duration": actual_duration,
            "target_rps": requests_per_second,
            "actual_rps": actual_rps,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "median_response_time": median_response_time,
            "p95_response_time": p95_response_time,
            "meets_target": success_rate >= 0.95 and actual_rps >= requests_per_second * 0.9
        }
        
        return summary
    
    def _delayed_request(self, delay: float, start_time: float, text: str) -> Dict[str, Any]:
        """Execute request with delay.
        
        Args:
            delay: Delay in seconds
            start_time: Test start time
            text: Text to analyze
            
        Returns:
            Request result
        """
        # Wait until it's time to make the request
        current_time = time.time()
        elapsed = current_time - start_time
        
        if elapsed < delay:
            time.sleep(delay - elapsed)
        
        return self.single_request(text)
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary.
        
        Args:
            summary: Test results summary
        """
        print("\n" + "="*60)
        print("SHENG-NATIVE API STRESS TEST RESULTS")
        print("="*60)
        
        print(f"\nRequest Volume:")
        print(f"  Total requests: {summary['total_requests']}")
        print(f"  Successful: {summary['successful_requests']}")
        print(f"  Failed: {summary['failed_requests']}")
        print(f"  Success rate: {summary['success_rate']:.2%}")
        
        print(f"\nPerformance:")
        print(f"  Target RPS: {summary['target_rps']}")
        print(f"  Actual RPS: {summary['actual_rps']:.2f}")
        print(f"  Test duration: {summary['actual_duration']:.2f}s")
        
        print(f"\nResponse Times:")
        print(f"  Average: {summary['avg_response_time']:.3f}s")
        print(f"  Median: {summary['median_response_time']:.3f}s")
        print(f"  Min: {summary['min_response_time']:.3f}s")
        print(f"  Max: {summary['max_response_time']:.3f}s")
        print(f"  95th percentile: {summary['p95_response_time']:.3f}s")
        
        if summary['meets_target']:
            print(f"\n✅ STRESS TEST PASSED")
            print(f"   Successfully handles {summary['target_rps']} RPS")
        else:
            print(f"\n⚠️  STRESS TEST FAILED")
            if summary['success_rate'] < 0.95:
                print(f"   Success rate too low: {summary['success_rate']:.2%} < 95%")
            if summary['actual_rps'] < summary['target_rps'] * 0.9:
                print(f"   RPS too low: {summary['actual_rps']:.2f} < {summary['target_rps'] * 0.9:.2f}")
        
        print("="*60 + "\n")


def main():
    """Run stress test."""
    tester = APIStressTest()
    
    # Check if API is running
    print("Checking API health...")
    if not tester.health_check():
        print("❌ API is not running. Please start the API first:")
        print("   python -m src.api.main")
        return
    
    print("✅ API is healthy")
    
    # Run stress test
    summary = tester.run_stress_test(
        requests_per_second=10,
        duration_seconds=30,
        concurrent_workers=20
    )
    
    # Print results
    tester.print_summary(summary)


if __name__ == "__main__":
    main()
