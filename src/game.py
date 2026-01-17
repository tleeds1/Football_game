import pygame
import os
import math
from src.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    TEAM_1_POSITIONS, TEAM_2_POSITIONS,
    MODE_1_PLAYER, MODE_2_PLAYER, MODE_TEST,
    WINNING_SCORE, GOAL_RESET_DELAY,
    FIELD_LEFT, FIELD_RIGHT, GOAL_TOP, GOAL_BOTTOM, GOAL_WIDTH
)
from src.player import Player
from src.ball import Ball
from src.physics import PhysicsEngine
from src.input_handler import InputHandler
from src.ai import AIController, TeammateAI
from src.ui import UI
from src.wind import Wind

# Try to import RL AI (optional)
try:
    from src.rl_ai import RLTeamAI, RLTeammateAI
    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False


class Game:
    """
    Main game class - HaxBall style.
    """
    
    def __init__(self, screen, game_mode):
        self.screen = screen
        self.game_mode = game_mode
        self.clock = pygame.time.Clock()
        
        self.background = self._load_background()
        
        self.players = []
        self.ball = None
        self.physics = PhysicsEngine()
        self.input_handler = InputHandler()
        self.ai_controller = None
        self.teammate_ai_team1 = TeammateAI(team=0)
        self.teammate_ai_team2 = TeammateAI(team=1)
        self.ui = UI(screen)
        self.wind = Wind()  # Wind system
        
        self.score = [0, 0]
        self.running = True
        self.paused = False
        self.goal_scored = False
        self.goal_team = 0
        self.goal_time = 0
        self.game_over = False
        self.winner = 0
        
        self._setup_game()
        
    def _load_background(self):
        """Load and scale background to new field size."""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            bg_path = os.path.join(base_path, 'assets', 'map.png')
            background = pygame.image.load(bg_path)
            background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            return background
        except Exception as e:
            print(f"Warning: Could not load background: {e}")
            return None
            
    def _setup_game(self):
        self.players = []
        
        # Create Team 1 players (always)
        for i, pos in enumerate(TEAM_1_POSITIONS):
            player = Player(pos[0], pos[1], team=0, player_id=i)
            if i == 0:
                player.selected = True
            self.players.append(player)
        
        # Create Team 2 players (except in test mode)
        if self.game_mode != MODE_TEST:
            for i, pos in enumerate(TEAM_2_POSITIONS):
                player = Player(pos[0], pos[1], team=1, player_id=i)
                if i == 0 and self.game_mode == MODE_2_PLAYER:
                    player.selected = True
                self.players.append(player)
            
        self.ball = Ball()
        
        # AI setup based on game mode
        if self.game_mode == MODE_1_PLAYER:
            # Opponent team uses RLTeamAI (controls both players with coordination)
            if RL_AVAILABLE:
                self.ai_controller = RLTeamAI(team=1)
            else:
                self.ai_controller = AIController(team=1)
            # Human team's teammate uses smart AI
            if RL_AVAILABLE:
                self.teammate_ai_team1 = RLTeammateAI(team=0)
        elif self.game_mode == MODE_2_PLAYER:
            # Both human teams use RL for non-selected player
            if RL_AVAILABLE:
                self.teammate_ai_team1 = RLTeammateAI(team=0)
                self.teammate_ai_team2 = RLTeammateAI(team=1)
            
    def _reset_positions(self):
        for player in self.players:
            if player.team == 0:
                player.reset(TEAM_1_POSITIONS[player.player_id][0],
                           TEAM_1_POSITIONS[player.player_id][1])
            else:
                player.reset(TEAM_2_POSITIONS[player.player_id][0],
                           TEAM_2_POSITIONS[player.player_id][1])
        self.ball.reset()
        
    def _handle_input(self):
        self.input_handler.handle_events(self.game_mode)
        
        if self.input_handler.quit_game:
            self.running = False
            return
            
        if self.input_handler.pause_game:
            self.paused = not self.paused
            return
            
        if self.paused:
            return
            
        # Team 1
        team1_input = self.input_handler.get_team1_input()
        self._apply_team_input(0, team1_input)
        
        # Team 2
        if self.game_mode == MODE_2_PLAYER:
            team2_input = self.input_handler.get_team2_input()
            self._apply_team_input(1, team2_input)
        elif self.ai_controller:
            # Pass score for tactical decisions
            if hasattr(self.ai_controller, 'set_score'):
                self.ai_controller.set_score(self.score)
            team2_input = self.ai_controller.update(self.players, self.ball)
            self._apply_team_input(1, team2_input, ai_controlled=True)
    
    def _switch_player(self, team):
        """Toggle selected player."""
        team_players = [p for p in self.players if p.team == team]
        for i, p in enumerate(team_players):
            if p.selected:
                p.selected = False
                team_players[(i + 1) % len(team_players)].selected = True
                break
            
    def _apply_team_input(self, team, input_data, ai_controlled=False):
        """
        Apply input to team players.
        If ai_controlled=True, AI already controls secondary players.
        """
        team_players = [p for p in self.players if p.team == team]
        
        if input_data.get('switch'):
            self._switch_player(team)
                
        selected = None
        for p in team_players:
            if p.selected:
                selected = p
                break
        if not selected and team_players:
            selected = team_players[0]
            selected.selected = True
            
        if selected:
            # Set movement input
            movement = input_data['movement']
            selected.set_input(movement[0], movement[1])
            
            # Kick
            if input_data.get('kick'):
                selected.kick_ball(self.ball)
                
        # Teammate AI for non-selected (only if NOT ai_controlled)
        if not ai_controlled:
            teammate_ai = self.teammate_ai_team1 if team == 0 else self.teammate_ai_team2
            # Pass score for tactical decisions
            if hasattr(teammate_ai, 'set_score'):
                teammate_ai.set_score(self.score)
            for p in team_players:
                if not p.selected:
                    move = teammate_ai.get_movement_for_player(p, self.ball, self.players)
                    p.set_input(move[0], move[1])
                
    def _update(self):
        if self.paused or self.game_over:
            return
            
        if self.goal_scored:
            if pygame.time.get_ticks() - self.goal_time > GOAL_RESET_DELAY:
                self.goal_scored = False
                self._reset_positions()
            return
            
        # Update players
        for player in self.players:
            player.update()
            
        # Update ball
        self.ball.update()
        
        # Update and apply wind
        self.wind.update()
        self.wind.apply(self.ball)
        
        # Physics
        goal = self.physics.update(self.players, self.ball)
        
        if goal > 0:
            self.score[goal - 1] += 1
            self.goal_scored = True
            self.goal_team = goal
            self.goal_time = pygame.time.get_ticks()
            
            if self.score[goal - 1] >= WINNING_SCORE:
                self.game_over = True
                self.winner = goal
                
    def _draw(self):
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self._draw_field()
            self._draw_goals()  # Only draw goals if no background
            
        self.ball.draw(self.screen)
        
        for player in self.players:
            player.draw(self.screen)
            
        self.ui.draw_score(self.score[0], self.score[1])
        self.ui.draw_wind_indicator(self.wind)
        
        if self.goal_scored:
            self.ui.draw_goal_message(self.goal_team)
        elif self.game_over:
            self.ui.draw_game_over(self.winner)
        elif self.paused:
            self.ui.draw_pause()
            
        pygame.display.flip()
    
    def _draw_field(self):
        """Draw field if no background."""
        self.screen.fill((60, 120, 60))
        # Field outline
        pygame.draw.rect(self.screen, (255, 255, 255),
                        (FIELD_LEFT, FIELD_TOP, 
                         FIELD_RIGHT - FIELD_LEFT, FIELD_BOTTOM - FIELD_TOP), 3)
        # Center line
        pygame.draw.line(self.screen, (255, 255, 255),
                        (SCREEN_WIDTH // 2, FIELD_TOP),
                        (SCREEN_WIDTH // 2, FIELD_BOTTOM), 2)
        # Center circle
        pygame.draw.circle(self.screen, (255, 255, 255),
                          (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 50, 2)
        
    def _draw_goals(self):
        # Left goal
        pygame.draw.rect(self.screen, (50, 50, 50),
                        (FIELD_LEFT - GOAL_WIDTH, GOAL_TOP,
                         GOAL_WIDTH, GOAL_BOTTOM - GOAL_TOP))
        # Right goal
        pygame.draw.rect(self.screen, (50, 50, 50),
                        (FIELD_RIGHT, GOAL_TOP,
                         GOAL_WIDTH, GOAL_BOTTOM - GOAL_TOP))
        
    def run(self):
        while self.running:
            self._handle_input()
            self._update()
            self._draw()
            self.clock.tick(FPS)
            
            if self.game_over:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    return 'menu'
                    
        return 'quit'
