"""
F1 Strategy Intelligence System - Elite Edition v3.1
Reinforcement Learning Strategy Engine

Implements Deep Q-Network (DQN) and rule-based Q-Learning for adaptive pit
strategy decisions.

Production design:
  - PyTorch is imported lazily — the engine starts in rule-based (Q-table) mode
    if torch is unavailable or fails to load.
  - The public API (predict, act) is identical regardless of backend.
  - All torch operations are guarded — no ImportError crashes the backend.
"""
import logging
import os
import pickle
import random
from collections import deque, namedtuple
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from app.core.config import CIRCUITS
from app.services.multi_car_simulator import MultiCarSimulator

logger = logging.getLogger(__name__)

# ── PyTorch — lazy optional import ────────────────────────────────────────────
_TORCH_AVAILABLE = False
torch = None  # noqa: N816 — module-level alias

def _try_import_torch():
    """Attempt to import PyTorch (CPU-only in production). Thread-safe."""
    global torch, _TORCH_AVAILABLE  # noqa: PLW0603
    if _TORCH_AVAILABLE:
        return True
    try:
        import torch as _torch          # type: ignore[import]
        import torch.nn as _nn          # noqa: F401  — pre-warm
        import torch.optim as _optim    # noqa: F401
        torch = _torch
        _TORCH_AVAILABLE = True
        logger.info("[RL] PyTorch loaded successfully (device: CPU)")
        return True
    except ImportError:
        logger.warning("[RL] PyTorch not available — using rule-based Q-table fallback")
        return False
    except Exception as exc:
        logger.warning(f"[RL] PyTorch import failed ({exc}) — using Q-table fallback")
        return False


# Attempt import at module load time (non-fatal)
_try_import_torch()

# Named tuple for experience replay
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])


# ── State Representation ──────────────────────────────────────────────────────

@dataclass
class RaceState:
    """Complete state representation for RL agent."""
    lap_number: int
    total_laps: int
    tire_age: int
    tire_compound: int  # 0=soft, 1=medium, 2=hard, 3=inter, 4=wet
    current_position: int
    gap_to_ahead: float   # seconds
    gap_to_behind: float  # seconds
    gap_to_leader: float  # seconds
    weather_condition: int  # 0=dry, 1=light_rain, 2=heavy_rain
    track_temperature: float
    safety_car_active: bool
    fuel_load: float        # kg remaining
    tire_degradation: float # seconds lost per lap due to tires
    track_evolution: float  # grip improvement

    def to_array(self) -> np.ndarray:
        """Convert state to numpy array for neural network / Q-table input."""
        return np.array([
            self.lap_number / max(self.total_laps, 1),
            self.tire_age / 60,
            self.tire_compound / 4,
            self.current_position / 20,
            np.clip(self.gap_to_ahead / 30, -1, 1),
            np.clip(self.gap_to_behind / 30, -1, 1),
            np.clip(self.gap_to_leader / 60, 0, 2),
            self.weather_condition / 2,
            (self.track_temperature - 20) / 40,
            1.0 if self.safety_car_active else 0.0,
            self.fuel_load / 100,
            self.tire_degradation / 5,
            self.track_evolution / 0.5,
        ], dtype=np.float32)


# ── DQN Network (only built when torch is available) ──────────────────────────

