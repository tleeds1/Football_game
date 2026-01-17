import pygame
import math
from src.constants import (
    PLAYER_RADIUS, PLAYER_MASS, PLAYER_ACCELERATION, PLAYER_MAX_SPEED, PLAYER_FRICTION,
    TEAM_1_COLOR, TEAM_2_COLOR,
    KICK_POWER, KICK_RANGE, BALL_RADIUS
)


class Player:
    """
    HaxBall-style player with inertia-based movement.
    Player slides when keys released, no ball possession.
    """
    
    def __init__(self, x, y, team, player_id):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.team = team
        self.player_id = player_id
        self.radius = PLAYER_RADIUS
        self.mass = PLAYER_MASS
        self.selected = False
        self.color = TEAM_1_COLOR if team == 0 else TEAM_2_COLOR
        
        # Input state
        self.input_dx = 0
        self.input_dy = 0
        
    @property
    def position(self):
        return (self.x, self.y)
    
    @property
    def velocity(self):
        return (self.vx, self.vy)
    
    @property
    def speed(self):
        return math.sqrt(self.vx**2 + self.vy**2)
        
    def set_input(self, dx, dy):
        """
        Set movement input direction.
        Args: dx, dy: -1, 0, or 1 for each axis
        """
        self.input_dx = dx
        self.input_dy = dy
        
    def update(self):
        """Update player with inertia-based physics."""
        # Apply acceleration from input
        if self.input_dx != 0 or self.input_dy != 0:
            # Normalize diagonal input
            length = math.sqrt(self.input_dx**2 + self.input_dy**2)
            if length > 0:
                ax = (self.input_dx / length) * PLAYER_ACCELERATION
                ay = (self.input_dy / length) * PLAYER_ACCELERATION
                self.vx += ax
                self.vy += ay
        
        # Apply friction (slide when no input)
        self.vx *= PLAYER_FRICTION
        self.vy *= PLAYER_FRICTION
        
        # Clamp to max speed
        speed = self.speed
        if speed > PLAYER_MAX_SPEED:
            factor = PLAYER_MAX_SPEED / speed
            self.vx *= factor
            self.vy *= factor
        
        # Stop if very slow
        if abs(self.vx) < 0.01:
            self.vx = 0
        if abs(self.vy) < 0.01:
            self.vy = 0
            
        # Update position
        self.x += self.vx
        self.y += self.vy
        
    def distance_to(self, x, y):
        """Calculate distance to a point."""
        return math.sqrt((self.x - x)**2 + (self.y - y)**2)
    
    def can_kick(self, ball):
        """Check if close enough to kick the ball."""
        dist = self.distance_to(ball.x, ball.y)
        return dist <= KICK_RANGE
    
    def kick_ball(self, ball):
        """
        Apply kick impulse to ball.
        Direction = from player center to ball center.
        """
        if not self.can_kick(ball):
            return False
            
        # Direction from player to ball
        dx = ball.x - self.x
        dy = ball.y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        
        if dist > 0:
            # Normalize and apply kick power
            nx = dx / dist
            ny = dy / dist
            
            # Add player velocity to kick for more power when running
            ball.vx += nx * KICK_POWER + self.vx * 0.5
            ball.vy += ny * KICK_POWER + self.vy * 0.5
            
        return True
        
    def draw(self, screen):
        """Draw the player."""
        # Kick range indicator (gray circle) - only for selected player
        if self.selected:
            from src.constants import KICK_RANGE, KICK_RANGE_COLOR
            pygame.draw.circle(screen, KICK_RANGE_COLOR, 
                             (int(self.x), int(self.y)), 
                             int(KICK_RANGE), 1)  # 1 = thin border
        
        # Player body
        pygame.draw.circle(screen, self.color, 
                         (int(self.x), int(self.y)), 
                         self.radius)
        
        # Outline - yellow if selected, white otherwise
        outline_color = (255, 255, 0) if self.selected else (255, 255, 255)
        pygame.draw.circle(screen, outline_color, 
                         (int(self.x), int(self.y)), 
                         self.radius, 2)
        
        # Player number
        font = pygame.font.Font(None, 18)
        text = font.render(str(self.player_id + 1), True, (255, 255, 255))
        text_rect = text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(text, text_rect)
        
    def reset(self, x, y):
        """Reset player to position."""
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.input_dx = 0
        self.input_dy = 0
