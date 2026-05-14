"""
F1 Strategy Intelligence System - Elite Edition v3.0
Probabilistic Risk Engine with Bayesian Modeling

Implements uncertainty quantification and probabilistic outcomes
for strategy decisions using Bayesian inference and Monte Carlo methods.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from dataclasses import dataclass
import warnings
# warnings.filterwarnings('ignore')  # moved below imports

from app.core.config import CIRCUITS, TIRE_COMPOUNDS
warnings.filterwarnings('ignore')


@dataclass
class ProbabilisticOutcome:
    """Probabilistic outcome distribution for a strategy."""
    mean: float
    std: float
    confidence_95: Tuple[float, float]
    probability_p1: float
    probability_podium: float
    probability_points: float
    value_at_risk_95: float  # 5% worst case
    expected_shortfall: float  # Average of worst 5%
    distribution_type: str


@dataclass
class StrategyRegret:
    """Regret analysis comparing chosen vs optimal strategy."""
    actual_strategy: str
    optimal_strategy: str
    time_regret: float  # Seconds lost
    position_regret: int  # Positions lost
    hindsight_utility: float
    explanation: str


class BayesianRiskModel:
    """
    Bayesian risk model for strategy uncertainty quantification.
    
    Uses conjugate priors where possible, MCMC approximations otherwise.
    """
    
    def __init__(self, prior_confidence: float = 0.5):
        self.prior_confidence = prior_confidence
        
        # Prior distributions for lap times by circuit
        self.lap_time_priors = {}
        
        # Prior distributions for tire degradation
        self.degradation_priors = {}
        
        # Historical observations
        self.observations = []
        
    def fit_priors(self, historical_data: pd.DataFrame):
        """
        Fit prior distributions from historical race data.
        
        Args:
            historical_data: DataFrame with race history
        """
        # Group by circuit and tire
        for circuit in historical_data['circuit'].unique():
            circuit_data = historical_data[historical_data['circuit'] == circuit]
            
            self.lap_time_priors[circuit] = {}
            
            for tire in circuit_data['tire_compound'].unique():
                tire_data = circuit_data[circuit_data['tire_compound'] == tire]['lap_time']
                
                if len(tire_data) > 10:
                    # Fit normal distribution as prior
                    mu = tire_data.mean()
                    sigma = tire_data.std()
                    
                    # Use inverse-gamma prior for variance
                    # Simplified: store mean and precision
                    self.lap_time_priors[circuit][tire] = {
                        'mean': mu,
                        'precision': 1.0 / (sigma ** 2),
                        'nu': len(tire_data)  # degrees of freedom
                    }
        
        print(f"Fitted priors for {len(self.lap_time_priors)} circuits")
    
    def posterior_predictive_distribution(self,
                                       circuit: str,
                                       tire: str,
                                       tire_age: int,
                                       weather: str = 'dry',
                                       n_samples: int = 10000) -> np.ndarray:
        """
        Generate posterior predictive distribution for lap time.
        
        Returns:
            Array of samples from predictive distribution
        """
        # Get prior
        prior = self.lap_time_priors.get(circuit, {}).get(tire, {
            'mean': 90.0,
            'precision': 0.01,
            'nu': 10
        })
        
        # Base lap time from prior
        base_mean = prior['mean']
        base_precision = prior['precision']
        
        # Adjust for tire age (degradation)
        tire_config = TIRE_COMPOUNDS[tire]
        degradation = tire_config['degradation_rate'] * (tire_age ** 1.5)
        
        # Weather adjustment
        weather_mult = 1.0
        if weather == 'wet':
            weather_mult = 1.15
        elif weather == 'mixed':
            weather_mult = 1.08
        
        # Calculate predictive distribution parameters
        mean = (base_mean + degradation) * weather_mult
        
        # Variance increases with tire age (more uncertainty)
        variance = (1.0 / base_precision) + (tire_age * 0.01)
        
        # Generate samples
        samples = np.random.normal(mean, np.sqrt(variance), n_samples)
        
        return samples
    
    def bayesian_race_time_distribution(self,
                                       circuit: str,
                                       total_laps: int,
                                       pit_laps: List[int],
                                       tires: List[str],
                                       weather: str = 'dry',
                                       n_simulations: int = 5000) -> ProbabilisticOutcome:
        """
        Generate full probabilistic race time distribution.
        
        Returns:
            ProbabilisticOutcome with full uncertainty quantification
        """
        circuit_config = CIRCUITS[circuit]
        pit_loss = circuit_config['pit_loss']
        
        total_times = []
        
        for _ in range(n_simulations):
            total_time = 0.0
            current_tire_idx = 0
            
            for lap in range(1, total_laps + 1):
                # Determine current tire
                while (current_tire_idx < len(pit_laps) and 
                       lap > pit_laps[current_tire_idx]):
                    current_tire_idx += 1
                
                current_tire = tires[min(current_tire_idx, len(tires) - 1)]
                
                # Calculate tire age
                if current_tire_idx == 0:
                    tire_age = lap
                else:
                    tire_age = lap - pit_laps[current_tire_idx - 1]
                
                # Sample lap time from posterior predictive
                lap_samples = self.posterior_predictive_distribution(
                    circuit, current_tire, tire_age, weather, n_samples=1
                )
                
                total_time += lap_samples[0]
                
                # Add pit time if applicable
                if lap in pit_laps:
                    # Pit loss has uncertainty too
                    pit_time = np.random.normal(pit_loss, 2.0)
                    total_time += max(pit_time, pit_loss * 0.8)
            
            total_times.append(total_time)
        
        total_times = np.array(total_times)
        
        # Calculate statistics
        mean_time = np.mean(total_times)
        std_time = np.std(total_times)
        ci_lower, ci_upper = np.percentile(total_times, [2.5, 97.5])
        
        # Value at Risk (95% - worst 5%)
        var_95 = np.percentile(total_times, 95)
        
        # Expected Shortfall (average of worst 5%)
        worst_5_percent = total_times[total_times >= var_95]
        expected_shortfall = np.mean(worst_5_percent) if len(worst_5_percent) > 0 else var_95
        
        # Position probabilities (relative to simulated competition)
        # Simulate competitor times
        competitor_times = []
        for _ in range(15):  # 15 competitors
            # Random strategy variation
            comp_variance = np.random.normal(0, 15)
            competitor_times.append(mean_time + comp_variance)
        
        # Calculate position for each simulation
        positions = []
        for our_time in total_times:
            all_times = competitor_times + [our_time]
            position = sorted(all_times).index(our_time) + 1
            positions.append(position)
        
        positions = np.array(positions)
        
        prob_p1 = np.mean(positions == 1)
        prob_podium = np.mean(positions <= 3)
        prob_points = np.mean(positions <= 10)
        
        return ProbabilisticOutcome(
            mean=float(mean_time),
            std=float(std_time),
            confidence_95=(float(ci_lower), float(ci_upper)),
            probability_p1=float(prob_p1),
            probability_podium=float(prob_podium),
            probability_points=float(prob_points),
            value_at_risk_95=float(var_95),
            expected_shortfall=float(expected_shortfall),
            distribution_type='bayesian_posterior'
        )
    
    def tire_delta_analysis(self,
                         our_tire: str,
                         our_age: int,
                         opponent_tire: str,
                         opponent_age: int,
                         circuit: str) -> Dict:
        """
        Calculate tire performance delta between two cars.
        
        Returns:
            Tire delta analysis with uncertainty
        """
        # Sample lap times for both
        n_samples = 5000
        
        our_samples = self.posterior_predictive_distribution(
            circuit, our_tire, our_age, n_samples=n_samples
        )
        opponent_samples = self.posterior_predictive_distribution(
            circuit, opponent_tire, opponent_age, n_samples=n_samples
        )
        
        # Calculate deltas
        delta_samples = our_samples - opponent_samples
        
        # Positive delta = we're slower
        prob_slower = np.mean(delta_samples > 0)
        prob_faster = np.mean(delta_samples < 0)
        
        return {
            'our_tire': our_tire,
            'our_age': our_age,
            'opponent_tire': opponent_tire,
            'opponent_age': opponent_age,
            'mean_delta': float(np.mean(delta_samples)),
            'std_delta': float(np.std(delta_samples)),
            'prob_we_are_faster': float(prob_faster),
            'prob_opponent_faster': float(prob_slower),
            'expected_lap_advantage': float(-np.mean(delta_samples)),  # Negative = our advantage
            'delta_confidence_95': (
                float(np.percentile(delta_samples, 2.5)),
                float(np.percentile(delta_samples, 97.5))
            ),
            'interpretation': self._interpret_delta(
                float(np.mean(delta_samples)), 
                float(prob_faster),
                our_tire, opponent_tire
            )
        }
    
    def _interpret_delta(self, mean_delta: float, prob_faster: float,
                        our_tire: str, their_tire: str) -> str:
        """Generate human-readable interpretation of tire delta."""
        if prob_faster > 0.7:
            return f"Strong tire advantage ({our_tire} vs {their_tire}). {(1-mean_delta):.2f}s/lap faster."
        elif prob_faster > 0.5:
            return f"Slight tire advantage. {(1-mean_delta):.2f}s/lap faster on average."
        elif prob_faster > 0.3:
            return f"Competitive tire performance. {(1-mean_delta):.2f}s/lap difference."
        else:
            return f"Tire disadvantage ({our_tire} vs {their_tire}). {abs(mean_delta):.2f}s/lap slower."
    
    def calculate_strategy_regret(self,
                                 chosen_strategy: Dict,
                                 race_results: Dict,
                                 circuit: str) -> StrategyRegret:
        """
        Calculate regret - how much better we could have done.
        
        Args:
            chosen_strategy: Strategy that was executed
            race_results: Actual race outcome
            circuit: Circuit name
            
        Returns:
            StrategyRegret analysis
        """
        # In practice, would compare against simulated alternatives
        # For now, estimate based on position outcome
        
        final_position = race_results.get('position', 10)
        actual_time = race_results.get('total_time', 5000)
        
        # Estimate optimal (P1 time)
        optimal_time = actual_time - (final_position - 1) * 10  # Rough estimate
        
        time_regret = optimal_time - actual_time
        position_regret = final_position - 1
        
        # Calculate hindsight utility
        # What would have been optimal?
        if final_position == 1:
            hindsight = "Optimal strategy executed. No regret."
            utility = 1.0
        elif final_position <= 3:
            hindsight = "Good result, but podium possible with better strategy."
            utility = 0.7
        elif final_position <= 10:
            hindsight = "Points scored, but higher positions achievable."
            utility = 0.4
        else:
            hindsight = "Significant regret. Major strategy errors likely."
            utility = 0.1
        
        return StrategyRegret(
            actual_strategy=chosen_strategy.get('type', 'unknown'),
            optimal_strategy='theoretical_optimal',
            time_regret=abs(time_regret),
            position_regret=position_regret,
            hindsight_utility=utility,
            explanation=hindsight
        )
    
    def risk_adjusted_strategy_ranking(self,
                                    strategies: List[Dict],
                                    risk_tolerance: float = 0.5) -> List[Dict]:
        """
        Rank strategies by risk-adjusted expected utility.
        
        Args:
            strategies: List of strategy dicts with probabilistic outcomes
            risk_tolerance: 0=very risk averse, 1=risk neutral
            
        Returns:
            Ranked strategies with utility scores
        """
        ranked = []
        
        for strategy in strategies:
            outcome = strategy.get('probabilistic_outcome')
            if not outcome:
                continue
            
            # Expected utility components
            p1_utility = outcome.probability_p1 * 100  # Win bonus
            podium_utility = outcome.probability_podium * 50
            points_utility = outcome.probability_points * 20
            
            # Risk penalty (variance penalty)
            risk_penalty = (1 - risk_tolerance) * outcome.std * 0.5
            
            # VaR penalty (worst case consideration)
            var_penalty = (1 - risk_tolerance) * (outcome.value_at_risk_95 - outcome.mean) * 0.3
            
            total_utility = p1_utility + podium_utility + points_utility - risk_penalty - var_penalty
            
            ranked.append({
                **strategy,
                'utility_score': total_utility,
                'components': {
                    'win_utility': p1_utility,
                    'podium_utility': podium_utility,
                    'points_utility': points_utility,
                    'risk_penalty': risk_penalty,
                    'var_penalty': var_penalty
                }
            })
        
        # Sort by utility (descending)
        ranked.sort(key=lambda x: x['utility_score'], reverse=True)
        
        return ranked


class UncertaintyQuantifier:
    """
    Real-time uncertainty quantification for live race decisions.
    """
    
    def __init__(self):
        self.uncertainty_budget = 1.0  # Base uncertainty
        
    def quantify_state_uncertainty(self,
                                  lap_data: List[Dict],
                                  weather_forecast: Dict) -> Dict:
        """
        Quantify uncertainty in current race state.
        
        Returns:
            Uncertainty breakdown by component
        """
        # Tire age uncertainty
        latest_lap = lap_data[-1] if lap_data else {}
        tire_age = latest_lap.get('tire_age', 0)
        tire_uncertainty = min(1.0, tire_age / 50)  # Increases with tire age
        
        # Weather uncertainty
        weather_changes = weather_forecast.get('state_changes', 0)
        weather_uncertainty = min(1.0, weather_changes / 5)
        
        # Traffic uncertainty (position effects)
        position = latest_lap.get('position', 10)
        traffic_uncertainty = max(0, (10 - position) / 10) * 0.5
        
        # Lap time variance
        if len(lap_data) > 5:
            recent_times = [lap['lap_time'] for lap in lap_data[-5:]]
            time_std = np.std(recent_times)
            performance_uncertainty = min(1.0, time_std / 2.0)
        else:
            performance_uncertainty = 0.5
        
        total_uncertainty = np.mean([
            tire_uncertainty, weather_uncertainty, 
            traffic_uncertainty, performance_uncertainty
        ])
        
        return {
            'total_uncertainty': float(total_uncertainty),
            'components': {
                'tire_uncertainty': float(tire_uncertainty),
                'weather_uncertainty': float(weather_uncertainty),
                'traffic_uncertainty': float(traffic_uncertainty),
                'performance_uncertainty': float(performance_uncertainty)
            },
            'recommendation_confidence': float(1 - total_uncertainty),
            'confidence_level': self._classify_confidence(1 - total_uncertainty)
        }
    
    def _classify_confidence(self, confidence: float) -> str:
        """Classify confidence level."""
        if confidence > 0.8:
            return 'HIGH'
        elif confidence > 0.6:
            return 'MODERATE'
        elif confidence > 0.4:
            return 'LOW'
        else:
            return 'CRITICAL - High Uncertainty'


def quick_probabilistic_analysis(circuit: str,
                                 total_laps: int,
                                 pit_laps: List[int],
                                 tires: List[str]) -> Dict:
    """
    Quick probabilistic analysis without full Bayesian inference.
    
    Returns:
        Simplified probabilistic outcome
    """
    engine = BayesianRiskModel()
    
    # Generate outcome
    outcome = engine.bayesian_race_time_distribution(
        circuit, total_laps, pit_laps, tires, n_simulations=1000
    )
    
    return {
        'expected_time': outcome.mean,
        'uncertainty': outcome.std,
        'confidence_interval_95': outcome.confidence_95,
        'win_probability': outcome.probability_p1,
        'podium_probability': outcome.probability_podium,
        'points_probability': outcome.probability_points,
        'risk_score': outcome.value_at_risk_95 - outcome.mean,
        'worst_case_95th': outcome.value_at_risk_95
    }


if __name__ == "__main__":
    # Test probabilistic risk engine
    print("Testing Probabilistic Risk Engine")
    print("=" * 60)
    
    engine = BayesianRiskModel()
    
    # Test 1: Posterior predictive
    print("\n1. Posterior Predictive Distribution")
    samples = engine.posterior_predictive_distribution('Monza', 'soft', 20, 'dry', 1000)
    print(f"Mean: {np.mean(samples):.2f}s")
    print(f"Std: {np.std(samples):.2f}s")
    print(f"95% CI: ({np.percentile(samples, 2.5):.2f}, {np.percentile(samples, 97.5):.2f})")
    
    # Test 2: Full race distribution
    print("\n2. Bayesian Race Time Distribution")
    outcome = engine.bayesian_race_time_distribution(
        'Monza', 53, [18, 36], ['soft', 'medium', 'hard'], n_simulations=500
    )
    print(f"Expected Time: {outcome.mean:.1f}s ± {outcome.std:.1f}s")
    print(f"Win Probability: {outcome.probability_p1:.1%}")
    print(f"Podium Probability: {outcome.probability_podium:.1%}")
    print(f"Points Probability: {outcome.probability_points:.1%}")
    print(f"Value at Risk (95%): {outcome.value_at_risk_95:.1f}s")
    print(f"Expected Shortfall: {outcome.expected_shortfall:.1f}s")
    
    # Test 3: Tire delta
    print("\n3. Tire Delta Analysis")
    delta = engine.tire_delta_analysis('soft', 15, 'medium', 25, 'Monza')
    print(f"Mean Delta: {delta['mean_delta']:.3f}s")
    print(f"P(We are faster): {delta['prob_we_are_faster']:.1%}")
    print(f"Interpretation: {delta['interpretation']}")
    
    # Test 4: Uncertainty quantifier
    print("\n4. Uncertainty Quantification")
    uq = UncertaintyQuantifier()
    lap_data = [
        {'lap': i, 'lap_time': 90 + np.random.normal(0, 0.5), 'tire_age': i, 'position': 3}
        for i in range(1, 21)
    ]
    weather = {'state_changes': 2}
    
    uncertainty = uq.quantify_state_uncertainty(lap_data, weather)
    print(f"Total Uncertainty: {uncertainty['total_uncertainty']:.2%}")
    print(f"Confidence: {uncertainty['recommendation_confidence']:.2%}")
    print(f"Level: {uncertainty['confidence_level']}")
    
    # Test 5: Quick analysis
    print("\n5. Quick Probabilistic Analysis")
    quick = quick_probabilistic_analysis('Monza', 53, [20, 38], ['soft', 'medium', 'hard'])
    print(f"Expected: {quick['expected_time']:.1f}s")
    print(f"Win %: {quick['win_probability']:.1%}")
    print(f"Risk Score: {quick['risk_score']:.1f}s")
    
    print("\n" + "=" * 60)
    print("Probabilistic Risk Engine test complete!")
