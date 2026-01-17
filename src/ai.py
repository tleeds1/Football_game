import math
import random
from src.constants import (
    FIELD_LEFT, FIELD_RIGHT, FIELD_TOP, FIELD_BOTTOM,
    GOAL_TOP, GOAL_BOTTOM, SCREEN_WIDTH, SCREEN_HEIGHT,
    KICK_RANGE
)


class AIController:
    """
    AI controller for computer-controlled team.
    HaxBall style: chase ball, kick when close.
    """
    
    def __init__(self, team):
        self.team = team
        self.selected_player = 0
        self.difficulty = 0.85
        
    def update(self, players, ball):
        """Get AI input for the team."""
        team_players = [p for p in players if p.team == self.team]
        
        if not team_players:
            return {'movement': [0, 0], 'kick': False, 'switch': False}
        
        # Select player closest to ball
        self._select_closest(team_players, ball)
        
        selected = team_players[self.selected_player]
        
        # Chase ball
        movement = self._chase_ball(selected, ball)
        
        # Kick if close
        kick = False
        if selected.can_kick(ball):
            # Check if facing goal direction
            if self.team == 1:
                if ball.x < selected.x:  # Ball is towards our target
                    kick = random.random() < 0.2
            else:
                if ball.x > selected.x:
                    kick = random.random() < 0.2
            
        if random.random() > self.difficulty:
            movement = [0, 0]
            
        return {
            'movement': movement,
            'kick': kick,
            'switch': False
        }
        
    def _select_closest(self, team_players, ball):
        min_dist = float('inf')
        for i, p in enumerate(team_players):
            dist = math.sqrt((p.x - ball.x)**2 + (p.y - ball.y)**2)
            if dist < min_dist:
                min_dist = dist
                self.selected_player = i
                
        for i, p in enumerate(team_players):
            p.selected = (i == self.selected_player)
            
    def _chase_ball(self, player, ball):
        dx = ball.x - player.x
        dy = ball.y - player.y
        
        move_x = 1 if dx > 5 else -1 if dx < -5 else 0
        move_y = 1 if dy > 5 else -1 if dy < -5 else 0
        
        return [move_x, move_y]


class TeammateAI:
    """
    AI for non-selected teammate.
    Provides support positioning.
    """
    
    def __init__(self, team):
        self.team = team
        
    def get_movement_for_player(self, player, ball, all_players):
        """Get movement for teammate."""
        # Find selected teammate
        selected = None
        for p in all_players:
            if p.team == self.team and p.selected:
                selected = p
                break
        
        # If selected has ball nearby, support ahead
        if selected:
            selected_dist = math.sqrt((selected.x - ball.x)**2 + (selected.y - ball.y)**2)
            if selected_dist < 100:
                return self._support_attack(player, selected)
        
        # Defend or chase
        if self._should_defend(ball):
            return self._defend(player, ball)
        else:
            return self._chase_ball(player, ball)
    
    def _should_defend(self, ball):
        if self.team == 0:
            return ball.x < SCREEN_WIDTH / 3
        else:
            return ball.x > 2 * SCREEN_WIDTH / 3
            
    def _support_attack(self, player, selected):
        if self.team == 0:
            target_x = selected.x + 100
            target_x = min(target_x, FIELD_RIGHT - 80)
        else:
            target_x = selected.x - 100
            target_x = max(target_x, FIELD_LEFT + 80)
            
        if player.y < selected.y:
            target_y = selected.y - 80
        else:
            target_y = selected.y + 80
        target_y = max(FIELD_TOP + 30, min(target_y, FIELD_BOTTOM - 30))
        
        dx = target_x - player.x
        dy = target_y - player.y
        
        return (1 if dx > 10 else -1 if dx < -10 else 0,
                1 if dy > 10 else -1 if dy < -10 else 0)
    
    def _defend(self, player, ball):
        if self.team == 0:
            goal_x = FIELD_LEFT
        else:
            goal_x = FIELD_RIGHT
        goal_y = (GOAL_TOP + GOAL_BOTTOM) / 2
        
        target_x = (ball.x + goal_x) / 2
        target_y = (ball.y + goal_y) / 2
        
        if self.team == 0:
            target_x = max(FIELD_LEFT + 50, min(target_x, SCREEN_WIDTH / 3))
        else:
            target_x = min(FIELD_RIGHT - 50, max(target_x, 2 * SCREEN_WIDTH / 3))
            
        dx = target_x - player.x
        dy = target_y - player.y
        
        return (1 if dx > 10 else -1 if dx < -10 else 0,
                1 if dy > 10 else -1 if dy < -10 else 0)
    
    def _chase_ball(self, player, ball):
        dx = ball.x - player.x
        dy = ball.y - player.y
        
        return (1 if dx > 10 else -1 if dx < -10 else 0,
                1 if dy > 10 else -1 if dy < -10 else 0)
