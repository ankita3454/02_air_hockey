"""
collisions: puck-vs-paddle collision handling.
"""

import math


def handle_paddle_collision(puck, paddle):
    """
    If the puck overlaps the paddle, push it out to exactly
    puck.radius + paddle.radius and reflect its velocity about the
    collision normal (only if it's moving toward the paddle).
    Returns True if the circles overlapped this call.
    """
    min_dist = puck.radius + paddle.radius
    dx = puck.x - paddle.x
    dy = puck.y - paddle.y
    dist_sq = dx * dx + dy * dy

    if dist_sq >= min_dist * min_dist:
        return False

    dist = math.sqrt(dist_sq)
    if dist > 1e-9:
        nx, ny = dx / dist, dy / dist          # paddle -> puck
    else:
        # Centers coincide: fall back to "opposite of puck's motion".
        speed = math.hypot(puck.vx, puck.vy)
        if speed > 1e-9:
            nx, ny = -puck.vx / speed, -puck.vy / speed
        else:
            nx, ny = 1.0, 0.0

    # Resolve penetration: always, regardless of velocity direction.
    puck.x = paddle.x + nx * min_dist
    puck.y = paddle.y + ny * min_dist

    # Reflect only if approaching (v . n < 0). Prevents the sticking/
    # vibration where the velocity flips every frame while overlapping.
    vn = puck.vx * nx + puck.vy * ny
    if vn < 0:
        puck.vx -= 2 * vn * nx
        puck.vy -= 2 * vn * ny

    return True