"""
Tiny Football - A Haxball-like 2D Football Game

Controls:
    Team 1 (Red):
        - WASD: Move
        - SPACE: Kick
        - 1/2: Switch player
        
    Team 2 (Blue):
        - Arrow keys: Move
        - ENTER: Kick
        - 9/0: Switch player
        
    ESC: Pause game
"""

import pygame
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.constants import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from src.ui import UI
from src.game import Game


def main():
    """Main entry point."""
    # Initialize pygame
    pygame.init()
    pygame.display.set_caption("Tiny Football")
    
    # Create screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    
    # Create UI
    ui = UI(screen)
    
    # Main loop
    running = True
    while running:
        # Show menu and get mode selection
        mode = None
        while mode is None and running:
            mode = ui.draw_menu()
            if mode == 'quit':
                running = False
                break
            clock.tick(FPS)
            
        if not running:
            break
            
        # Start game with selected mode
        game = Game(screen, mode)
        result = game.run()
        
        if result == 'quit':
            running = False
            
    # Cleanup
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
