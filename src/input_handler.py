import pygame
from src.constants import MODE_1_PLAYER, MODE_2_PLAYER, MODE_TEST


class InputHandler:
    """
    Keyboard input handler.
    Team 1: WASD + K(kick) + U(switch)
    Team 2: Arrows + 2(kick) + 3(switch)
    """
    
    def __init__(self):
        self.team1_movement = [0, 0]
        self.team2_movement = [0, 0]
        
        self.team1_kick = False
        self.team1_switch = False
        
        self.team2_kick = False
        self.team2_switch = False
        
        self.quit_game = False
        self.pause_game = False
        
    def handle_events(self, game_mode=MODE_2_PLAYER):
        """Process input events."""
        # Reset one-time actions
        self.team1_kick = False
        self.team1_switch = False
        self.team2_kick = False
        self.team2_switch = False
        self.pause_game = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game = True
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.pause_game = True
                    
                # Team 1
                if event.key == pygame.K_k:
                    self.team1_kick = True
                if event.key == pygame.K_u:
                    self.team1_switch = True
                    
                # Team 2
                if game_mode == MODE_2_PLAYER:
                    if event.key == pygame.K_2:
                        self.team2_kick = True
                    if event.key == pygame.K_3:
                        self.team2_switch = True
        
        # Continuous movement input
        keys = pygame.key.get_pressed()
        
        # Team 1 (WASD)
        self.team1_movement = [0, 0]
        if keys[pygame.K_a]:
            self.team1_movement[0] -= 1
        if keys[pygame.K_d]:
            self.team1_movement[0] += 1
        if keys[pygame.K_w]:
            self.team1_movement[1] -= 1
        if keys[pygame.K_s]:
            self.team1_movement[1] += 1
            
        # Team 2 (Arrows)
        if game_mode == MODE_2_PLAYER:
            self.team2_movement = [0, 0]
            if keys[pygame.K_LEFT]:
                self.team2_movement[0] -= 1
            if keys[pygame.K_RIGHT]:
                self.team2_movement[0] += 1
            if keys[pygame.K_UP]:
                self.team2_movement[1] -= 1
            if keys[pygame.K_DOWN]:
                self.team2_movement[1] += 1
                
    def get_team1_input(self):
        return {
            'movement': self.team1_movement,
            'kick': self.team1_kick,
            'switch': self.team1_switch
        }
        
    def get_team2_input(self):
        return {
            'movement': self.team2_movement,
            'kick': self.team2_kick,
            'switch': self.team2_switch
        }
