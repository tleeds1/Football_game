"""
AI Controllers cho HaxBall
- RLTeamAI: Điều khiển đội đối thủ (cả 2 cầu thủ) trong chế độ 1 Player
- RLTeammateAI: Điều khiển cầu thủ không được chọn trong đội người chơi
"""

import math
from src.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    FIELD_LEFT, FIELD_RIGHT, FIELD_TOP, FIELD_BOTTOM,
    GOAL_TOP, GOAL_BOTTOM,
    KICK_RANGE
)


class RLTeamAI:
    """
    AI cho đội ĐỐI THỦ trong chế độ 1 người chơi.
    Điều khiển CẢ 2 cầu thủ với chiến thuật phối hợp.
    """
    
    def __init__(self, team, model_path=None):
        self.team = team
        self.score = [0, 0]
    
    def set_score(self, score):
        self.score = score
    
    def _get_opponent_goal_pos(self):
        """Lấy vị trí goal đối thủ (goal mà ta tấn công)."""
        if self.team == 0:
            return FIELD_RIGHT, (GOAL_TOP + GOAL_BOTTOM) / 2
        else:
            return FIELD_LEFT, (GOAL_TOP + GOAL_BOTTOM) / 2
    
    def _get_own_goal_pos(self):
        """Lấy vị trí goal của ta (goal cần phòng thủ)."""
        if self.team == 0:
            return FIELD_LEFT, (GOAL_TOP + GOAL_BOTTOM) / 2
        else:
            return FIELD_RIGHT, (GOAL_TOP + GOAL_BOTTOM) / 2
    
    def _facing_opponent_goal(self, player, ball):
        """Kiểm tra nếu đá bóng sẽ bay về phía goal đối thủ."""
        dx = ball.x - player.x
        if self.team == 0:  # Đỏ tấn công bên PHẢI
            return dx > 0
        else:  # Xanh tấn công bên TRÁI
            return dx < 0
    
    def _attack_dir(self):
        """Hướng tấn công: +1 = sang phải, -1 = sang trái."""
        return 1 if self.team == 0 else -1

    def _get_ball_approach_point(self, player, ball):
        """
        Tính điểm tiếp cận bóng khi bóng ở phía sau.
        Vòng qua bóng từ phía center (tránh đẩy bóng ra biên).
        """
        attack_dir = self._attack_dir()
        center_y = SCREEN_HEIGHT / 2
        
        # Kiểm tra player đã ở phía sau bóng chưa
        if self.team == 0:
            already_behind = player.x < ball.x - 20
        else:
            already_behind = player.x > ball.x + 20
        
        if already_behind:
            # Đã ở phía sau → tiến thẳng về bóng
            approach_x = ball.x - attack_dir * 25
            approach_y = ball.y
        else:
            # Chưa ở sau → vòng qua từ phía center
            approach_x = ball.x - attack_dir * 50
            
            # Vòng phía đối diện với center
            if ball.y > center_y:
                approach_y = ball.y - 60  # Bóng dưới → vòng trên
            else:
                approach_y = ball.y + 60  # Bóng trên → vòng dưới
            
            # Giới hạn trong sân
            approach_y = max(FIELD_TOP + 40, min(approach_y, FIELD_BOTTOM - 40))
        
        return approach_x, approach_y

    def update(self, players, ball):
        """Điều khiển cả 2 cầu thủ của đội."""
        team_players = [p for p in players if p.team == self.team]
        
        if not team_players:
            return {'movement': [0, 0], 'kick': False, 'switch': False}
        
        # Sắp xếp theo khoảng cách đến bóng
        # Tiebreaker: người xa goal hơn là primary (vị trí tấn công tốt hơn)
        own_goal_x, _ = self._get_own_goal_pos()
        team_players.sort(key=lambda p: (
            math.sqrt((p.x - ball.x)**2 + (p.y - ball.y)**2),
            -abs(p.x - own_goal_x)
        ))
        
        primary = team_players[0]
        for p in team_players:
            p.selected = (p == primary)
        
        # Điều khiển cầu thủ phụ
        for p in team_players[1:]:
            self._control_secondary(p, ball, primary)
        
        # Điều khiển cầu thủ chính
        move_x, move_y = self._control_primary(primary, ball)
        
        # Chỉ đá khi hướng về goal đối thủ
        kick = primary.can_kick(ball) and self._facing_opponent_goal(primary, ball)
        
        return {'movement': [move_x, move_y], 'kick': kick, 'switch': False}
    
    def _control_primary(self, player, ball):
        """
        Cầu thủ chính:
        - Bóng ở trước và gần → dẫn bóng về goal đối thủ
        - Bóng ở sau → vòng qua bóng rồi đẩy
        """
        dist_to_ball = math.hypot(player.x - ball.x, player.y - ball.y)
        opp_goal_x, opp_goal_y = self._get_opponent_goal_pos()
        forward_dir = self._attack_dir()

        dx = ball.x - player.x
        dy = ball.y - player.y
        
        # Bóng ở phía trước?
        ball_in_front = (self.team == 0 and dx > 0) or (self.team == 1 and dx < 0)

        # CÓ BÓNG và bóng ở trước → dẫn bóng về goal
        if dist_to_ball < KICK_RANGE + 10 and ball_in_front:
            move_x = forward_dir
            dy_goal = opp_goal_y - player.y
            move_y = 1 if dy_goal > 15 else -1 if dy_goal < -15 else 0
            return move_x, move_y

        # BÓNG Ở SAU hoặc xa → vòng qua bóng
        target_x, target_y = self._get_ball_approach_point(player, ball)

        dx = target_x - player.x
        dy = target_y - player.y

        move_x = 1 if dx > 5 else -1 if dx < -5 else 0
        move_y = 1 if dy > 5 else -1 if dy < -5 else 0
        
        # An toàn: không đứng yên
        if move_x == 0 and move_y == 0:
            move_x = -forward_dir

        return move_x, move_y
    
    def _control_secondary(self, player, ball, primary):
        """Cầu thủ phụ: Hỗ trợ hoặc phòng thủ."""
        own_goal_x, own_goal_y = self._get_own_goal_pos()
        forward_dir = self._attack_dir()
        
        dist_to_ball = math.sqrt((player.x - ball.x)**2 + (player.y - ball.y)**2)
        
        # CHẶN BÓNG nếu gần
        if dist_to_ball < 100:
            dx = ball.x - player.x
            dy = ball.y - player.y
            move_x = 1 if dx > 5 else -1 if dx < -5 else 0
            move_y = 1 if dy > 5 else -1 if dy < -5 else 0
            
            if move_x == 0 and move_y == 0:
                move_x = 0
                move_y = 0
            
            player.set_input(move_x, move_y)
            
            # Đá an toàn
            if player.can_kick(ball) and self._facing_opponent_goal(player, ball):
                player.kick_ball(ball)
            return
        
        # PHÒNG THỦ khi bóng ở nửa sân nhà
        ball_in_our_half = (self.team == 0 and ball.x < SCREEN_WIDTH / 2) or \
                           (self.team == 1 and ball.x > SCREEN_WIDTH / 2)
        
        if ball_in_our_half:
            target_x = own_goal_x + (ball.x - own_goal_x) * 0.4
            target_y = own_goal_y + (ball.y - own_goal_y) * 0.5
            
            if self.team == 0:
                target_x = max(FIELD_LEFT + 30, min(target_x, SCREEN_WIDTH * 0.4))
            else:
                target_x = min(FIELD_RIGHT - 30, max(target_x, SCREEN_WIDTH * 0.6))
        else:
            # HỖ TRỢ TẤN CÔNG
            if self.team == 0:
                target_x = min(ball.x + 80, FIELD_RIGHT - 100)
            else:
                target_x = max(ball.x - 80, FIELD_LEFT + 100)
            
            center_y = SCREEN_HEIGHT / 2
            if primary.y < center_y:
                target_y = min(FIELD_BOTTOM - 50, center_y + 60)
            else:
                target_y = max(FIELD_TOP + 50, center_y - 60)
        
        target_y = max(FIELD_TOP + 30, min(target_y, FIELD_BOTTOM - 30))
        
        dx = target_x - player.x
        dy = target_y - player.y
        
        move_x = 1 if dx > 10 else -1 if dx < -10 else 0
        move_y = 1 if dy > 10 else -1 if dy < -10 else 0
        
        if move_x == 0 and move_y == 0:
            move_x = 0
            move_y = 0
        
        player.set_input(move_x, move_y)
        
        if player.can_kick(ball) and self._facing_opponent_goal(player, ball):
            player.kick_ball(ball)


