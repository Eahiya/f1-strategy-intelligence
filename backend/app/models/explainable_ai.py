"""
F1 Strategy Intelligence System - Elite Edition v3.0
Explainable AI (XAI) Engine

Provides transparent, interpretable explanations for all AI decisions,
including alternative analysis and structured reasoning output.
"""
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from app.models.rl_strategy_engine import RaceState


class ExplanationType(Enum):
    """Types of explanations available."""
    STRATEGY_DECISION = "strategy_decision"
    PIT_TIMING = "pit_timing"
    TIRE_CHOICE = "tire_choice"
    RISK_ASSESSMENT = "risk_assessment"
    UNDERCUT_OPPORTUNITY = "undercut_opportunity"
    DEFENSIVE_ACTION = "defensive_action"
    COMPETITIVE_ANALYSIS = "competitive_analysis"


@dataclass
class DecisionFactor:
    """Individual factor contributing to a decision."""
    factor_name: str
    category: str  # 'tire', 'position', 'weather', 'opponent', 'timing'
    importance_score: float  # 0-1
    impact_direction: str  # 'positive', 'negative', 'neutral'
    current_value: Any
    threshold_value: Any
    description: str


@dataclass
class AlternativeOption:
    """Alternative option that was considered."""
    option_name: str
    option_description: str
    expected_outcome: str
    why_rejected: str
    risk_level: str  # 'low', 'medium', 'high'
    time_difference: float  # vs chosen option


@dataclass
class StrategyExplanation:
    """Comprehensive explanation for a strategy decision."""
    explanation_id: str
    timestamp: str
    decision_type: ExplanationType
    
    # Core decision
    recommended_action: str
    confidence: float
    
    # Reasoning
    primary_reasoning: str
    decision_factors: List[DecisionFactor]
    
    # Alternatives
    alternatives_considered: List[AlternativeOption]
    
    # Risk analysis
    risk_if_executed: Dict
    risk_if_not_executed: Dict
    
    # What-if scenarios
    best_case_scenario: str
    worst_case_scenario: str
    most_likely_scenario: str
    
    # Supporting data
    key_metrics: Dict
    visual_indicators: Dict  # For UI rendering
    
    # For debugging/validation
    raw_model_outputs: Dict
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'explanation_id': self.explanation_id,
            'timestamp': self.timestamp,
            'decision_type': self.decision_type.value,
            'recommended_action': self.recommended_action,
            'confidence': self.confidence,
            'primary_reasoning': self.primary_reasoning,
            'decision_factors': [
                {
                    'factor_name': f.factor_name,
                    'category': f.category,
                    'importance_score': f.importance_score,
                    'impact_direction': f.impact_direction,
                    'current_value': f.current_value,
                    'threshold_value': f.threshold_value,
                    'description': f.description
                }
                for f in self.decision_factors
            ],
            'alternatives_considered': [
                {
                    'option_name': a.option_name,
                    'description': a.option_description,
                    'expected_outcome': a.expected_outcome,
                    'why_rejected': a.why_rejected,
                    'risk_level': a.risk_level,
                    'time_difference': a.time_difference
                }
                for a in self.alternatives_considered
            ],
            'risk_analysis': {
                'if_executed': self.risk_if_executed,
                'if_not_executed': self.risk_if_not_executed
            },
            'scenarios': {
                'best_case': self.best_case_scenario,
                'worst_case': self.worst_case_scenario,
                'most_likely': self.most_likely_scenario
            },
            'key_metrics': self.key_metrics,
            'visual_indicators': self.visual_indicators
        }
    
    def to_natural_language(self) -> str:
        """Generate human-readable explanation."""
        nl = f"Strategy Recommendation: {self.recommended_action}\n\n"
        
        nl += f"Primary Reasoning:\n{self.primary_reasoning}\n\n"
        
        nl += "Key Factors:\n"
        for factor in sorted(self.decision_factors, 
                            key=lambda x: x.importance_score, reverse=True)[:5]:
            nl += f"  • {factor.factor_name}: {factor.description}\n"
        
        nl += f"\nConfidence: {self.confidence:.0%}\n\n"
        
        if self.alternatives_considered:
            nl += "Alternatives Considered:\n"
            for alt in self.alternatives_considered:
                nl += f"  • {alt.option_name}: {alt.why_rejected}\n"
        
        nl += "\nRisk Analysis:\n"
        nl += f"  If we execute: {self.risk_if_executed.get('summary', 'N/A')}\n"
        nl += f"  If we don't: {self.risk_if_not_executed.get('summary', 'N/A')}\n"
        
        return nl


