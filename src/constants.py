# Tiny Football Game Constants - HaxBall Style Physics

# Screen dimensions (smaller field width)
SCREEN_WIDTH = 750
SCREEN_HEIGHT = 375

# Field boundaries (within white border of map.png)
FIELD_LEFT = 30
FIELD_RIGHT = 720
FIELD_TOP = 30
FIELD_BOTTOM = 345

# Goal dimensions and positions
GOAL_WIDTH = 15
GOAL_HEIGHT = 84
GOAL_TOP = (SCREEN_HEIGHT - GOAL_HEIGHT) // 2 + 1
GOAL_BOTTOM = GOAL_TOP + GOAL_HEIGHT

LEFT_GOAL_X = FIELD_LEFT
RIGHT_GOAL_X = FIELD_RIGHT

# Player physics
PLAYER_RADIUS = 12
PLAYER_MASS = 1.0
PLAYER_ACCELERATION = 0.6  # How fast player speeds up (slower)
PLAYER_MAX_SPEED = 2.5  # Slower max speed for better ball control
PLAYER_FRICTION = 0.90  # Slide when releasing keys (1.0 = no friction)

# Ball physics
BALL_RADIUS = 6
BALL_MASS = 0.5  # Lighter ball for better sliding
BALL_FRICTION = 0.92  # Reduced friction for sliding effect
BALL_MAX_SPEED = 12  # Ball can move faster
BALL_BOUNCE = 0.84  # Wall bounce factor (1.2x increased)

# Collision physics
PLAYER_BOUNCE = 0.5  # Player-player collision bounce
BALL_PLAYER_BOUNCE = 0.3  # Some bounce for realistic physics

# Kick mechanics (only when pressing kick button)
KICK_POWER = 12  # Impulse force when kicking (1.2x increased)
KICK_RANGE = PLAYER_RADIUS + BALL_RADIUS + 10  # Distance to kick ball

# Push mechanics - ball interaction with player
PUSH_POWER = 0.6  # How much player velocity transfers to ball
DRIBBLE_ZONE = PLAYER_RADIUS + BALL_RADIUS + 4  # Small zone for close control
DRIBBLE_ATTRACTION = 0.08  # Gentle attraction (not sticky)
DRIBBLE_DAMPING = 0.2  # Light damping for sliding feel

# Wind system
WIND_MAX_FORCE = KICK_POWER / 3  # Max wind force (~4, less than 1/3 of kick)
WIND_DURATION = 15000  # Wind active for 15 seconds (ms)
WIND_CALM_DURATION = 5000  # Calm period for 5 seconds (ms)

# Kick range indicator
KICK_RANGE_COLOR = (120, 120, 120)  # Gray color for kick range circle

# Team colors
TEAM_1_COLOR = (220, 50, 50)     # Red team
TEAM_2_COLOR = (50, 100, 220)   # Blue team
BALL_COLOR = (255, 255, 255)     # White ball

# Player starting positions
TEAM_1_POSITIONS = [
    (FIELD_LEFT + 100, SCREEN_HEIGHT // 2 - 60),
    (FIELD_LEFT + 180, SCREEN_HEIGHT // 2 + 60),
]

TEAM_2_POSITIONS = [
    (FIELD_RIGHT - 100, SCREEN_HEIGHT // 2 + 60),
    (FIELD_RIGHT - 180, SCREEN_HEIGHT // 2 - 60),
]

# Ball starting position
BALL_START_POS = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# Game settings
FPS = 60
WINNING_SCORE = 5
GOAL_RESET_DELAY = 1500

# UI settings
FONT_SIZE = 36
SCORE_Y = 15

# Game modes
MODE_1_PLAYER = 1
MODE_2_PLAYER = 2
MODE_TEST = 3  # Test mode: only player's team (2 players), no opponents

# Reinforcement Learning
RL_MODEL_PATH = "models/haxball_ai.zip"
RL_TRAINING_TIMESTEPS = 500000
RL_MAX_EPISODE_STEPS = 3000  # ~50 seconds at 60 FPS