class RLTeammateAI:
    """
    AI cho cầu thủ ĐỒNG ĐỘI trên đội người chơi.
    Điều khiển cầu thủ không được chọn (non-selected).
    """
    
    def __init__(self, team, model_path=None):
        self.team = team
        self.score = [0, 0]
    
    def set_score(self, score):
        self.score = score
    
    def _get_opponent_goal_pos(self):
        """Lấy vị trí goal đối thủ."""
        if self.team == 0:
            return FIELD_RIGHT, (GOAL_TOP + GOAL_BOTTOM) / 2
        else:
            return FIELD_LEFT, (GOAL_TOP + GOAL_BOTTOM) / 2
    
    def _get_own_goal_pos(self):
        """Lấy vị trí goal của ta."""
        if self.team == 0:
            return FIELD_LEFT, (GOAL_TOP + GOAL_BOTTOM) / 2
        else:
            return FIELD_RIGHT, (GOAL_TOP + GOAL_BOTTOM) / 2
    
    def _facing_opponent_goal(self, player, ball):
        """Kiểm tra nếu đá bóng sẽ bay về phía goal đối thủ."""
        dx = ball.x - player.x
        if self.team == 0:
            return dx > 0
        else:
            return dx < 0
    
    def _attack_dir(self):
        """Hướng tấn công."""
        return 1 if self.team == 0 else -1
    
    def get_movement_for_player(self, player, ball, all_players):
        """
        Lấy hướng di chuyển cho đồng đội.
        - Đuổi bóng khi gần
        - Phòng thủ bằng cách đứng TRƯỚC bóng (về phía goal đối thủ)
        - Hỗ trợ tấn công bằng cách đứng vị trí nhận bóng
        """
        selected = None
        for p in all_players:
            if p.team == self.team and p.selected:
                selected = p
                break
        
        own_goal_x, own_goal_y = self._get_own_goal_pos()
        opp_goal_x, opp_goal_y = self._get_opponent_goal_pos()
        forward_dir = self._attack_dir()
        center_y = SCREEN_HEIGHT / 2
        
        dist_to_ball = math.sqrt((player.x - ball.x)**2 + (player.y - ball.y)**2)
        dx_ball = ball.x - player.x
        dy_ball = ball.y - player.y
        
        # CHẶN BÓNG: Nếu bóng gần, đuổi theo
        if dist_to_ball < 100:
            move_x = 1 if dx_ball > 3 else -1 if dx_ball < -3 else 0
            move_y = 1 if dy_ball > 3 else -1 if dy_ball < -3 else 0
            
            if move_x == 0 and move_y == 0:
                move_x = forward_dir
            
            # Chỉ đá về phía goal đối thủ
            if player.can_kick(ball) and self._facing_opponent_goal(player, ball):
                player.kick_ball(ball)
            
            return (move_x, move_y)
        
        # XÁC ĐỊNH VỊ TRÍ dựa trên bóng
        ball_in_our_half = (self.team == 0 and ball.x < SCREEN_WIDTH / 2) or \
                           (self.team == 1 and ball.x > SCREEN_WIDTH / 2)
        
        if ball_in_our_half:
            # PHÒNG THỦ: Đứng TRƯỚC bóng (về phía goal đối thủ), không phải sau
            if self.team == 0:
                target_x = min(ball.x + 50, SCREEN_WIDTH * 0.45)
                target_x = max(target_x, FIELD_LEFT + 80)
            else:
                target_x = max(ball.x - 50, SCREEN_WIDTH * 0.55)
                target_x = min(target_x, FIELD_RIGHT - 80)
            
            # Y: Giữa bóng và center goal
            target_y = (ball.y + own_goal_y) / 2
        else:
            # HỖ TRỢ TẤN CÔNG: Vị trí nhận đường chuyền
            if self.team == 0:
                target_x = min(ball.x + 100, FIELD_RIGHT - 120)
            else:
                target_x = max(ball.x - 100, FIELD_LEFT + 120)
            
            # Đứng đối diện với người chơi
            if selected:
                if selected.y < center_y:
                    target_y = min(FIELD_BOTTOM - 60, center_y + 80)
                else:
                    target_y = max(FIELD_TOP + 60, center_y - 80)
            else:
                target_y = center_y
        
        # Giới hạn trong sân
        target_y = max(FIELD_TOP + 40, min(target_y, FIELD_BOTTOM - 40))
        
        # Di chuyển về target
        dx = target_x - player.x
        dy = target_y - player.y
        
        move_x = 1 if dx > 10 else -1 if dx < -10 else 0
        move_y = 1 if dy > 10 else -1 if dy < -10 else 0
        
        if move_x == 0 and move_y == 0:
            move_x = forward_dir
        
        # Đá an toàn
        if player.can_kick(ball) and self._facing_opponent_goal(player, ball):
            player.kick_ball(ball)
        
        return (move_x, move_y)