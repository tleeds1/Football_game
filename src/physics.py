import math
from src.constants import (
    FIELD_LEFT, FIELD_RIGHT, FIELD_TOP, FIELD_BOTTOM,
    GOAL_TOP, GOAL_BOTTOM, GOAL_WIDTH,
    PLAYER_BOUNCE, BALL_PLAYER_BOUNCE, BALL_BOUNCE,
    PUSH_POWER, DRIBBLE_ZONE, DRIBBLE_ATTRACTION, DRIBBLE_DAMPING,
    PLAYER_RADIUS, BALL_RADIUS
)

# Corner radius for rounded corners (HaxBall style) - keep small
CORNER_RADIUS = 15


class PhysicsEngine:
    """
    HaxBall-style physics engine.
    Key features:
    - Rounded corners to prevent ball getting stuck
    - Wall collision priority over player collision
    - Force decomposition when pushing into walls
    - Bounce dampening on consecutive collisions
    """
    
    def __init__(self):
        # Track consecutive wall collisions for dampening
        self.ball_wall_collision_count = 0
        self.ball_in_corner = False
        
        # Track stuck ball (for escape mechanism)
        self.ball_stuck_frames = 0
        self.prev_ball_pos = (0, 0)
        
    def update(self, players, ball):
        """
        Update all physics interactions.
        Priority: Wall > Player (HaxBall style)
        Returns: 0 = no goal, 1 = team 1 scored, 2 = team 2 scored
        """
        # 0. Check for stuck ball and apply escape
        self._check_stuck_ball(ball, players)
        
        # 1. FIRST: Ball-wall collision (highest priority)
        wall_hit = self._ball_wall_collision(ball)
        
        # 2. Player-wall collision
        for player in players:
            self._player_wall_collision(player)
        
        # 3. Player-player collisions
        for i, p1 in enumerate(players):
            for p2 in players[i+1:]:
                self._player_player_collision(p1, p2)
        
        # 4. LAST: Ball-player collisions (after wall is resolved)
        for player in players:
            self._ball_player_collision(ball, player, wall_hit)
        
        # 5. Check for goal
        return self._check_goal(ball)
    
    def _check_stuck_ball(self, ball, players):
        """
        Detect and escape stuck ball situations.
        When ball is barely moving AND near wall AND surrounded by players, push it out.
        """
        import random
        
        # Check if ball barely moved
        dx = ball.x - self.prev_ball_pos[0]
        dy = ball.y - self.prev_ball_pos[1]
        moved = math.sqrt(dx**2 + dy**2)
        
        # Check if ball is near wall
        near_wall = (
            ball.x < FIELD_LEFT + 30 or 
            ball.x > FIELD_RIGHT - 30 or
            ball.y < FIELD_TOP + 30 or 
            ball.y > FIELD_BOTTOM - 30
        )
        
        # Count players touching ball
        players_touching = 0
        for p in players:
            dist = math.sqrt((ball.x - p.x)**2 + (ball.y - p.y)**2)
            if dist < ball.radius + p.radius + 5:
                players_touching += 1
        
        # Stuck = barely moving + near wall + multiple players
        if moved < 2 and near_wall and players_touching >= 2:
            self.ball_stuck_frames += 1
        else:
            self.ball_stuck_frames = 0
        
        # ESCAPE: Apply random impulse after being stuck for 30 frames (~0.5s)
        if self.ball_stuck_frames > 30:
            # Random escape direction (towards center)
            center_x = (FIELD_LEFT + FIELD_RIGHT) / 2
            center_y = (FIELD_TOP + FIELD_BOTTOM) / 2
            
            escape_x = (center_x - ball.x) * 0.1 + random.uniform(-3, 3)
            escape_y = (center_y - ball.y) * 0.1 + random.uniform(-3, 3)
            
            ball.vx += escape_x
            ball.vy += escape_y
            
            self.ball_stuck_frames = 0  # Reset
        
        self.prev_ball_pos = (ball.x, ball.y)
    
    def _is_in_corner(self, x, y, radius):
        """
        Check if position is in a corner area.
        Only returns true if ball is VERY close to a corner point.
        """
        corners = [
            (FIELD_LEFT, FIELD_TOP),
            (FIELD_RIGHT, FIELD_TOP),
            (FIELD_LEFT, FIELD_BOTTOM),
            (FIELD_RIGHT, FIELD_BOTTOM),
        ]
        
        for cx, cy in corners:
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx**2 + dy**2)
            # Only trigger if ball is actually overlapping with the corner circle
            if dist < CORNER_RADIUS + radius:
                return True, cx, cy
        
        return False, 0, 0
    
    def _ball_wall_collision(self, ball):
        """
        Ball bounces off walls with ROUNDED CORNERS.
        Returns True if wall was hit (for player collision dampening).
        """
        wall_hit = False
        
        # Check if ball is in goal area (horizontally)
        in_left_goal_area = ball.x - ball.radius < FIELD_LEFT
        in_right_goal_area = ball.x + ball.radius > FIELD_RIGHT
        in_goal_y_range = GOAL_TOP < ball.y < GOAL_BOTTOM
        
        # Left wall (not goal area)
        if in_left_goal_area:
            if not in_goal_y_range:
                ball.x = FIELD_LEFT + ball.radius
                ball.vx = abs(ball.vx) * BALL_BOUNCE
                wall_hit = True
            else:
                # Ball is in goal opening - check goalpost collision (top/bottom edges)
                # Top goalpost
                if ball.y - ball.radius < GOAL_TOP and ball.y > GOAL_TOP - ball.radius:
                    ball.y = GOAL_TOP + ball.radius
                    ball.vy = abs(ball.vy) * BALL_BOUNCE
                    wall_hit = True
                # Bottom goalpost
                if ball.y + ball.radius > GOAL_BOTTOM and ball.y < GOAL_BOTTOM + ball.radius:
                    ball.y = GOAL_BOTTOM - ball.radius
                    ball.vy = -abs(ball.vy) * BALL_BOUNCE
                    wall_hit = True
                
        # Right wall (not goal area)
        if in_right_goal_area:
            if not in_goal_y_range:
                ball.x = FIELD_RIGHT - ball.radius
                ball.vx = -abs(ball.vx) * BALL_BOUNCE
                wall_hit = True
            else:
                # Ball is in goal opening - check goalpost collision
                # Top goalpost
                if ball.y - ball.radius < GOAL_TOP and ball.y > GOAL_TOP - ball.radius:
                    ball.y = GOAL_TOP + ball.radius
                    ball.vy = abs(ball.vy) * BALL_BOUNCE
                    wall_hit = True
                # Bottom goalpost
                if ball.y + ball.radius > GOAL_BOTTOM and ball.y < GOAL_BOTTOM + ball.radius:
                    ball.y = GOAL_BOTTOM - ball.radius
                    ball.vy = -abs(ball.vy) * BALL_BOUNCE
                    wall_hit = True
                
        # Top wall
        if ball.y - ball.radius < FIELD_TOP:
            ball.y = FIELD_TOP + ball.radius
            ball.vy = abs(ball.vy) * BALL_BOUNCE
            wall_hit = True
            
        # Bottom wall
        if ball.y + ball.radius > FIELD_BOTTOM:
            ball.y = FIELD_BOTTOM - ball.radius
            ball.vy = -abs(ball.vy) * BALL_BOUNCE
            wall_hit = True
        
        # Now check if in corner - apply rounded corner logic
        in_corner, corner_x, corner_y = self._is_in_corner(ball.x, ball.y, ball.radius)
        
        if in_corner:
            self.ball_in_corner = True
            
            # Distance from corner point
            dx = ball.x - corner_x
            dy = ball.y - corner_y
            dist = math.sqrt(dx**2 + dy**2)
            
            min_dist = CORNER_RADIUS + ball.radius
            
            # If ball is overlapping with corner circle
            if dist < min_dist and dist > 0:
                # Push ball out along the radius
                nx = dx / dist
                ny = dy / dist
                
                # Position ball at correct distance from corner
                ball.x = corner_x + nx * min_dist
                ball.y = corner_y + ny * min_dist
                
                # IMPORTANT: Re-clamp to walls after corner push
                # This ensures ball still touches walls correctly
                if corner_x == FIELD_LEFT:
                    ball.x = max(FIELD_LEFT + ball.radius, ball.x)
                elif corner_x == FIELD_RIGHT:
                    ball.x = min(FIELD_RIGHT - ball.radius, ball.x)
                    
                if corner_y == FIELD_TOP:
                    ball.y = max(FIELD_TOP + ball.radius, ball.y)
                elif corner_y == FIELD_BOTTOM:
                    ball.y = min(FIELD_BOTTOM - ball.radius, ball.y)
                
                # Reflect velocity
                vn = ball.vx * nx + ball.vy * ny
                if vn < 0:
                    dampen = max(0.3, BALL_BOUNCE - self.ball_wall_collision_count * 0.1)
                    ball.vx -= (1 + dampen) * vn * nx
                    ball.vy -= (1 + dampen) * vn * ny
                    self.ball_wall_collision_count += 1
                    wall_hit = True
        else:
            self.ball_in_corner = False
        
        # Reset collision count if no wall hit
        if not wall_hit:
            self.ball_wall_collision_count = max(0, self.ball_wall_collision_count - 1)
        
        # Final boundary clamp (safety net - but allow goal areas)
        if not (GOAL_TOP < ball.y < GOAL_BOTTOM):
            ball.x = max(FIELD_LEFT + ball.radius, min(FIELD_RIGHT - ball.radius, ball.x))
        ball.y = max(FIELD_TOP + ball.radius, min(FIELD_BOTTOM - ball.radius, ball.y))
        
        return wall_hit
    
    def _player_wall_collision(self, player):
        """Keep players inside field."""
        if player.x - player.radius < FIELD_LEFT:
            player.x = FIELD_LEFT + player.radius
            player.vx = 0
            
        if player.x + player.radius > FIELD_RIGHT:
            player.x = FIELD_RIGHT - player.radius
            player.vx = 0
            
        if player.y - player.radius < FIELD_TOP:
            player.y = FIELD_TOP + player.radius
            player.vy = 0
            
        if player.y + player.radius > FIELD_BOTTOM:
            player.y = FIELD_BOTTOM - player.radius
            player.vy = 0
    
    def _player_player_collision(self, p1, p2):
        """Elastic collision between two players."""
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        dist = math.sqrt(dx**2 + dy**2)
        min_dist = p1.radius + p2.radius
        
        if dist < min_dist and dist > 0:
            nx = dx / dist
            ny = dy / dist
            
            overlap = min_dist - dist
            p1.x -= nx * overlap / 2
            p1.y -= ny * overlap / 2
            p2.x += nx * overlap / 2
            p2.y += ny * overlap / 2
            
            dvx = p1.vx - p2.vx
            dvy = p1.vy - p2.vy
            dvn = dvx * nx + dvy * ny
            
            if dvn > 0:
                impulse = dvn * PLAYER_BOUNCE
                p1.vx -= impulse * nx
                p1.vy -= impulse * ny
                p2.vx += impulse * nx
                p2.vy += impulse * ny
    
    def _ball_player_collision(self, ball, player, wall_hit):
        """
        Ball-player collision with FORCE DECOMPOSITION.
        When ball is near wall, remove player's push component towards wall.
        """
        dx = ball.x - player.x
        dy = ball.y - player.y
        dist = math.sqrt(dx**2 + dy**2)
        min_dist = ball.radius + player.radius
        
        if dist < min_dist and dist > 0:
            # Collision normal
            nx = dx / dist
            ny = dy / dist
            
            # Separate ball from player
            overlap = min_dist - dist
            ball.x += nx * overlap
            ball.y += ny * overlap
            
            # Re-apply wall constraints after separation (wall has priority!)
            if not (GOAL_TOP < ball.y < GOAL_BOTTOM):
                if ball.x - ball.radius < FIELD_LEFT:
                    ball.x = FIELD_LEFT + ball.radius
                if ball.x + ball.radius > FIELD_RIGHT:
                    ball.x = FIELD_RIGHT - ball.radius
            if ball.y - ball.radius < FIELD_TOP:
                ball.y = FIELD_TOP + ball.radius
            if ball.y + ball.radius > FIELD_BOTTOM:
                ball.y = FIELD_BOTTOM - ball.radius
            
            # Calculate push force from player
            push_vx = player.vx * PUSH_POWER
            push_vy = player.vy * PUSH_POWER
            
            # FORCE DECOMPOSITION: Only remove push when ball is AT the wall
            # Use small epsilon for float comparison, check if NOT in goal area
            
            in_goal_y = GOAL_TOP < ball.y < GOAL_BOTTOM
            
            # Left/Right walls (open at goal)
            at_left_wall = (ball.x <= FIELD_LEFT + ball.radius + 0.1) and not in_goal_y
            at_right_wall = (ball.x >= FIELD_RIGHT - ball.radius - 0.1) and not in_goal_y
            
            # Top/Bottom walls (solid)
            at_top_wall = ball.y <= FIELD_TOP + ball.radius + 0.1
            at_bottom_wall = ball.y >= FIELD_BOTTOM - ball.radius - 0.1
            
            # Remove force component pushing into wall (only when at solid wall)
            if at_left_wall and push_vx < 0:
                push_vx = 0
            if at_right_wall and push_vx > 0:
                push_vx = 0
            if at_top_wall and push_vy < 0:
                push_vy = 0
            if at_bottom_wall and push_vy > 0:
                push_vy = 0
            
            # If in corner, heavily dampen player's push
            if self.ball_in_corner:
                push_vx *= 0.2
                push_vy *= 0.2
                
                # Add escape velocity along wall
                center_x = (FIELD_LEFT + FIELD_RIGHT) / 2
                center_y = (FIELD_TOP + FIELD_BOTTOM) / 2
                escape_dx = center_x - ball.x
                escape_dy = center_y - ball.y
                escape_dist = math.sqrt(escape_dx**2 + escape_dy**2)
                if escape_dist > 0:
                    push_vx += (escape_dx / escape_dist) * 0.5
                    push_vy += (escape_dy / escape_dist) * 0.5
            
            # Relative velocity
            rel_vx = ball.vx - player.vx
            rel_vy = ball.vy - player.vy
            rel_vn = rel_vx * nx + rel_vy * ny
            
            if rel_vn < 0:
                # Reduce bounce if wall was just hit (prevents jitter)
                effective_bounce = BALL_PLAYER_BOUNCE
                if wall_hit:
                    effective_bounce *= 0.3
                
                mass_ratio = player.mass / (player.mass + ball.mass)
                impulse = -rel_vn * (1 + effective_bounce) * mass_ratio
                
                ball.vx += impulse * nx
                ball.vy += impulse * ny
            
            # Apply decomposed push force
            ball.vx += push_vx
            ball.vy += push_vy
        
        # Gentle dribble attraction (only when not in corner)
        elif dist < DRIBBLE_ZONE and dist > min_dist and not self.ball_in_corner:
            player_speed = math.sqrt(player.vx**2 + player.vy**2)
            if player_speed > 0.1:
                ball.vx += player.vx * DRIBBLE_ATTRACTION
                ball.vy += player.vy * DRIBBLE_ATTRACTION
    
    def _check_goal(self, ball):
        """Check if ball crossed goal line."""
        # Ball crosses LEFT boundary -> Team 2 (blue) scores
        # (Red team's goal is on the left, so blue scores when ball goes in)
        if ball.x + ball.radius < FIELD_LEFT:
            if GOAL_TOP < ball.y < GOAL_BOTTOM:
                return 2
                
        # Ball crosses RIGHT boundary -> Team 1 (red) scores
        # (Blue team's goal is on the right, so red scores when ball goes in)
        if ball.x - ball.radius > FIELD_RIGHT:
            if GOAL_TOP < ball.y < GOAL_BOTTOM:
                return 1
                
        return 0
