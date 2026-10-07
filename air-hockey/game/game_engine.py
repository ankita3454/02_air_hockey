"""
GameEngine: owns the puck, both paddles, and the computer AI, and runs
one frame's worth of game logic.

"""

import random
import math 
import pygame

from game.puck import Puck
from game.paddle import Paddle
from game.ai import ComputerAI
from game.collisions import handle_paddle_collision
from game.renderer import WIDTH, HEIGHT, MARGIN, GOAL_TOP, GOAL_BOTTOM

MATCH_DURATION_MS = 30_000

PLAYER_SPEED = 6
PUCK_RADIUS = 12
PADDLE_RADIUS = 28
INITIAL_PUCK_SPEED = 4.5


class GameEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        """Start a fresh match: scores, timer, puck and paddles."""
        self.puck = Puck(WIDTH / 2, HEIGHT / 2, PUCK_RADIUS)
        self._launch_puck()

        self.player = Paddle(
            x=WIDTH * 0.15, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=MARGIN + PADDLE_RADIUS, max_x=WIDTH / 2 - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )
        self.computer = Paddle(
            x=WIDTH * 0.85, y=HEIGHT / 2, radius=PADDLE_RADIUS,
            min_x=WIDTH / 2 + PADDLE_RADIUS, max_x=WIDTH - MARGIN - PADDLE_RADIUS,
            min_y=MARGIN + PADDLE_RADIUS, max_y=HEIGHT - MARGIN - PADDLE_RADIUS,
        )
        self.ai = ComputerAI()

        self.player_score = 0
        self.computer_score = 0
        self.game_over = False
        self.start_ticks = pygame.time.get_ticks()

    def _launch_puck(self, direction=None):
        angle_choices = [0.3, 0.6, -0.3, -0.6]
        if direction is None:
            direction = random.choice([-1, 1])
        vy_factor = random.choice(angle_choices)
        self.puck.vx = INITIAL_PUCK_SPEED * direction
        self.puck.vy = INITIAL_PUCK_SPEED * vy_factor

    def handle_input(self, keys_pressed):
        if keys_pressed[pygame.K_r]:
            self.reset()
            return
        if self.game_over:
            return

        dx = dy = 0
        if keys_pressed[pygame.K_UP]:
            dy -= PLAYER_SPEED
        if keys_pressed[pygame.K_DOWN]:
            dy += PLAYER_SPEED
        if keys_pressed[pygame.K_LEFT]:
            dx -= PLAYER_SPEED
        if keys_pressed[pygame.K_RIGHT]:
            dx += PLAYER_SPEED
        self.player.move_by(dx, dy)

    def update(self):
        if self.game_over:
            return
        if self._remaining_ms() <= 0:
            self.game_over = True
            return

        self.ai.update(self.computer, self.puck)
        speed = math.hypot(self.puck.vx, self.puck.vy)
        steps = max(1, math.ceil(speed / (self.puck.radius * 0.5)))

        for _ in range(steps):
            self.puck.x += self.puck.vx / steps
            self.puck.y += self.puck.vy / steps
            self.puck.bounce_off_walls(HEIGHT, MARGIN)

            handle_paddle_collision(self.puck, self.player)
            handle_paddle_collision(self.puck, self.computer)

            if self._handle_goals():   # goal scored -> puck already reset, stop this frame
                break

    def _handle_goals(self):
        """Returns True if a goal was scored this call."""
        # Left goal: player conceded -> computer scores, serve toward player.
        if self.puck.x - self.puck.radius < MARGIN:
            if GOAL_TOP < self.puck.y < GOAL_BOTTOM:
                self.computer_score += 1
                self._reset_puck(toward=-1)
                return True
            self.puck.x = MARGIN + self.puck.radius
            self.puck.vx = -self.puck.vx
        # Right goal: computer conceded -> player scores, serve toward computer.
        elif self.puck.x + self.puck.radius > WIDTH - MARGIN:
            if GOAL_TOP < self.puck.y < GOAL_BOTTOM:
                self.player_score += 1
                self._reset_puck(toward=1)
                return True
            self.puck.x = WIDTH - MARGIN - self.puck.radius
            self.puck.vx = -self.puck.vx
        return False

    def _reset_puck(self, toward):
        """Re-center the puck and serve it toward the side that conceded."""
        self.puck.x, self.puck.y = WIDTH / 2, HEIGHT / 2
        self._launch_puck(toward)

    def draw(self, surface, font):
        from game import renderer
        renderer.draw_table(surface)
        renderer.draw_paddle(surface, self.player, renderer.COLOR_PLAYER)
        renderer.draw_paddle(surface, self.computer, renderer.COLOR_COMPUTER)
        renderer.draw_puck(surface, self.puck)

        y = MARGIN + 8
        renderer.draw_text(surface, font, str(self.player_score),
                           (WIDTH / 2 - 40, y), renderer.COLOR_PLAYER)
        renderer.draw_text(surface, font, str(self.computer_score),
                           (WIDTH / 2 + 22, y), renderer.COLOR_COMPUTER)

        # Remaining time, centered along the bottom of the table.
        seconds = math.ceil(self._remaining_ms() / 1000)
        label = f"Time: {seconds}"
        w, h = font.size(label)
        renderer.draw_text(surface, font, label,
                           (WIDTH / 2 - w / 2, HEIGHT - MARGIN - h - 8))

        if self.game_over:
            if self.player_score > self.computer_score:
                msg = "You Win"
            elif self.computer_score > self.player_score:
                msg = "Computer Wins"
            else:
                msg = "Draw"
            renderer.draw_banner(surface, font, msg)
            hint = "Press R to restart"
            hw, _ = font.size(hint)
            renderer.draw_text(surface, font, hint,
                               (WIDTH / 2 - hw / 2, HEIGHT / 2 + 30))
        
    def _remaining_ms(self):
        if self.game_over:
            return 0
        elapsed = pygame.time.get_ticks() - self.start_ticks
        return max(0, MATCH_DURATION_MS - elapsed)