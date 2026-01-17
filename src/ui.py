import pygame
import math
from src.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, 
    FONT_SIZE, SCORE_Y,
    MODE_1_PLAYER, MODE_2_PLAYER, MODE_TEST,
    TEAM_1_COLOR, TEAM_2_COLOR
)


class UI:
    """UI rendering for menu, score, overlays."""
    
    def __init__(self, screen):
        self.screen = screen
        pygame.font.init()
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.title_font = pygame.font.Font(None, 72)
        self.small_font = pygame.font.Font(None, 24)
        
    def draw_menu(self):
        """Draw main menu. Returns mode or None."""
        self.screen.fill((30, 60, 30))
        
        # Title
        title = self.title_font.render("TINY FOOTBALL", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 80)))
        
        subtitle = self.small_font.render("HaxBall Style", True, (200, 200, 200))
        self.screen.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 120)))
        
        mouse_pos = pygame.mouse.get_pos()
        
        # 1 Player button
        btn1 = pygame.Rect(SCREEN_WIDTH // 2 - 100, 160, 200, 45)
        color1 = (80, 120, 80) if btn1.collidepoint(mouse_pos) else (60, 100, 60)
        pygame.draw.rect(self.screen, color1, btn1, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), btn1, 2, border_radius=10)
        self.screen.blit(self.font.render("1 PLAYER", True, (255, 255, 255)),
                        self.font.render("1 PLAYER", True, (255, 255, 255)).get_rect(center=btn1.center))
        
        # 2 Players button
        btn2 = pygame.Rect(SCREEN_WIDTH // 2 - 100, 220, 200, 45)
        color2 = (80, 120, 80) if btn2.collidepoint(mouse_pos) else (60, 100, 60)
        pygame.draw.rect(self.screen, color2, btn2, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), btn2, 2, border_radius=10)
        self.screen.blit(self.font.render("2 PLAYERS", True, (255, 255, 255)),
                        self.font.render("2 PLAYERS", True, (255, 255, 255)).get_rect(center=btn2.center))
        
        # Test Mode button
        btn_test = pygame.Rect(SCREEN_WIDTH // 2 - 100, 280, 200, 45)
        color_test = (120, 100, 60) if btn_test.collidepoint(mouse_pos) else (100, 80, 40)
        pygame.draw.rect(self.screen, color_test, btn_test, border_radius=10)
        pygame.draw.rect(self.screen, (255, 200, 100), btn_test, 2, border_radius=10)
        self.screen.blit(self.font.render("TEST MODE", True, (255, 220, 150)),
                        self.font.render("TEST MODE", True, (255, 220, 150)).get_rect(center=btn_test.center))
        
        # Controls
        ctrl1 = self.small_font.render("Team 1: WASD + K (kick) + U (switch)", True, (180, 180, 180))
        self.screen.blit(ctrl1, ctrl1.get_rect(center=(SCREEN_WIDTH // 2, 360)))
        ctrl2 = self.small_font.render("Team 2: Arrows + 2 (kick) + 3 (switch)", True, (180, 180, 180))
        self.screen.blit(ctrl2, ctrl2.get_rect(center=(SCREEN_WIDTH // 2, 390)))
        test_hint = self.small_font.render("Test Mode: Practice with your team only", True, (200, 180, 120))
        self.screen.blit(test_hint, test_hint.get_rect(center=(SCREEN_WIDTH // 2, 420)))
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if btn1.collidepoint(event.pos):
                    return MODE_1_PLAYER
                elif btn2.collidepoint(event.pos):
                    return MODE_2_PLAYER
                elif btn_test.collidepoint(event.pos):
                    return MODE_TEST
        return None
        
    def draw_score(self, score1, score2):
        """Draw score display."""
        bg = pygame.Rect(SCREEN_WIDTH // 2 - 60, 5, 120, 40)
        pygame.draw.rect(self.screen, (0, 0, 0), bg, border_radius=5)
        
        s1 = self.font.render(str(score1), True, TEAM_1_COLOR)
        self.screen.blit(s1, (SCREEN_WIDTH // 2 - 40, SCORE_Y))
        
        sep = self.font.render("-", True, (255, 255, 255))
        self.screen.blit(sep, (SCREEN_WIDTH // 2 - 8, SCORE_Y))
        
        s2 = self.font.render(str(score2), True, TEAM_2_COLOR)
        self.screen.blit(s2, (SCREEN_WIDTH // 2 + 20, SCORE_Y))
        
    def draw_goal_message(self, team):
        """Draw goal scored message."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))
        
        color = TEAM_1_COLOR if team == 1 else TEAM_2_COLOR
        text = self.title_font.render("GOAL!", True, color)
        self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        
    def draw_game_over(self, winner):
        """Draw game over screen."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        color = TEAM_1_COLOR if winner == 1 else TEAM_2_COLOR
        text = self.title_font.render(f"TEAM {winner} WINS!", True, color)
        self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
        
        hint = self.small_font.render("Press SPACE to return to menu", True, (200, 200, 200))
        self.screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)))
        
    def draw_pause(self):
        """Draw pause overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        text = self.title_font.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
    
    def draw_wind_indicator(self, wind):
        """Draw wind direction and strength indicator."""
        # Position: top-right corner
        center_x = SCREEN_WIDTH - 50
        center_y = 55
        
        # Background circle
        pygame.draw.circle(self.screen, (0, 0, 0, 180), (center_x, center_y), 25)
        pygame.draw.circle(self.screen, (255, 255, 255), (center_x, center_y), 25, 2)
        
        if wind.is_active and wind.magnitude > 0.1:
            # Draw arrow showing wind direction
            # Arrow length proportional to wind strength (max 20 pixels)
            from src.constants import WIND_MAX_FORCE
            arrow_len = min(20, (wind.magnitude / WIND_MAX_FORCE) * 20)
            
            # Arrow end point
            end_x = center_x + math.cos(wind.angle) * arrow_len
            end_y = center_y + math.sin(wind.angle) * arrow_len
            
            # Draw arrow line
            pygame.draw.line(self.screen, (100, 200, 255), 
                           (center_x, center_y), (end_x, end_y), 3)
            
            # Draw arrowhead
            head_angle = wind.angle
            head_len = 6
            for offset in [2.5, -2.5]:  # Two sides of arrowhead
                hx = end_x - math.cos(head_angle + offset) * head_len
                hy = end_y - math.sin(head_angle + offset) * head_len
                pygame.draw.line(self.screen, (100, 200, 255),
                               (end_x, end_y), (hx, hy), 2)
        else:
            # No wind - show "CALM" or dot
            pygame.draw.circle(self.screen, (150, 150, 150), (center_x, center_y), 4)
        
        # Label
        label = self.small_font.render("WIND", True, (200, 200, 200))
        self.screen.blit(label, label.get_rect(center=(center_x, center_y + 35)))
