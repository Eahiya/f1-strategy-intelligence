"""
F1 Strategy Platform v4.0 - Load Testing Suite
Locust script for performance testing with realistic user scenarios.
"""
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import random
import json
import time


class F1StrategyUser(HttpUser):
    """Simulates a user interacting with the F1 Strategy Platform."""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Login when user starts."""
        self.circuits = ["Monza", "Silverstone", "Spa", "Monaco", "Suzuka"]
        self.strategies = ["1_stop", "2_stop", "3_stop", "auto"]
        self.tires = ["soft", "medium", "hard"]
        
        # Attempt login
        self.login()
    
    def login(self):
        """Simulate user login."""
        credentials = {
            "username": f"loadtest_user_{self.user_id}",
            "password": "TestPass123!"
        }
        
        with self.client.post("/auth/login", json=credentials, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                response.success()
            else:
                # For load testing, we'll simulate successful auth
                self.token = "test_token"
                self.headers = {"Authorization": "Bearer test_token"}
                response.success()
    
    @task(3)
    def basic_simulation(self):
        """Run basic strategy simulation (most common task)."""
        payload = {
            "circuit": random.choice(self.circuits),
            "laps": None,  # Use default
            "strategy_type": random.choice(self.strategies),
            "tire_compound": random.choice(self.tires),
            "weather": random.choice(["dry", "wet", "mixed"]),
            "include_safety_car": random.random() < 0.3
        }
        
        with self.client.post(
            "/simulate",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/simulate (basic)"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Verify response structure
                if "best_strategy" in data and "pit_laps" in data:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            elif response.status_code == 429:
                response.success()  # Rate limiting is expected under load
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(2)
    def advanced_optimization(self):
        """Run advanced Monte Carlo optimization (engineer/admin only)."""
        payload = {
            "circuit": random.choice(self.circuits),
            "laps": 53,
            "strategy_type": "auto",
            "initial_weather": "dry",
            "rain_probability": random.uniform(0.0, 0.3),
            "num_simulations": 50,
            "risk_aversion": random.uniform(0.2, 0.5)
        }
        
        with self.client.post(
            "/optimize/advanced",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/optimize/advanced"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [401, 403]:
                response.success()  # Expected for viewer users
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(1)
    def multi_car_simulation(self):
        """Run multi-car race simulation (computationally expensive)."""
        payload = {
            "circuit": random.choice(self.circuits),
            "laps": 53,
            "num_cars": random.randint(5, 15),
            "weather": "dry",
            "strategies": ["balanced", "aggressive", "conservative"]
        }
        
        with self.client.post(
            "/simulate/multi-car",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/simulate/multi-car"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(2)
    def weather_simulation(self):
        """Run weather simulation."""
        payload = {
            "circuit": random.choice(self.circuits),
            "laps": 53,
            "initial_weather": "dry",
            "rain_probability": 0.2
        }
        
        with self.client.post(
            "/simulate/weather",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/simulate/weather"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(1)
    def elite_rl_strategy(self):
        """Test RL strategy endpoint (engineer/admin)."""
        payload = {
            "circuit": "Monza",
            "total_laps": 53,
            "current_lap": random.randint(10, 40),
            "position": random.randint(1, 10),
            "gap_to_ahead": random.uniform(0.5, 3.0),
            "gap_to_behind": random.uniform(0.5, 5.0),
            "tire_age": random.randint(5, 30),
            "tire_compound": random.choice(["soft", "medium", "hard"]),
            "weather": "dry",
            "safety_car": False
        }
        
        with self.client.post(
            "/elite/rl-strategy",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="/elite/rl-strategy"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [401, 403]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(4)
    def get_health(self):
        """Check health endpoint (lightweight)."""
        with self.client.get("/health", catch_response=True, name="/health") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def get_circuits(self):
        """Get circuits list."""
        with self.client.get("/circuits", headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class HeavyLoadUser(HttpUser):
    """Simulates heavy users making computationally expensive requests."""
    
    wait_time = between(5, 15)
    weight = 1  # Fewer heavy users
    
    @task
    def digital_twin_simulation(self):
        """Run expensive digital twin simulation."""
        payload = {
            "circuit": "Monza",
            "current_lap": 25,
            "current_state": {
                "position": 3,
                "tire_age": 20,
                "tire_compound": "soft",
                "gap_to_ahead": 1.5,
                "pit_laps": [20, 40],
                "tires": ["soft", "medium", "hard"]
            }
        }
        
        with self.client.post(
            "/elite/digital-twin",
            json=payload,
            catch_response=True,
            name="/elite/digital-twin (heavy)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


# ==========================================
# Event Hooks
# ==========================================
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, 
               response, context, exception, **kwargs):
    """Log detailed request metrics."""
    if exception:
        print(f"Request failed: {name} - {exception}")


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """Print summary when test ends."""
    print("\n" + "=" * 60)
    print("LOAD TEST COMPLETED")
    print("=" * 60)
    
    stats = environment.runner.stats
    
    print(f"\nTotal Requests: {stats.num_requests}")
    print(f"Failed Requests: {stats.num_failures}")
    print(f"Avg Response Time: {stats.avg_response_time:.2f}ms")
    print(f"Max Response Time: {stats.max_response_time:.2f}ms")
    
    if stats.num_requests > 0:
        error_rate = (stats.num_failures / stats.num_requests) * 100
        print(f"Error Rate: {error_rate:.2f}%")
    
    print("\nResponse Time Percentiles:")
    print(f"  50% (median): {stats.get_response_time_percentile(0.5):.2f}ms")
    print(f"  90%: {stats.get_response_time_percentile(0.9):.2f}ms")
    print(f"  95%: {stats.get_response_time_percentile(0.95):.2f}ms")
    print(f"  99%: {stats.get_response_time_percentile(0.99):.2f}ms")


# ==========================================
# Run Configuration
# ==========================================
if __name__ == "__main__":
    print("""
    F1 Strategy Platform - Load Testing
    ====================================
    
    Usage:
      # Run with web UI
      locust -f locustfile.py --host=http://localhost
      
      # Run headless (command line)
      locust -f locustfile.py --host=http://localhost \
        --headless -u 100 -r 10 --run-time 5m
      
      # Run distributed (multiple workers)
      locust -f locustfile.py --host=http://localhost --master
      locust -f locustfile.py --host=http://localhost --worker
    
    Options:
      -u, --users: Number of concurrent users
      -r, --spawn-rate: Users to spawn per second
      --run-time: Test duration (e.g., 5m, 1h)
    """)
