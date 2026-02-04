# Mars: Mars - Particle System
# Visual effects for exhaust and explosions

import pygame
from pygame.math import Vector2
import random
from settings import *


class Particle:
    """
    A single particle with position, velocity, and lifetime.
    """
    
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 size: float, color: tuple, lifetime: float):
        self.position = Vector2(x, y)
        self.velocity = Vector2(vx, vy)
        self.size = size
        self.initial_size = size
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alive = True
    
    def update(self, dt: float):
        """Updates particle physics and lifetime."""
        self.position += self.velocity * dt
        self.velocity.y += GRAVITY * 0.3 * dt  # Lighter gravity for particles
        
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
        
        # Shrink over lifetime
        life_ratio = self.lifetime / self.max_lifetime
        self.size = self.initial_size * life_ratio
    
    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draws the particle as a fading circle."""
        if not self.alive or self.size < 1:
            return
        
        screen_x = int(self.position.x - camera_offset.x)
        screen_y = int(self.position.y - camera_offset.y)
        
        # Fade alpha based on lifetime
        life_ratio = self.lifetime / self.max_lifetime
        alpha = int(255 * life_ratio)
        
        # Create a surface with alpha
        size = max(1, int(self.size))
        particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color[:3], alpha)
        pygame.draw.circle(particle_surface, color_with_alpha, (size, size), size)
        
        screen.blit(particle_surface, (screen_x - size, screen_y - size))


class ParticleSystem:
    """
    Manages all particles in the game.
    Handles spawning and cleanup.
    """
    
    def __init__(self):
        self.particles = []
    
    def spawn_exhaust(self, x: float, y: float, direction: str):
        """
        Spawns exhaust particles at the player's feet.
        
        Args:
            x: X position of player center
            y: Y position of player feet
            direction: 'left', 'right', or 'both'
        """
        for _ in range(EXHAUST_PARTICLE_COUNT):
            # Random offset around spawn point
            offset_x = random.uniform(-5, 5)
            
            # Velocity based on thrust direction (opposite to thrust)
            if direction == 'left':
                vx = random.uniform(50, 150)  # Particles go right
            elif direction == 'right':
                vx = random.uniform(-150, -50)  # Particles go left
            else:  # both
                vx = random.uniform(-50, 50)
            
            vy = random.uniform(100, 200)  # Always go down
            
            # Random grey-white color
            grey = random.randint(200, 255)
            color = (grey, grey, grey)
            
            particle = Particle(
                x=x + offset_x,
                y=y,
                vx=vx,
                vy=vy,
                size=EXHAUST_PARTICLE_SIZE,
                color=color,
                lifetime=EXHAUST_PARTICLE_LIFETIME
            )
            self.particles.append(particle)
    
    def spawn_explosion(self, x: float, y: float):
        """
        Spawns explosion particles when player crashes.
        
        Args:
            x: X position of explosion center
            y: Y position of explosion center
        """
        for _ in range(EXPLOSION_PARTICLE_COUNT):
            # Random direction
            angle = random.uniform(0, 360)
            speed = random.uniform(100, 400)
            
            import math
            vx = math.cos(math.radians(angle)) * speed
            vy = math.sin(math.radians(angle)) * speed
            
            # Random fire colors (red, orange, yellow)
            colors = [
                (255, 100, 50),   # Orange-red
                (255, 200, 50),   # Yellow-orange
                (255, 50, 50),    # Red
                (255, 255, 200),  # White-yellow
            ]
            color = random.choice(colors)
            
            particle = Particle(
                x=x + random.uniform(-10, 10),
                y=y + random.uniform(-10, 10),
                vx=vx,
                vy=vy,
                size=random.uniform(5, 15),
                color=color,
                lifetime=random.uniform(0.5, 1.5)
            )
            self.particles.append(particle)
    
    def update(self, dt: float):
        """Updates all particles and removes dead ones."""
        for particle in self.particles:
            particle.update(dt)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.alive]
    
    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draws all particles."""
        for particle in self.particles:
            particle.draw(screen, camera_offset)
    
    def clear(self):
        """Clears all particles."""
        self.particles.clear()
