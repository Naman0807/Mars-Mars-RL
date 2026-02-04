# Mars: Mars - Camera System
# Smooth-following camera with screen shake

import pygame
from pygame.math import Vector2
import random
from settings import *


class Camera:
    """
    Camera system that smoothly follows the player.
    Handles offset calculation and screen shake effects.
    """
    
    def __init__(self):
        self.position = Vector2(0, 0)
        self.target = Vector2(0, 0)
        
        # Screen shake
        self.shake_magnitude = 0
        self.shake_offset = Vector2(0, 0)
    
    @property
    def offset(self) -> Vector2:
        """
        Returns the camera offset for rendering.
        Includes screen shake.
        """
        return self.position + self.shake_offset
    
    def update(self, player_position: Vector2, dt: float):
        """
        Updates camera position to follow player.
        Uses linear interpolation for smooth movement.
        
        Args:
            player_position: The player's current position
            dt: Delta time in seconds
        """
        # Calculate target position (center player with look-ahead)
        self.target.x = player_position.x - SCREEN_WIDTH / 2 + CAMERA_LOOK_AHEAD_X
        self.target.y = player_position.y - SCREEN_HEIGHT / 2 + CAMERA_VERTICAL_OFFSET
        
        # Lerp towards target
        self.position.x += (self.target.x - self.position.x) * CAMERA_SMOOTH
        self.position.y += (self.target.y - self.position.y) * CAMERA_SMOOTH
        
        # Update screen shake
        self._update_shake()
    
    def add_shake(self, magnitude: float):
        """
        Adds screen shake effect.
        Args:
            magnitude: The intensity of the shake in pixels
        """
        self.shake_magnitude = max(self.shake_magnitude, magnitude)
    
    def _update_shake(self):
        """Updates and decays screen shake effect."""
        if self.shake_magnitude > 0.1:
            # Random shake offset
            self.shake_offset.x = random.uniform(-1, 1) * self.shake_magnitude
            self.shake_offset.y = random.uniform(-1, 1) * self.shake_magnitude
            
            # Decay shake
            self.shake_magnitude *= SHAKE_DECAY
        else:
            self.shake_magnitude = 0
            self.shake_offset = Vector2(0, 0)
    
    def world_to_screen(self, world_pos: Vector2) -> Vector2:
        """
        Converts world coordinates to screen coordinates.
        Args:
            world_pos: Position in world space
        Returns: Position in screen space
        """
        return world_pos - self.offset
    
    def screen_to_world(self, screen_pos: Vector2) -> Vector2:
        """
        Converts screen coordinates to world coordinates.
        Args:
            screen_pos: Position in screen space
        Returns: Position in world space
        """
        return screen_pos + self.offset
