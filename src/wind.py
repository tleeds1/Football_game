"""
Wind system for HaxBall-style game.
Wind affects ball physics with random direction and magnitude.
Cycles: 15s wind -> 5s calm -> repeat
"""

import math
import random
import pygame
from src.constants import WIND_MAX_FORCE, WIND_DURATION, WIND_CALM_DURATION


class Wind:
    """
    Wind system that affects ball movement.
    - Random direction and magnitude (up to WIND_MAX_FORCE)
    - Cycles between active (15s) and calm (5s) periods
    """
    
    def __init__(self):
        self.vx = 0.0
        self.vy = 0.0
        self.magnitude = 0.0
        self.angle = 0.0  # In radians
        self.is_active = True
        self.state_start_time = pygame.time.get_ticks()
        
        # Generate initial wind
        self._generate_wind()
    
    def _generate_wind(self):
        """Generate random wind direction and magnitude."""
        self.angle = random.uniform(0, 2 * math.pi)
        self.magnitude = random.uniform(WIND_MAX_FORCE * 0.3, WIND_MAX_FORCE)
        
        self.vx = math.cos(self.angle) * self.magnitude
        self.vy = math.sin(self.angle) * self.magnitude
    
    def update(self):
        """Update wind state (active/calm cycle)."""
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.state_start_time
        
        if self.is_active:
            # Wind is active, check if should become calm
            if elapsed >= WIND_DURATION:
                self.is_active = False
                self.state_start_time = current_time
                self.vx = 0
                self.vy = 0
                self.magnitude = 0
        else:
            # Wind is calm, check if should become active
            if elapsed >= WIND_CALM_DURATION:
                self.is_active = True
                self.state_start_time = current_time
                self._generate_wind()
    
    def apply(self, ball):
        """Apply wind force to ball."""
        if self.is_active and self.magnitude > 0:
            # Wind force is applied as acceleration (scaled down for smooth effect)
            wind_factor = 0.01  # Scale factor for wind influence
            ball.vx += self.vx * wind_factor
            ball.vy += self.vy * wind_factor
    
    def get_time_remaining(self):
        """Get time remaining in current state (ms)."""
        elapsed = pygame.time.get_ticks() - self.state_start_time
        if self.is_active:
            return max(0, WIND_DURATION - elapsed)
        else:
            return max(0, WIND_CALM_DURATION - elapsed)
