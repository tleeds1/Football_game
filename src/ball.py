import pygame
import math
from src.constants import (
    BALL_RADIUS, BALL_COLOR, BALL_FRICTION, BALL_MAX_SPEED, BALL_BOUNCE,
    BALL_START_POS, BALL_MASS
)


class Ball:
    """
    HaxBall-style ball - pure physics object.
    No ownership, just velocity and collisions.
    """
    
    def __init__(self, x=None, y=None):
        if x is None:
            x = BALL_START_POS[0]
        if y is None:
            y = BALL_START_POS[1]
            
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.radius = BALL_RADIUS
        self.mass = BALL_MASS
        self.color = BALL_COLOR
        
    @property
    def position(self):
        return (self.x, self.y)
        
    @property
    def speed(self):
        return math.sqrt(self.vx**2 + self.vy**2)
        
    def update(self):
        """Update ball physics."""
        # Apply friction
        self.vx *= BALL_FRICTION
        self.vy *= BALL_FRICTION
        
        # Clamp max speed
        speed = self.speed
        if speed > BALL_MAX_SPEED:
            factor = BALL_MAX_SPEED / speed
            self.vx *= factor
            self.vy *= factor
        
        # Stop if very slow
        if abs(self.vx) < 0.05:
            self.vx = 0
        if abs(self.vy) < 0.05:
            self.vy = 0
            
        # Update position
        self.x += self.vx
        self.y += self.vy
        
    def apply_impulse(self, fx, fy):
        """Apply an impulse force to the ball."""
        self.vx += fx / self.mass
        self.vy += fy / self.mass
        
    def draw(self, screen):
        """Draw the ball."""
        # Shadow
        pygame.draw.circle(screen, (30, 30, 30),
                         (int(self.x) + 2, int(self.y) + 2),
                         self.radius)
        
        # Ball
        pygame.draw.circle(screen, self.color,
                         (int(self.x), int(self.y)),
                         self.radius)
        
        # Highlight
        pygame.draw.circle(screen, (255, 255, 255),
                         (int(self.x) - 1, int(self.y) - 1),
                         max(2, self.radius // 3))
        
    def reset(self, x=None, y=None):
        """Reset ball to starting position."""
        if x is None:
            x = BALL_START_POS[0]
        if y is None:
            y = BALL_START_POS[1]
            
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
