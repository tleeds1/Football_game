"""
HaxBall Gymnasium Environment for RL Training.
2v2 game simulation with smarter opponent AI.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import math
import random

from src.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    FIELD_LEFT, FIELD_RIGHT, FIELD_TOP, FIELD_BOTTOM,
    GOAL_TOP, GOAL_BOTTOM,
    PLAYER_RADIUS, BALL_RADIUS,
    KICK_RANGE, KICK_POWER,
    RL_MAX_EPISODE_STEPS,
    TEAM_1_POSITIONS, TEAM_2_POSITIONS
)
from src.player import Player
from src.ball import Ball
from src.physics import PhysicsEngine


class HaxBallEnv(gym.Env):
    """
    Custom Gymnasium environment for HaxBall 2v2.
    
    Agent controls the PRIMARY player (closest to ball).
    Secondary teammate uses rule-based AI.
    
    Observation: 17-dimensional vector
    - Ball position (2) + velocity (2)
    - Agent position (2) + velocity (2)  
    - Teammate position (2)
    - Opponent goal position (2)
    - Nearest opponent position (2)
    - Distance to ball (1)
    - Is agent primary? (1)
    - Ball possession (1) - who has the ball
    
    Action: MultiDiscrete([3, 3, 2])
    - move_x: 0=left, 1=none, 2=right
    - move_y: 0=up, 1=none, 2=down
    - kick: 0=no, 1=yes
    """
    
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}
    
    def __init__(self, render_mode=None, team=0):
        super().__init__()
        
        self.render_mode = render_mode
        self.team = team  # 0 = red (left), 1 = blue (right)
        
        # Observation space: normalized values [-1, 1]
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(17,), dtype=np.float32
        )
        
        # Action space: [move_x, move_y, kick]
        self.action_space = spaces.MultiDiscrete([3, 3, 2])
        
        # Game objects
        self.players = []
        self.ball = None
        self.physics = PhysicsEngine()
        
        # Episode tracking
        self.steps = 0
        self.score = [0, 0]
        self.prev_ball_dist_to_goal = 0
        self.prev_agent_dist_to_ball = 0
        
        # Ball stall detection (penalty for stuck ball)
        self.prev_ball_x = 0
        self.prev_ball_y = 0
        self.ball_stall_counter = 0
        
    def _normalize_x(self, x):
        return (x - SCREEN_WIDTH / 2) / (SCREEN_WIDTH / 2)
    
    def _normalize_y(self, y):
        return (y - SCREEN_HEIGHT / 2) / (SCREEN_HEIGHT / 2)
    
    def _normalize_vel(self, v, max_v=15):
        return np.clip(v / max_v, -1, 1)
    
    def _get_opponent_goal_pos(self):
        if self.team == 0:
            return FIELD_RIGHT, (GOAL_TOP + GOAL_BOTTOM) / 2
        else:
            return FIELD_LEFT, (GOAL_TOP + GOAL_BOTTOM) / 2
    
    def _get_own_goal_pos(self):
        if self.team == 0:
            return FIELD_LEFT, (GOAL_TOP + GOAL_BOTTOM) / 2
        else:
            return FIELD_RIGHT, (GOAL_TOP + GOAL_BOTTOM) / 2
    
    def _get_team_players(self):
        return [p for p in self.players if p.team == self.team]
    
    def _get_opponents(self):
        return [p for p in self.players if p.team != self.team]
    
    def _get_agent(self):
        """Get the agent's controlled player (closest to ball)."""
        team_players = self._get_team_players()
        if not team_players:
            return None
        
        # Agent controls closest player to ball
        team_players.sort(key=lambda p: math.sqrt((p.x - self.ball.x)**2 + (p.y - self.ball.y)**2))
        return team_players[0]
    
    def _get_teammate(self):
        """Get teammate (not the agent)."""
        team_players = self._get_team_players()
        if len(team_players) < 2:
            return None
        
        agent = self._get_agent()
        for p in team_players:
            if p != agent:
                return p
        return None
    
    def _get_nearest_opponent(self):
        agent = self._get_agent()
        if not agent:
            return None
            
        opponents = self._get_opponents()
        if not opponents:
            return None
            
        return min(opponents, key=lambda p: math.sqrt((p.x - agent.x)**2 + (p.y - agent.y)**2))
    
    def _get_ball_possession(self):
        """Return who has ball: 0=nobody, 1=our team, -1=opponent"""
        for p in self.players:
            dist = math.sqrt((p.x - self.ball.x)**2 + (p.y - self.ball.y)**2)
            if dist < KICK_RANGE:
                return 1.0 if p.team == self.team else -1.0
        return 0.0
    
    def _get_obs(self):
        agent = self._get_agent()
        teammate = self._get_teammate()
        opponent = self._get_nearest_opponent()
        goal_x, goal_y = self._get_opponent_goal_pos()
        
        dist_to_ball = math.sqrt(
            (agent.x - self.ball.x)**2 + (agent.y - self.ball.y)**2
        ) if agent else 200
        
        obs = np.array([
            self._normalize_x(self.ball.x),
            self._normalize_y(self.ball.y),
            self._normalize_vel(self.ball.vx),
            self._normalize_vel(self.ball.vy),
            self._normalize_x(agent.x) if agent else 0,
            self._normalize_y(agent.y) if agent else 0,
            self._normalize_vel(agent.vx) if agent else 0,
            self._normalize_vel(agent.vy) if agent else 0,
            self._normalize_x(teammate.x) if teammate else 0,
            self._normalize_y(teammate.y) if teammate else 0,
            self._normalize_x(goal_x),
            self._normalize_y(goal_y),
            self._normalize_x(opponent.x) if opponent else 0,
            self._normalize_y(opponent.y) if opponent else 0,
            np.clip(dist_to_ball / 200, 0, 1),
            1.0,  # Agent is always primary
            self._get_ball_possession(),
        ], dtype=np.float32)
        
        return obs
    
    def _get_info(self):
        return {"score": self.score.copy(), "steps": self.steps}
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.steps = 0
        self.score = [0, 0]
        
        # Create 2v2 players
        self.players = []
        
        # Team 0 (Red - left side)
        for i, pos in enumerate(TEAM_1_POSITIONS):
            p = Player(pos[0], pos[1], team=0, player_id=i)
            self.players.append(p)
        
        # Team 1 (Blue - right side)
        for i, pos in enumerate(TEAM_2_POSITIONS):
            p = Player(pos[0], pos[1], team=1, player_id=i)
            self.players.append(p)
        
        # Ball at center with small random offset
        self.ball = Ball()
        self.ball.x += random.uniform(-20, 20)
        self.ball.y += random.uniform(-20, 20)
        
        # Track initial distances
        goal_x, _ = self._get_opponent_goal_pos()
        self.prev_ball_dist_to_goal = abs(self.ball.x - goal_x)
        agent = self._get_agent()
        if agent:
            self.prev_agent_dist_to_ball = math.sqrt(
                (agent.x - self.ball.x)**2 + (agent.y - self.ball.y)**2
            )
        
        # Reset stall tracking
        self.prev_ball_x = self.ball.x
        self.prev_ball_y = self.ball.y
        self.ball_stall_counter = 0
        
        return self._get_obs(), self._get_info()
    
    def step(self, action):
        self.steps += 1
        
        # Decode action
        move_x = int(action[0]) - 1
        move_y = int(action[1]) - 1
        kick = int(action[2]) == 1
        
        # Apply action to agent (primary player on our team)
        agent = self._get_agent()
        if agent:
            agent.set_input(move_x, move_y)
            if kick and agent.can_kick(self.ball):
                agent.kick_ball(self.ball)
        
        # Teammate AI (secondary player on our team)
        teammate = self._get_teammate()
        if teammate:
            self._control_teammate(teammate, agent)
        
        # Opponent AI (both opponent players)
        opponents = self._get_opponents()
        self._control_opponents(opponents)
        
        # Update physics
        for p in self.players:
            p.update()
        self.ball.update()
        goal = self.physics.update(self.players, self.ball)
        
        # Calculate reward
        reward = 0.0
        terminated = False
        truncated = False
        
        # Goal scored/conceded
        if goal > 0:
            if goal == (2 if self.team == 0 else 1):  # We scored
                reward += 50.0
                self.score[self.team] += 1
            else:  # We conceded (OWN GOAL = HEAVY PENALTY)
                reward -= 200.0  # Heavy penalty for own goal
                self.score[1 - self.team] += 1
            terminated = True
        
        # Shaping rewards (smaller scale)
        goal_x, _ = self._get_opponent_goal_pos()
        ball_dist_to_goal = abs(self.ball.x - goal_x)
        
        # Ball closer to opponent goal
        if ball_dist_to_goal < self.prev_ball_dist_to_goal:
            reward += 0.05
        elif ball_dist_to_goal > self.prev_ball_dist_to_goal:
            reward -= 0.02
        self.prev_ball_dist_to_goal = ball_dist_to_goal
        
        # Agent closer to ball (encourage chasing)
        if agent:
            agent_dist = math.sqrt((agent.x - self.ball.x)**2 + (agent.y - self.ball.y)**2)
            if agent_dist < self.prev_agent_dist_to_ball:
                reward += 0.02
            self.prev_agent_dist_to_ball = agent_dist
            
            # Possession reward
            if agent_dist < KICK_RANGE:
                reward += 0.01
        
        # Ball stall penalty (prevent stuck ball)
        ball_moved = math.sqrt(
            (self.ball.x - self.prev_ball_x)**2 + 
            (self.ball.y - self.prev_ball_y)**2
        )
        if ball_moved < 3:  # Ball barely moved
            self.ball_stall_counter += 1
            if self.ball_stall_counter > 60:  # Stuck for ~1 second
                reward -= 0.5  # Penalty per frame when stuck
        else:
            self.ball_stall_counter = 0  # Reset if ball moved
        
        self.prev_ball_x = self.ball.x
        self.prev_ball_y = self.ball.y
        
        # Penalty for dribbling backwards (ball moving towards own goal)
        own_goal_x, _ = self._get_own_goal_pos()
        if self.team == 0:  # Red, own goal on left
            if self.ball.vx < -2 and self.ball.x < SCREEN_WIDTH / 2:
                reward -= 0.1  # Penalize ball going left in our half
        else:  # Blue, own goal on right
            if self.ball.vx > 2 and self.ball.x > SCREEN_WIDTH / 2:
                reward -= 0.1  # Penalize ball going right in our half
        
        # Timeout penalty
        if self.steps >= RL_MAX_EPISODE_STEPS:
            truncated = True
            reward -= 5.0
        
        return self._get_obs(), reward, terminated, truncated, self._get_info()
    
    def _control_teammate(self, teammate, agent):
        """Rule-based AI for teammate - support/defend."""
        own_goal_x, own_goal_y = self._get_own_goal_pos()
        
        # Decide role based on ball position
        if self.team == 0:
            ball_in_our_half = self.ball.x < SCREEN_WIDTH / 2
        else:
            ball_in_our_half = self.ball.x > SCREEN_WIDTH / 2
        
        if ball_in_our_half:
            # Defend: stay between ball and goal
            target_x = own_goal_x + (self.ball.x - own_goal_x) * 0.4
            target_y = own_goal_y + (self.ball.y - own_goal_y) * 0.4
        else:
            # Support: stay behind agent but offset vertically
            if self.team == 0:
                target_x = max(SCREEN_WIDTH * 0.4, agent.x - 100)
            else:
                target_x = min(SCREEN_WIDTH * 0.6, agent.x + 100)
            
            if agent.y < SCREEN_HEIGHT / 2:
                target_y = min(FIELD_BOTTOM - 50, SCREEN_HEIGHT / 2 + 50)
            else:
                target_y = max(FIELD_TOP + 50, SCREEN_HEIGHT / 2 - 50)
        
        dx = target_x - teammate.x
        dy = target_y - teammate.y
        teammate.set_input(
            1 if dx > 20 else -1 if dx < -20 else 0,
            1 if dy > 20 else -1 if dy < -20 else 0
        )
        
        if teammate.can_kick(self.ball):
            teammate.kick_ball(self.ball)
    
    def _control_opponents(self, opponents):
        """Rule-based AI for opponents - similar to our teammate logic."""
        if not opponents:
            return
        
        # Sort by distance to ball
        opponents.sort(key=lambda p: math.sqrt((p.x - self.ball.x)**2 + (p.y - self.ball.y)**2))
        
        # Primary opponent chases ball
        primary = opponents[0]
        dx = self.ball.x - primary.x
        dy = self.ball.y - primary.y
        primary.set_input(
            1 if dx > 5 else -1 if dx < -5 else 0,
            1 if dy > 5 else -1 if dy < -5 else 0
        )
        if primary.can_kick(self.ball):
            primary.kick_ball(self.ball)
        
        # Secondary opponent defends/supports
        if len(opponents) > 1:
            secondary = opponents[1]
            opp_team = 1 - self.team
            
            if opp_team == 0:
                own_goal_x = FIELD_LEFT
                ball_in_their_half = self.ball.x < SCREEN_WIDTH / 2
            else:
                own_goal_x = FIELD_RIGHT
                ball_in_their_half = self.ball.x > SCREEN_WIDTH / 2
            
            own_goal_y = (GOAL_TOP + GOAL_BOTTOM) / 2
            
            if ball_in_their_half:
                target_x = own_goal_x + (self.ball.x - own_goal_x) * 0.4
                target_y = own_goal_y + (self.ball.y - own_goal_y) * 0.4
            else:
                if opp_team == 0:
                    target_x = max(SCREEN_WIDTH * 0.4, primary.x - 100)
                else:
                    target_x = min(SCREEN_WIDTH * 0.6, primary.x + 100)
                
                if primary.y < SCREEN_HEIGHT / 2:
                    target_y = SCREEN_HEIGHT / 2 + 50
                else:
                    target_y = SCREEN_HEIGHT / 2 - 50
            
            dx = target_x - secondary.x
            dy = target_y - secondary.y
            secondary.set_input(
                1 if dx > 20 else -1 if dx < -20 else 0,
                1 if dy > 20 else -1 if dy < -20 else 0
            )
            if secondary.can_kick(self.ball):
                secondary.kick_ball(self.ball)
    
    def render(self):
        pass
    
    def close(self):
        pass
