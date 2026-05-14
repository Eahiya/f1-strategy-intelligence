"""
F1 Strategy Platform v5.0 - Stress Testing Suite
High-load testing with performance metrics and resource monitoring.
"""
import time
import statistics
import concurrent.futures
import requests
import psutil
import json
from datetime import datetime
from typing import Dict, List, Any
import argparse


class StressTestRunner:
    """
    Stress test runner for F1 Strategy Platform.
    Tests system under various load conditions.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict] = []
        self.errors: List[Dict] = []
        self.system_metrics: List[Dict] = []
    
    def _make_request(self, endpoint: str, method: str = "GET", 
                      data: Dict = None) -> Dict:
        """Make a single request and measure performance."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=30)
            else:
                response = requests.post(url, json=data, timeout=60)
            
            elapsed = time.time() - start_time
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_time": elapsed,
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat()
            }
    
    def _collect_system_metrics(self) -> Dict:
        """Collect system resource metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
    
    def run_concurrent_test(
        self,
        endpoint: str,
        method: str = "GET",
        data: Dict = None,
        concurrent_users: int = 100,
        requests_per_user: int = 10,
        ramp_up_time: float = 10.0
    ) -> Dict:
        """
        Run concurrent load test.
        
        Args:
            endpoint: API endpoint to test
            method: HTTP method
            data: Request data for POST
            concurrent_users: Number of concurrent users
            requests_per_user: Requests per user
            ramp_up_time: Time to ramp up all users (seconds)
        
        Returns:
            Test results dict
        """
        print(f"\n{'='*60}")
        print(f"Stress Test: {concurrent_users} users, {requests_per_user} requests each")
        print(f"Endpoint: {method} {endpoint}")
        print(f"{'='*60}\n")
        
        self.results = []
        self.errors = []
        self.system_metrics = []
        
        start_time = time.time()
        
        # System metrics collection thread
        def collect_metrics():
            while time.time() - start_time < (concurrent_users * requests_per_user * 0.5 + ramp_up_time):
                self.system_metrics.append(self._collect_system_metrics())
                time.sleep(1)
        
        # Start metrics collection
        import threading
        metrics_thread = threading.Thread(target=collect_metrics)
        metrics_thread.daemon = True
        metrics_thread.start()
        
        # Execute requests with thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            # Ramp up users gradually
            for user_id in range(concurrent_users):
                delay = (ramp_up_time / concurrent_users) * user_id
                
                for req_num in range(requests_per_user):
                    future = executor.submit(
                        self._make_request,
                        endpoint,
                        method,
                        data
                    )
                    futures.append((user_id, req_num, future))
                    
                    # Small delay between requests from same user
                    if req_num < requests_per_user - 1:
                        time.sleep(0.1)
                
                # Ramp up delay
                if user_id < concurrent_users - 1:
                    time.sleep(ramp_up_time / concurrent_users)
            
            # Collect results
            completed = 0
            total = len(futures)
            
            for user_id, req_num, future in futures:
                try:
                    result = future.result(timeout=120)
                    self.results.append(result)
                    
                    if not result["success"]:
                        self.errors.append(result)
                    
                    completed += 1
                    if completed % 50 == 0:
                        print(f"Progress: {completed}/{total} requests completed")
                        
                except Exception as e:
                    self.errors.append({
                        "success": False,
                        "error": str(e),
                        "user_id": user_id,
                        "request_num": req_num
                    })
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        successful_requests = [r for r in self.results if r["success"]]
        failed_requests = [r for r in self.results if not r["success"]]
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            
            stats = {
                "total_requests": len(self.results),
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "error_rate": len(failed_requests) / len(self.results) * 100 if self.results else 0,
                "total_time_seconds": total_time,
                "requests_per_second": len(self.results) / total_time if total_time > 0 else 0,
                "response_time": {
                    "mean": statistics.mean(response_times),
                    "median": statistics.median(response_times),
                    "min": min(response_times),
                    "max": max(response_times),
                    "p95": self._percentile(response_times, 95),
                    "p99": self._percentile(response_times, 99),
                    "std": statistics.stdev(response_times) if len(response_times) > 1 else 0
                }
            }
        else:
            stats = {
                "total_requests": len(self.results),
                "successful_requests": 0,
                "failed_requests": len(failed_requests),
                "error_rate": 100.0,
                "total_time_seconds": total_time
            }
        
        # System metrics summary
        if self.system_metrics:
            cpu_readings = [m["cpu_percent"] for m in self.system_metrics]
            memory_readings = [m["memory_percent"] for m in self.system_metrics]
            
            stats["system"] = {
                "cpu_max": max(cpu_readings),
                "cpu_mean": statistics.mean(cpu_readings),
                "memory_max": max(memory_readings),
                "memory_mean": statistics.mean(memory_readings)
            }
        
        return stats
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * (percentile / 100))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def test_health_endpoint(self, concurrent_users: int = 100) -> Dict:
        """Test health check endpoint."""
        return self.run_concurrent_test(
            endpoint="/health",
            method="GET",
            concurrent_users=concurrent_users,
            requests_per_user=20,
            ramp_up_time=5.0
        )
    
    def test_simulation_endpoint(self, concurrent_users: int = 50) -> Dict:
        """Test simulation endpoint (heavy load)."""
        return self.run_concurrent_test(
            endpoint="/simulate",
            method="POST",
            data={
                "circuit": "Monza",
                "strategy_type": "auto",
                "tire_compound": "soft",
                "weather": "dry"
            },
            concurrent_users=concurrent_users,
            requests_per_user=5,
            ramp_up_time=10.0
        )
    
    def test_monte_carlo_endpoint(self, concurrent_users: int = 20) -> Dict:
        """Test Monte Carlo optimization (very heavy load)."""
        return self.run_concurrent_test(
            endpoint="/optimize/advanced",
            method="POST",
            data={
                "circuit": "Monza",
                "laps": 53,
                "strategy_type": "auto",
                "num_simulations": 20,
                "rain_probability": 0.1
            },
            concurrent_users=concurrent_users,
            requests_per_user=3,
            ramp_up_time=10.0
        )
    
    def run_full_stress_test(self) -> Dict:
        """Run complete stress test suite."""
        print("\n" + "="*60)
        print("F1 STRATEGY PLATFORM - FULL STRESS TEST SUITE")
        print("="*60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "tests": {}
        }
        
        # Test 1: Health endpoint (light)
        print("\n[TEST 1] Health Check Endpoint")
        results["tests"]["health_light"] = self.test_health_endpoint(concurrent_users=100)
        self._print_results("Health (100 users)", results["tests"]["health_light"])
        
        # Wait between tests
        time.sleep(5)
        
        # Test 2: Health endpoint (heavy)
        print("\n[TEST 2] Health Check (Heavy Load)")
        results["tests"]["health_heavy"] = self.test_health_endpoint(concurrent_users=500)
        self._print_results("Health (500 users)", results["tests"]["health_heavy"])
        
        time.sleep(10)
        
        # Test 3: Basic simulation
        print("\n[TEST 3] Basic Simulation")
        results["tests"]["simulation"] = self.test_simulation_endpoint(concurrent_users=50)
        self._print_results("Simulation (50 users)", results["tests"]["simulation"])
        
        time.sleep(15)
        
        # Test 4: Monte Carlo (stress)
        print("\n[TEST 4] Monte Carlo Optimization (Stress)")
        results["tests"]["monte_carlo"] = self.test_monte_carlo_endpoint(concurrent_users=20)
        self._print_results("Monte Carlo (20 users)", results["tests"]["monte_carlo"])
        
        # Overall summary
        results["summary"] = self._calculate_overall_summary(results["tests"])
        
        return results
    
    def _print_results(self, test_name: str, results: Dict):
        """Print test results."""
        print(f"\n{test_name} Results:")
        print("-" * 40)
        print(f"Total Requests: {results.get('total_requests', 0)}")
        print(f"Successful: {results.get('successful_requests', 0)}")
        print(f"Failed: {results.get('failed_requests', 0)}")
        print(f"Error Rate: {results.get('error_rate', 0):.2f}%")
        print(f"Throughput: {results.get('requests_per_second', 0):.1f} req/s")
        
        if "response_time" in results:
            rt = results["response_time"]
            print(f"Response Times:")
            print(f"  Mean: {rt['mean']:.3f}s")
            print(f"  Median: {rt['median']:.3f}s")
            print(f"  P95: {rt['p95']:.3f}s")
            print(f"  P99: {rt['p99']:.3f}s")
        
        if "system" in results:
            sys = results["system"]
            print(f"System Load:")
            print(f"  CPU Max: {sys['cpu_max']:.1f}%")
            print(f"  Memory Max: {sys['memory_max']:.1f}%")
        
        # Pass/Fail
        if results.get('error_rate', 100) < 5 and results.get('response_time', {}).get('p95', 999) < 10:
            print("✓ PASS")
        else:
            print("✗ FAIL")
    
    def _calculate_overall_summary(self, tests: Dict) -> Dict:
        """Calculate overall test summary."""
        all_pass = all(
            t.get('error_rate', 100) < 5 and 
            t.get('response_time', {}).get('p95', 999) < 10
            for t in tests.values()
        )
        
        max_throughput = max(
            (t.get('requests_per_second', 0) for t in tests.values()),
            default=0
        )
        
        return {
            "all_tests_pass": all_pass,
            "max_throughput_rps": max_throughput,
            "total_requests": sum(t.get('total_requests', 0) for t in tests.values()),
            "recommendation": "System ready for production" if all_pass else "Performance issues detected"
        }
    
    def save_results(self, results: Dict, filename: str = None):
        """Save results to file."""
        if filename is None:
            filename = f"stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✓ Results saved to {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='F1 Strategy Platform Stress Test')
    parser.add_argument('--url', default='http://localhost:8000', help='Base URL')
    parser.add_argument('--users', type=int, default=100, help='Concurrent users')
    parser.add_argument('--full', action='store_true', help='Run full test suite')
    
    args = parser.parse_args()
    
    runner = StressTestRunner(args.url)
    
    if args.full:
        results = runner.run_full_stress_test()
        runner.save_results(results)
        
        print("\n" + "="*60)
        print("STRESS TEST COMPLETE")
        print("="*60)
        print(f"Overall: {'PASS' if results['summary']['all_tests_pass'] else 'FAIL'}")
        print(f"Max Throughput: {results['summary']['max_throughput_rps']:.1f} req/s")
        print(f"Recommendation: {results['summary']['recommendation']}")
    else:
        # Quick test
        results = runner.test_health_endpoint(args.users)
        print(f"\nQuick test: {results['successful_requests']}/{results['total_requests']} succeeded")
        print(f"Avg response time: {results['response_time']['mean']:.3f}s")