def _build_dqn_network(state_size: int, action_size: int, hidden_size: int = 128):
    """
    Build a DQN network using PyTorch. Returns None if torch unavailable.
    """
    if not _TORCH_AVAILABLE:
        return None
    try:
        import torch.nn as nn  # type: ignore[import]

        class _DQNNetwork(nn.Module):
            def __init__(self):
                super().__init__()
                self.fc1 = nn.Linear(state_size, hidden_size)
                self.fc2 = nn.Linear(hidden_size, hidden_size // 2)
                self.fc3 = nn.Linear(hidden_size // 2, hidden_size // 4)
                self.fc4 = nn.Linear(hidden_size // 4, action_size)
                self.dropout = nn.Dropout(0.2)

            def forward(self, x):
                x = torch.relu(self.fc1(x))
                x = self.dropout(x)
                x = torch.relu(self.fc2(x))
                x = self.dropout(x)
                x = torch.relu(self.fc3(x))
                return self.fc4(x)

        return _DQNNetwork()
    except Exception as exc:
        logger.warning(f"[RL] DQN network build failed: {exc} — falling back to Q-table")
        return None


# ── RL Strategy Engine ────────────────────────────────────────────────────────

class RLStrategyEngine:
    """
    Elite RL Strategy Engine with DQN and Q-Learning capabilities.

    Automatically degrades gracefully:
      - If PyTorch is available: uses DQN (neural network).
      - If PyTorch is unavailable: uses rule-based Q-table (no crash).

    The predict() and act() public API is identical in both modes.
    """

    ACTIONS = [
        'STAY_OUT',
        'PIT_SOFT',
        'PIT_MEDIUM',
        'PIT_HARD',
        'PIT_INTERMEDIATE',
    ]

    TIRE_MAP = {'soft': 0, 'medium': 1, 'hard': 2, 'intermediate': 3, 'wet': 4}
    REVERSE_TIRE_MAP = {v: k for k, v in TIRE_MAP.items()}

    def __init__(
        self,
        state_size: int = 13,
        action_size: int = 5,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon: float = 1.0,
        epsilon_min: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_size: int = 100_000,
        batch_size: int = 64,
        target_update: int = 1_000,
        use_dqn: bool = True,
    ):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update = target_update
        self.memory: deque = deque(maxlen=buffer_size)
        self.training_step = 0
        self.episode_rewards: List[float] = []
        self.episode_lengths: List[int] = []
        self.win_rate: List[int] = []

        # Decide actual backend: DQN or Q-table
        self._using_dqn = use_dqn and _TORCH_AVAILABLE
        self.use_dqn = self._using_dqn  # backward-compat attribute

        if self._using_dqn:
            try:
                self.device = torch.device("cpu")  # CPU-only in production
                self.policy_net = _build_dqn_network(state_size, action_size)
                self.target_net = _build_dqn_network(state_size, action_size)

                if self.policy_net is None or self.target_net is None:
                    raise RuntimeError("DQN network build returned None")

                self.policy_net = self.policy_net.to(self.device)
                self.target_net = self.target_net.to(self.device)
                self.target_net.load_state_dict(self.policy_net.state_dict())
                self.target_net.eval()

                import torch.nn as nn
                import torch.optim as optim
                self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
                self.criterion = nn.MSELoss()
                logger.info("[RL] DQN engine initialized (CPU mode)")
            except Exception as exc:
                logger.warning(f"[RL] DQN init failed ({exc}) — switching to Q-table fallback")
                self._using_dqn = False
                self.use_dqn = False

        if not self._using_dqn:
            self.q_table: Dict = {}
            logger.info("[RL] Q-table (rule-based) engine initialized")

    # ── Core Action Selection ─────────────────────────────────────────────────

    def get_state_key(self, state: RaceState) -> tuple:
        """Discretise continuous state into Q-table key."""
        return (
            int(state.lap_number / 5),
            int(state.tire_age / 5),
            state.tire_compound,
            state.current_position,
            int(state.weather_condition),
            int(state.track_temperature / 10),
            1 if state.safety_car_active else 0,
        )

    def act(self, state: RaceState, training: bool = False) -> int:
        """
        Select action using epsilon-greedy policy.
        Works identically in DQN and Q-table modes.
        """
        if training and random.random() <= self.epsilon:
            return random.randrange(self.action_size)

        if self._using_dqn:
            try:
                with torch.no_grad():
                    state_tensor = torch.FloatTensor(state.to_array()).unsqueeze(0).to(self.device)
                    q_values = self.policy_net(state_tensor)
                    return int(q_values.argmax().item())
            except Exception as exc:
                logger.warning(f"[RL] DQN act() failed ({exc}) — using Q-table fallback")

        # Q-table path (also used as DQN fallback)
        state_key = self.get_state_key(state)
        q_values = self.q_table.get(state_key, np.zeros(self.action_size))
        return int(np.argmax(q_values))

    def remember(self, state: RaceState, action: int, reward: float,
                 next_state: RaceState, done: bool):
        """Store experience in replay buffer."""
        self.memory.append(Experience(
            state.to_array(), action, reward, next_state.to_array(), done
        ))

    def replay(self) -> Optional[float]:
        """Train on batch of experiences (DQN mode only)."""
        if not self._using_dqn or len(self.memory) < self.batch_size:
            return None
        try:
            batch = random.sample(self.memory, self.batch_size)
            states = torch.FloatTensor([e.state for e in batch]).to(self.device)
            actions = torch.LongTensor([e.action for e in batch]).to(self.device)
            rewards = torch.FloatTensor([e.reward for e in batch]).to(self.device)
            next_states = torch.FloatTensor([e.next_state for e in batch]).to(self.device)
            dones = torch.FloatTensor([e.done for e in batch]).to(self.device)

            current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))

            with torch.no_grad():
                next_actions = self.policy_net(next_states).argmax(1)
                next_q = self.target_net(next_states).gather(
                    1, next_actions.unsqueeze(1)
                ).squeeze(1)
                target_q = rewards + (1 - dones) * self.gamma * next_q

            loss = self.criterion(current_q.squeeze(), target_q)
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            self.training_step += 1
            if self.training_step % self.target_update == 0:
                self.target_net.load_state_dict(self.policy_net.state_dict())

            return float(loss.item())
        except Exception as exc:
            logger.warning(f"[RL] replay() failed: {exc}")
            return None

    def update_q_table(self, state: RaceState, action: int, reward: float,
                       next_state: RaceState, done: bool):
        """Update Q-table for Q-learning mode."""
        state_key = self.get_state_key(state)
        next_key = self.get_state_key(next_state)

        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.action_size)
        if next_key not in self.q_table:
            self.q_table[next_key] = np.zeros(self.action_size)

        current_q = self.q_table[state_key][action]
        next_max_q = float(np.max(self.q_table[next_key])) if not done else 0.0
        self.q_table[state_key][action] = current_q + self.learning_rate * (
            reward + self.gamma * next_max_q - current_q
        )

    def decay_epsilon(self):
        """Decay exploration rate."""
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    # ── Reward Calculation ────────────────────────────────────────────────────

    def calculate_reward(
        self,
        prev_state: RaceState,
        new_state: RaceState,
        action: int,
        race_completed: bool = False,
        final_position: int = None,
        total_time: float = None,
    ) -> float:
        """Calculate reward for state transition."""
        reward = 0.0

        # Position improvement
        reward += (prev_state.current_position - new_state.current_position) * 10.0

        # Gap to leader improvement
        reward += (prev_state.gap_to_leader - new_state.gap_to_leader) * 0.5

        # Undercut range bonus
        if new_state.gap_to_ahead < 2.0 and prev_state.gap_to_ahead >= 2.0:
            reward += 5.0

        # Pit action evaluation
        if action > 0:
            reward += 3.0 if prev_state.tire_age > 25 else -2.0
            if prev_state.safety_car_active:
                reward += 5.0
            if prev_state.weather_condition == 0 and action == 1:
                if prev_state.lap_number < prev_state.total_laps * 0.3:
                    reward += 2.0
                elif prev_state.lap_number > prev_state.total_laps * 0.7:
                    reward -= 1.0

        # Tire degradation penalty
        if new_state.tire_degradation > 2.0:
            reward -= 1.0

        # Race completion bonus
        if race_completed:
            position_bonus = {1: 100, 2: 50, 3: 25, 4: 10, 5: 5}
            reward += position_bonus.get(final_position, 0)
            if total_time and total_time < 5000:
                reward += (5000 - total_time) / 100

        return reward

    # ── Training ──────────────────────────────────────────────────────────────

    def train_episode(self, circuit: str = 'Monza', total_laps: int = 53) -> Dict:
        """Train for one complete race episode."""
        simulator = MultiCarSimulator(circuit, total_laps, num_cars=5)
        simulator.initialize_race(weather='dry')
        agent_driver = simulator.drivers[0]

        episode_reward = 0.0
        steps = 0

        for lap in range(1, total_laps + 1):
            ahead = [d for d in simulator.drivers if d.position == agent_driver.position - 1]
            behind = [d for d in simulator.drivers if d.position == agent_driver.position + 1]
            ahead_gap = (ahead[0].gap_to_leader - agent_driver.gap_to_leader) if ahead else 0.0
            behind_gap = (agent_driver.gap_to_leader - behind[0].gap_to_leader) if behind else 0.0

            current_state = RaceState(
                lap_number=lap, total_laps=total_laps,
                tire_age=agent_driver.tire_age,
                tire_compound=self.TIRE_MAP.get(agent_driver.current_tire, 0),
                current_position=agent_driver.position,
                gap_to_ahead=ahead_gap, gap_to_behind=behind_gap,
                gap_to_leader=agent_driver.gap_to_leader,
                weather_condition=0, track_temperature=35.0,
                safety_car_active=False,
                fuel_load=50.0 * (1 - lap / total_laps),
                tire_degradation=agent_driver.tire_age * 0.05,
                track_evolution=lap * 0.001,
            )

            action = self.act(current_state, training=True)

            if action > 0:
                new_tire = self.REVERSE_TIRE_MAP.get(action - 1, 'medium')
                simulator.simulate_pit_stop(agent_driver, new_tire)

            simulator.simulate_lap()

            new_ahead = [d for d in simulator.drivers if d.position == agent_driver.position - 1]
            new_behind = [d for d in simulator.drivers if d.position == agent_driver.position + 1]
            new_ahead_gap = (new_ahead[0].gap_to_leader - agent_driver.gap_to_leader) if new_ahead else 0.0
            new_behind_gap = (agent_driver.gap_to_leader - new_behind[0].gap_to_leader) if new_behind else 5.0

            next_state = RaceState(
                lap_number=lap + 1, total_laps=total_laps,
                tire_age=agent_driver.tire_age,
                tire_compound=self.TIRE_MAP.get(agent_driver.current_tire, 0),
                current_position=agent_driver.position,
                gap_to_ahead=new_ahead_gap, gap_to_behind=new_behind_gap,
                gap_to_leader=agent_driver.gap_to_leader,
                weather_condition=0, track_temperature=35.0,
                safety_car_active=False,
                fuel_load=50.0 * (1 - (lap + 1) / total_laps),
                tire_degradation=agent_driver.tire_age * 0.05,
                track_evolution=(lap + 1) * 0.001,
            )

            reward = self.calculate_reward(
                current_state, next_state, action,
                race_completed=(lap == total_laps),
                final_position=agent_driver.position,
            )

            if self._using_dqn:
                self.remember(current_state, action, reward, next_state, lap == total_laps)
                if len(self.memory) > self.batch_size:
                    self.replay()
            else:
                self.update_q_table(current_state, action, reward, next_state, lap == total_laps)

            episode_reward += reward
            steps += 1

        self.decay_epsilon()
        self.episode_rewards.append(episode_reward)
        self.episode_lengths.append(steps)
        self.win_rate.append(1 if agent_driver.position == 1 else 0)

        return {
            'episode_reward': episode_reward,
            'final_position': agent_driver.position,
            'epsilon': self.epsilon,
            'steps': steps,
        }

    def train(
        self,
        num_episodes: int = 1000,
        circuits: List[str] = None,
        save_interval: int = 100,
        save_path: str = 'models/rl_strategy',
    ):
        """Train RL agent for multiple episodes."""
        if circuits is None:
            circuits = ['Monza', 'Silverstone', 'Spa']

        Path(save_path).mkdir(parents=True, exist_ok=True)
        backend = 'DQN (CPU)' if self._using_dqn else 'Q-table (rule-based)'
        print(f"Training RL Strategy Agent: {num_episodes} episodes | backend={backend}")

        best_reward = -float('inf')

        for episode in range(num_episodes):
            circuit = random.choice(circuits)
            total_laps = CIRCUITS[circuit]['laps']
            metrics = self.train_episode(circuit, total_laps)

            if (episode + 1) % 10 == 0:
                avg_reward = float(np.mean(self.episode_rewards[-100:]))
                avg_win = float(np.mean(self.win_rate[-100:])) * 100
                print(
                    f"Episode {episode + 1}/{num_episodes} | "
                    f"Reward={metrics['episode_reward']:.1f} | "
                    f"Avg={avg_reward:.1f} | Win={avg_win:.1f}% | ε={self.epsilon:.3f}"
                )

            if metrics['episode_reward'] > best_reward:
                best_reward = metrics['episode_reward']
                self.save(f"{save_path}/best_model.pt")

            if (episode + 1) % save_interval == 0:
                self.save(f"{save_path}/checkpoint_{episode + 1}.pt")

        self.save(f"{save_path}/final_model.pt")
        print(f"\nTraining complete! Best reward: {best_reward:.1f}")

    # ── Prediction (production API) ───────────────────────────────────────────

    def predict(self, state: RaceState) -> Dict:
        """
        Get strategy recommendation for current race state.

        Returns a dict identical in structure regardless of DQN vs Q-table backend.
        """
        action = self.act(state, training=False)
        action_name = self.ACTIONS[action]

        # Get Q-values for confidence calculation
        if self._using_dqn:
            try:
                with torch.no_grad():
                    state_tensor = torch.FloatTensor(state.to_array()).unsqueeze(0).to(self.device)
                    q_values = self.policy_net(state_tensor).cpu().numpy()[0]
            except Exception as exc:
                logger.warning(f"[RL] DQN predict() failed ({exc}) — using Q-table")
                state_key = self.get_state_key(state)
                q_values = self.q_table.get(state_key, np.zeros(self.action_size))
        else:
            state_key = self.get_state_key(state)
            q_values = self.q_table.get(state_key, np.zeros(self.action_size))

        # Softmax confidence
        exp_q = np.exp(q_values - np.max(q_values))
        probs = exp_q / np.sum(exp_q)
        confidence = float(probs[action])

        return {
            'action': action,
            'action_name': action_name,
            'confidence': confidence,
            'q_values': {name: float(val) for name, val in zip(self.ACTIONS, q_values)},
            'explanation': self._generate_explanation(state, action, q_values),
            'should_pit': action > 0,
            'recommended_tire': self.REVERSE_TIRE_MAP.get(action - 1, None) if action > 0 else None,
            'backend': 'dqn_cpu' if self._using_dqn else 'q_table',
        }

    def _generate_explanation(self, state: RaceState, action: int, q_values: np.ndarray) -> str:
        """Generate human-readable explanation for decision."""
        action_name = self.ACTIONS[action]
        reasons = []

        if action == 0:
            if state.tire_age < 15:
                reasons.append("Tires are still fresh")
            if state.gap_to_ahead > 3.0:
                reasons.append("No undercut threat from behind")
            if state.lap_number < state.total_laps * 0.2:
                reasons.append("Too early for optimal pit window")
        else:
            if state.tire_age > 25:
                reasons.append(f"Tires are {state.tire_age} laps old — degradation is high")
            if 0 < state.gap_to_ahead < 2.0:
                reasons.append("Perfect undercut opportunity on car ahead")
            if state.safety_car_active:
                reasons.append("Safety car deployed — optimal pit window")
            if state.tire_degradation > 1.5:
                reasons.append("Tire degradation is costing significant lap time")

        valid_alts = [i for i in range(self.action_size) if i != action]
        best_alt_idx = int(np.argmax([q_values[i] for i in valid_alts]))
        alt_action = valid_alts[best_alt_idx]
        q_diff = float(q_values[action] - q_values[alt_action])

        explanation = f"Recommended: {action_name}."
        if reasons:
            explanation += f" Key factors: {', '.join(reasons)}."
        explanation += f" Q-advantage over best alternative: {q_diff:.2f}."
        return explanation

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, path: str):
        """Save model to disk."""
        if self._using_dqn:
            try:
                torch.save({
                    'policy_net': self.policy_net.state_dict(),
                    'target_net': self.target_net.state_dict(),
                    'optimizer': self.optimizer.state_dict(),
                    'epsilon': self.epsilon,
                    'training_step': self.training_step,
                    'episode_rewards': self.episode_rewards,
                }, path)
            except Exception as exc:
                logger.warning(f"[RL] save() failed: {exc}")
        else:
            pkl_path = path.replace('.pt', '.pkl')
            with open(pkl_path, 'wb') as f:
                pickle.dump({
                    'q_table': self.q_table,
                    'epsilon': self.epsilon,
                    'episode_rewards': self.episode_rewards,
                }, f)

    def load(self, path: str):
        """Load model from disk."""
        if self._using_dqn:
            try:
                checkpoint = torch.load(path, map_location=self.device)
                self.policy_net.load_state_dict(checkpoint['policy_net'])
                self.target_net.load_state_dict(checkpoint['target_net'])
                self.optimizer.load_state_dict(checkpoint['optimizer'])
                self.epsilon = checkpoint['epsilon']
                self.training_step = checkpoint['training_step']
                self.episode_rewards = checkpoint.get('episode_rewards', [])
            except Exception as exc:
                logger.warning(f"[RL] load() failed: {exc}")
        else:
            pkl_path = path.replace('.pt', '.pkl')
            try:
                with open(pkl_path, 'rb') as f:
                    data = pickle.load(f)
                    self.q_table = data['q_table']
                    self.epsilon = data['epsilon']
                    self.episode_rewards = data.get('episode_rewards', [])
            except FileNotFoundError:
                logger.info(f"[RL] No saved Q-table found at {pkl_path} — starting fresh")


# ── Convenience Function ──────────────────────────────────────────────────────

def train_rl_agent(num_episodes: int = 500, save_path: str = 'models/rl_strategy'):
    """Convenience function to train and save RL agent."""
    agent = RLStrategyEngine(use_dqn=True)
    agent.train(num_episodes=num_episodes, save_path=save_path)
    return agent
