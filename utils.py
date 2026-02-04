# Mars: Mars - Utility Functions
# Helper functions for collision detection and math

import pygame
from pygame.math import Vector2
from settings import *


def check_collision(player_rect: pygame.Rect, platform_rect: pygame.Rect) -> dict:
    """
    Checks for collision between player and platform.
    Returns detailed collision information.
    
    Args:
        player_rect: Player's collision rectangle
        platform_rect: Platform's collision rectangle
    
    Returns:
        Dictionary with collision info:
        - 'colliding': bool
        - 'from_top': bool (player hit top of platform)
        - 'overlap': float (how much overlap in Y)
    """
    result = {
        'colliding': False,
        'from_top': False,
        'overlap': 0
    }
    
    if not player_rect.colliderect(platform_rect):
        return result
    
    result['colliding'] = True
    
    # Check if player is coming from above
    player_bottom = player_rect.bottom
    platform_top = platform_rect.top
    
    # Player is hitting from top if their bottom is near the platform top
    # and they're not too far inside
    overlap = player_bottom - platform_top
    result['overlap'] = overlap
    
    # Consider it "from top" if overlap is reasonable (not hitting from side)
    if overlap > 0 and overlap < player_rect.height * 0.5:
        # Also check horizontal alignment
        player_center_x = player_rect.centerx
        if platform_rect.left <= player_center_x <= platform_rect.right:
            result['from_top'] = True
    
    return result


def lerp(a: float, b: float, t: float) -> float:
    """
    Linear interpolation between two values.
    
    Args:
        a: Start value
        b: End value
        t: Interpolation factor (0-1)
    
    Returns:
        Interpolated value
    """
    return a + (b - a) * t


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamps a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def draw_text(screen: pygame.Surface, text: str, x: float, y: float,
              font: pygame.font.Font, color: tuple = COLOR_UI_TEXT,
              center: bool = True):
    """
    Draws text on screen with optional centering.
    
    Args:
        screen: Pygame surface to draw on
        text: Text string to draw
        x: X position
        y: Y position
        font: Pygame font object
        color: Text color tuple
        center: If True, center text at position
    """
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    
    screen.blit(text_surface, text_rect)


def draw_gradient_background(screen: pygame.Surface, color1: tuple, color2: tuple):
    """
    Draws a vertical gradient background.
    
    Args:
        screen: Pygame surface to draw on
        color1: Top color
        color2: Bottom color
    """
    height = screen.get_height()
    width = screen.get_width()
    
    for y in range(height):
        ratio = y / height
        r = int(color1[0] + (color2[0] - color1[0]) * ratio)
        g = int(color1[1] + (color2[1] - color1[1]) * ratio)
        b = int(color1[2] + (color2[2] - color1[2]) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (width, y))