class ExplainableAIEngine:
    """
    Elite Explainable AI Engine for F1 strategy decisions.
    Provides transparent, interpretable explanations for all AI outputs.
    """
    
    def __init__(self):
        self.explanation_history = []
        self.factor_weights = {
            'tire_age': 0.25,
            'gap_to_ahead': 0.20,
            'track_position': 0.15,
            'weather': 0.15,
            'safety_car': 0.15,
            'tire_compound': 0.10
        }
    
    def explain_strategy_decision(self,
                                 race_state: RaceState,
                                 rl_recommendation: Dict,
                                 optimizer_recommendation: Dict,
                                 opponent_analysis: Optional[Dict] = None) -> StrategyExplanation:
        """
        Generate comprehensive explanation for strategy decision.
        
        Returns:
            StrategyExplanation with full reasoning
        """
        import uuid
        from datetime import datetime
        
        explanation_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        # Determine primary recommendation
        if rl_recommendation.get('confidence', 0) > 0.7:
            recommended_action = rl_recommendation['action_name']
            confidence = rl_recommendation['confidence']
            # primary_source = 'rl_agent'
        else:
            rec = optimizer_recommendation
            if rec.get('pit_laps') and race_state.lap_number in range(
                rec['pit_laps'][0] - 2, rec['pit_laps'][0] + 2):
                recommended_action = "PIT (Monte Carlo optimized)"
                confidence = 0.75
            else:
                recommended_action = "STAY_OUT"
                confidence = 0.6
            # primary_source = 'monte_carlo_optimizer'  # unused variable removed
        
        # Build decision factors
        factors = self._build_decision_factors(race_state, rl_recommendation)
        
        # Generate primary reasoning
        primary_reasoning = self._generate_primary_reasoning(
            race_state, factors, recommended_action
        )
        
        # Generate alternatives
        alternatives = self._generate_alternatives(
            race_state, recommended_action, rl_recommendation
        )
        
        # Risk analysis
        risk_executed, risk_not_executed = self._analyze_risks(
            race_state, recommended_action, factors
        )
        
        # Scenarios
        scenarios = self._generate_scenarios(race_state, recommended_action)
        
        # Key metrics
        metrics = self._extract_key_metrics(race_state)
        
        # Visual indicators
        visuals = self._generate_visual_indicators(race_state, factors)
        
        explanation = StrategyExplanation(
            explanation_id=explanation_id,
            timestamp=timestamp,
            decision_type=ExplanationType.STRATEGY_DECISION,
            recommended_action=recommended_action,
            confidence=confidence,
            primary_reasoning=primary_reasoning,
            decision_factors=factors,
            alternatives_considered=alternatives,
            risk_if_executed=risk_executed,
            risk_if_not_executed=risk_not_executed,
            best_case_scenario=scenarios['best_case'],
            worst_case_scenario=scenarios['worst_case'],
            most_likely_scenario=scenarios['most_likely'],
            key_metrics=metrics,
            visual_indicators=visuals,
            raw_model_outputs={
                'rl': rl_recommendation,
                'optimizer': optimizer_recommendation,
                'opponent': opponent_analysis
            }
        )
        
        self.explanation_history.append(explanation)
        return explanation
    
    def _build_decision_factors(self, 
                               state: RaceState, 
                               rl_rec: Dict) -> List[DecisionFactor]:
        """Build list of factors influencing decision."""
        factors = []
        
        # Tire age factor
        tire_old = state.tire_age > 25
        factors.append(DecisionFactor(
            factor_name="Tire Age",
            category="tire",
            importance_score=self.factor_weights['tire_age'] * (1 if tire_old else 0.5),
            impact_direction="negative" if tire_old else "neutral",
            current_value=state.tire_age,
            threshold_value=25,
            description=f"Tires are {state.tire_age} laps old. "
                       f"{'Degradation significant.' if tire_old else 'Still have life.'}"
        ))
        
        # Gap to ahead
        close_gap = 0 < state.gap_to_ahead < 2.0
        factors.append(DecisionFactor(
            factor_name="Gap to Car Ahead",
            category="position",
            importance_score=self.factor_weights['gap_to_ahead'] * (1.2 if close_gap else 0.6),
            impact_direction="positive" if close_gap else "neutral",
            current_value=round(state.gap_to_ahead, 2),
            threshold_value=2.0,
            description=f"Gap to ahead: {state.gap_to_ahead:.2f}s. "
                       f"{'Undercut viable!' if close_gap else 'Too far for undercut.'}"
        ))
        
        # Track position
        podium_position = state.current_position <= 3
        factors.append(DecisionFactor(
            factor_name="Track Position",
            category="position",
            importance_score=self.factor_weights['track_position'] * (1.5 if podium_position else 0.8),
            impact_direction="positive" if state.current_position <= 5 else "neutral",
            current_value=state.current_position,
            threshold_value=3,
            description=f"P{state.current_position}. "
                       f"{'Podium position - defend!' if podium_position else 'Midfield - attack mode.'}"
        ))
        
        # Safety car
        if state.safety_car_active:
            factors.append(DecisionFactor(
                factor_name="Safety Car",
                category="timing",
                importance_score=self.factor_weights['safety_car'],
                impact_direction="positive",
                current_value="Active",
                threshold_value="Inactive",
                description="SAFETY CAR DEPLOYED. Pit window wide open. ~15s saved."
            ))
        
        # Weather
        if state.weather_condition > 0:
            factors.append(DecisionFactor(
                factor_name="Weather Conditions",
                category="weather",
                importance_score=self.factor_weights['weather'],
                impact_direction="negative" if state.weather_condition == 2 else "neutral",
                current_value=['dry', 'light_rain', 'heavy_rain'][state.weather_condition],
                threshold_value="dry",
                description="Rain affecting grip. Consider inters/wets."
            ))
        
        # Tire compound
        compound_name = {0: 'soft', 1: 'medium', 2: 'hard', 3: 'inter', 4: 'wet'}.get(
            state.tire_compound, 'unknown')
        factors.append(DecisionFactor(
            factor_name="Current Tire Compound",
            category="tire",
            importance_score=self.factor_weights['tire_compound'],
            impact_direction="neutral",
            current_value=compound_name,
            threshold_value="optimal",
            description=f"Running {compound_name.upper()}. "
                       f"{'Fast but fragile.' if state.tire_compound == 0 else 'Balanced.' if state.tire_compound == 1 else 'Durable.'}"
        ))
        
        return factors
    
    def _generate_primary_reasoning(self,
                                  state: RaceState,
                                  factors: List[DecisionFactor],
                                  recommended_action: str) -> str:
        """Generate primary reasoning text."""
        # Sort by importance
        # top_factors = sorted(factors, key=lambda x: x.importance_score, reverse=True)[:3]  # unused variable removed
        
        reasoning_parts = []
        
        if state.safety_car_active and 'PIT' in recommended_action:
            reasoning_parts.append(
                "SAFETY CAR presents a strategic opportunity. "
                "Pit loss time reduced by ~15 seconds."
            )
        
        if state.gap_to_ahead < 2.0 and state.gap_to_ahead > 0:
            reasoning_parts.append(
                f"Close gap to car ahead ({state.gap_to_ahead:.2f}s) "
                f"creates undercut opportunity. Fresh tires will gain 2-3s on out-lap."
            )
        
        if state.tire_age > 25:
            reasoning_parts.append(
                f"Tire degradation at {state.tire_age} laps is costing "
                f"~{state.tire_degradation:.2f}s per lap. Pit stop recommended."
            )
        
        if state.current_position <= 3:
            reasoning_parts.append(
                f"P{state.current_position} is championship-critical. "
                "Prioritize track position over pure pace."
            )
        
        if not reasoning_parts:
            reasoning_parts.append(
                "Current strategy on track. No immediate action required. "
                "Continue monitoring gaps and tire degradation."
            )
        
        return " ".join(reasoning_parts)
    
    def _generate_alternatives(self,
                             state: RaceState,
                             chosen_action: str,
                             rl_rec: Dict) -> List[AlternativeOption]:
        """Generate alternative options that were considered."""
        alternatives = []
        
        if 'PIT' in chosen_action:
            # Alternative: Stay out
            risk = 'high' if state.tire_age > 30 else 'medium'
            alternatives.append(AlternativeOption(
                option_name="Stay Out",
                option_description="Continue current stint",
                expected_outcome="Lap times will degrade. Risk losing positions.",
                why_rejected=f"Tires at {state.tire_age} laps - degradation too high",
                risk_level=risk,
                time_difference=-2.0 if state.tire_age > 25 else 0.0
            ))
        else:
            # Alternative: Pit now
            alternatives.append(AlternativeOption(
                option_name="Pit Now",
                option_description="Immediate pit stop",
                expected_outcome="Fresh tires but lose track position",
                why_rejected=f"Too early in stint ({state.tire_age} laps). "
                           "Optimal window not yet reached.",
                risk_level='medium',
                time_difference=22.0  # Pit loss
            ))
            
            # Alternative: Pit next lap
            alternatives.append(AlternativeOption(
                option_name="Pit Next Lap",
                option_description="Delay pit by one lap",
                expected_outcome="Similar outcome, slight tire degradation",
                why_rejected="Marginal difference, current lap is optimal",
                risk_level='low',
                time_difference=0.5
            ))
        
        return alternatives
    
    def _analyze_risks(self, 
                      state: RaceState,
                      action: str,
                      factors: List[DecisionFactor]) -> Tuple[Dict, Dict]:
        """Analyze risks of executing vs not executing recommendation."""
        
        if 'PIT' in action:
            risk_executed = {
                'summary': 'Lose track position. Traffic on exit.',
                'position_loss_probability': 0.3,
                'time_risk': 22.0,
                'mitigation': 'Undercut car ahead to maintain position'
            }
            
            risk_not_executed = {
                'summary': f'Tire degradation at {state.tire_age} laps will cost positions.',
                'position_loss_probability': 0.7 if state.tire_age > 25 else 0.4,
                'time_risk': state.tire_degradation * 5,  # Next 5 laps
                'mitigation': 'None - degradation is inevitable'
            }
        else:
            risk_executed = {
                'summary': 'Maintain track position but tire degradation continues.',
                'position_loss_probability': 0.2,
                'time_risk': state.tire_degradation * 3,
                'mitigation': 'Push harder on tires to defend'
            }
            
            risk_not_executed = {
                'summary': 'Missed opportunity if safety car or undercut window closes.',
                'position_loss_probability': 0.5 if state.safety_car_active else 0.2,
                'time_risk': 0.0,
                'mitigation': 'Prepare for next opportunity'
            }
        
        return risk_executed, risk_not_executed
    
    def _generate_scenarios(self, 
                          state: RaceState,
                          action: str) -> Dict[str, str]:
        """Generate what-if scenarios."""
        
        if 'PIT' in action:
            return {
                'best_case': (
                    "Exit pits ahead of car that was ahead. "
                    "Fresh tires allow extending lead by 0.5s/lap. "
                    "Gain 1-2 positions by end of race."
                ),
                'worst_case': (
                    "Exit in traffic. Lose 3 positions to cars that didn't pit. "
                    "Spend 10 laps trying to overtake. "
                    "Finish 2 positions lower than if stayed out."
                ),
                'most_likely': (
                    "Maintain current position. "
                    f"Gap to ahead changes from {state.gap_to_ahead:.2f}s "
                    f"to ~{state.gap_to_ahead - 1.5:.2f}s. "
                    "Net neutral position change."
                )
            }
        else:
            return {
                'best_case': (
                    "Tire degradation slower than expected. "
                    "Maintain pace and positions. "
                    "Next pit window even better."
                ),
                'worst_case': (
                    "Rapid tire degradation. "
                    f"Lose {state.gap_to_behind + 1:.1f}s to car behind in 5 laps. "
                    "Overtaken and unable to regain position."
                ),
                'most_likely': (
                    "Gradual pace decline. "
                    "Lose 1 position to car on fresher tires. "
                    "Pit in 3-5 laps under less optimal conditions."
                )
            }
    
    def _extract_key_metrics(self, state: RaceState) -> Dict:
        """Extract key metrics for explanation."""
        return {
            'lap_number': state.lap_number,
            'total_laps': state.total_laps,
            'race_progress': f"{state.lap_number / state.total_laps:.1%}",
            'position': state.current_position,
            'tire_age': state.tire_age,
            'tire_degradation': round(state.tire_degradation, 3),
            'gap_to_ahead': round(state.gap_to_ahead, 3),
            'gap_to_leader': round(state.gap_to_leader, 3),
            'fuel_remaining': round(state.fuel_load, 1),
            'track_temperature': round(state.track_temperature, 1)
        }
    
    def _generate_visual_indicators(self, 
                                  state: RaceState,
                                  factors: List[DecisionFactor]) -> Dict:
        """Generate visual indicators for UI."""
        return {
            'urgency_level': 'CRITICAL' if state.safety_car_active else 
                           'HIGH' if state.tire_age > 30 else
                           'MEDIUM' if state.tire_age > 20 else 'LOW',
            'confidence_color': 'green' if state.safety_car_active else
                               'yellow' if state.tire_age > 25 else 'blue',
            'pit_window_indicator': 'OPEN' if state.safety_car_active or state.tire_age > 22 else 'CLOSED',
            'undercut_opportunity': state.gap_to_ahead < 2.0 and state.gap_to_ahead > 0,
            'defensive_required': state.gap_to_behind < 1.5
        }
    
    def answer_question(self, 
                     question: str, 
                     explanation: StrategyExplanation) -> str:
        """
        Answer specific questions about a strategy decision.
        
        Args:
            question: Natural language question
            explanation: The strategy explanation context
            
        Returns:
            Answer string
        """
        question_lower = question.lower()
        
        if 'why' in question_lower and 'this' in question_lower:
            return explanation.primary_reasoning
        
        if 'alternative' in question_lower or 'else' in question_lower:
            if explanation.alternatives_considered:
                alt = explanation.alternatives_considered[0]
                return (
                    f"Alternative considered: {alt.option_name}. "
                    f"{alt.why_rejected} Expected outcome: {alt.expected_outcome}"
                )
            return "No significant alternatives were competitive with this recommendation."
        
        if 'risk' in question_lower:
            return (
                f"Risk if we execute: {explanation.risk_if_executed['summary']}\n"
                f"Risk if we don't: {explanation.risk_if_not_executed['summary']}"
            )
        
        if 'worst' in question_lower or 'bad' in question_lower:
            return explanation.worst_case_scenario
        
        if 'best' in question_lower or 'good' in question_lower:
            return explanation.best_case_scenario
        
        if 'confident' in question_lower or 'confidence' in question_lower:
            return f"Confidence level: {explanation.confidence:.0%}. Based on {len(explanation.decision_factors)} key factors."
        
        return (
            "I can answer questions about: why this decision was made, "
            "alternatives considered, risk analysis, best/worst case scenarios, "
            "or confidence level. What would you like to know?"
        )


def generate_sample_explanation() -> Dict:
    """Generate a sample explanation for testing."""
    xai = ExplainableAIEngine()
    
    # Create sample state
    from app.models.rl_strategy_engine import RaceState
    
    state = RaceState(
        lap_number=24,
        total_laps=53,
        tire_age=23,
        tire_compound=0,  # soft
        current_position=3,
        gap_to_ahead=1.3,
        gap_to_behind=2.1,
        gap_to_leader=8.5,
        weather_condition=0,
        track_temperature=38.0,
        safety_car_active=False,
        fuel_load=28.0,
        tire_degradation=2.8,
        track_evolution=0.024
    )
    
    # Mock recommendations
    rl_rec = {
        'action_name': 'PIT_SOFT',
        'confidence': 0.85,
        'should_pit': True,
        'recommended_tire': 'soft'
    }
    
    opt_rec = {
        'pit_laps': [25, 42],
        'tires': ['soft', 'medium', 'hard'],
        'explanation': 'Optimal 2-stop strategy for Monza'
    }
    
    # Generate explanation
    explanation = xai.explain_strategy_decision(state, rl_rec, opt_rec)
    
    return explanation.to_dict()


if __name__ == "__main__":
    # Test explainable AI
    print("Testing Explainable AI Engine")
    print("=" * 60)
    
    sample = generate_sample_explanation()
    
    print("\n1. Explanation Structure")
    print(f"   ID: {sample['explanation_id']}")
    print(f"   Decision Type: {sample['decision_type']}")
    print(f"   Recommended: {sample['recommended_action']}")
    print(f"   Confidence: {sample['confidence']:.0%}")
    
    print("\n2. Primary Reasoning")
    print(f"   {sample['primary_reasoning']}")
    
    print("\n3. Key Decision Factors")
    for factor in sample['decision_factors'][:3]:
        print(f"   • {factor['factor_name']} ({factor['category']}): "
              f"{factor['description'][:50]}...")
    
    print("\n4. Risk Analysis")
    print(f"   If executed: {sample['risk_analysis']['if_executed']['summary']}")
    print(f"   If not executed: {sample['risk_analysis']['if_not_executed']['summary']}")
    
    print("\n5. Scenarios")
    print(f"   Best case: {sample['scenarios']['best_case'][:60]}...")
    print(f"   Worst case: {sample['scenarios']['worst_case'][:60]}...")
    
    print("\n6. Natural Language Output")
    from app.models.rl_strategy_engine import RaceState
    xai = ExplainableAIEngine()
    state = RaceState(24, 53, 23, 0, 3, 1.3, 2.1, 8.5, 0, 38.0, False, 28.0, 2.8, 0.024)
    rl_rec = {'action_name': 'PIT_SOFT', 'confidence': 0.85}
    opt_rec = {'pit_laps': [25, 42], 'tires': ['soft', 'medium', 'hard']}
    explanation = xai.explain_strategy_decision(state, rl_rec, opt_rec)
    print(explanation.to_natural_language()[:500] + "...")
    
    print("\n7. Q&A Test")
    print("   Q: Why this decision?")
    print(f"   A: {xai.answer_question('Why this decision?', explanation)[:80]}...")
    
    print("\n" + "=" * 60)
    print("Explainable AI test complete!")
