# Mars: Mars - Entity Classes
# Player and Platform entities

import pygame
from pygame.math import Vector2
import random
from settings import *


class Player:
    """
    The astronaut player with jetpack physics.
    Handles movement, fuel, and state management.
    """
    
    def __init__(self, x: float, y: float):
        self.position = Vector2(x, y)
        self.velocity = Vector2(0, 0)
        self.acceleration = Vector2(0, 0)
        
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        
        self.fuel = MAX_FUEL
        self.is_grounded = False
        self.is_thrusting = False
        
        # Track which thrusters are active for visuals
        self.left_thruster = False
        self.right_thruster = False
    
    @property
    def rect(self) -> pygame.Rect:
        """Returns the collision rectangle for the player."""
        return pygame.Rect(
            self.position.x - self.width / 2,
            self.position.y - self.height,
            self.width,
            self.height
        )
    
    @property
    def feet_y(self) -> float:
        """Returns the Y coordinate of the player's feet."""
        return self.position.y
    
    def apply_thrust(self, direction: str, dt: float):
        """
        Applies thrust force based on input direction.
        Args:
            direction: 'left', 'right', or 'both'
            dt: Delta time for frame-independent physics
        """
        if self.fuel <= 0:
            return
        
        thrust_force = Vector2(0, 0)
        
        if direction == 'left':
            # Left arrow fires RIGHT thruster, pushes LEFT and UP
            thrust_force.x = -THRUST_HORIZONTAL
            thrust_force.y = -THRUST_POWER
            self.right_thruster = True
            self.left_thruster = False
        elif direction == 'right':
            # Right arrow fires LEFT thruster, pushes RIGHT and UP
            thrust_force.x = THRUST_HORIZONTAL
            thrust_force.y = -THRUST_POWER
            self.left_thruster = True
            self.right_thruster = False
        elif direction == 'both':
            # Both arrows fire both thrusters, straight UP
            thrust_force.y = -THRUST_POWER * 1.5
            self.left_thruster = True
            self.right_thruster = True
        
        self.acceleration += thrust_force
        self.fuel -= FUEL_DRAIN_RATE * dt
        self.fuel = max(0, self.fuel)
        self.is_thrusting = True
    
    def update(self, dt: float):
        """
        Updates player physics each frame.
        Args:
            dt: Delta time in seconds
        """
        # Reset acceleration each frame
        self.acceleration = Vector2(0, GRAVITY)
        self.is_thrusting = False
        self.left_thruster = False
        self.right_thruster = False
        
        # Handle input
        keys = pygame.key.get_pressed()
        
        if not self.is_grounded:
            if keys[pygame.K_LEFT] and keys[pygame.K_RIGHT]:
                self.apply_thrust('both', dt)
            elif keys[pygame.K_LEFT]:
                self.apply_thrust('left', dt)
            elif keys[pygame.K_RIGHT]:
                self.apply_thrust('right', dt)
        
        # Apply physics
        self.velocity += self.acceleration * dt
        
        # Apply drag
        self.velocity.x *= DRAG
        
        # Clamp to terminal velocity
        if self.velocity.y > TERMINAL_VELOCITY:
            self.velocity.y = TERMINAL_VELOCITY
        
        # Update position
        self.position += self.velocity * dt
    
    def land(self, platform_y: float):
        """
        Called when player successfully lands on a platform.
        Args:
            platform_y: The Y coordinate of the platform top
        """
        self.position.y = platform_y
        self.velocity = Vector2(0, 0)
        self.is_grounded = True
        self.fuel = MAX_FUEL  # Refuel on landing
    
    def launch(self):
        """Called when player takes off from a platform."""
        self.is_grounded = False
    
    def check_landing_safe(self) -> bool:
        """
        Checks if current velocity is within safe landing limits.
        Returns: True if landing would be safe, False otherwise.
        """
        return (abs(self.velocity.y) <= MAX_LANDING_SPEED_Y and 
                abs(self.velocity.x) <= MAX_LANDING_SPEED_X)
    
    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """
        Draws the player on screen.
        Args:
            screen: Pygame surface to draw on
            camera_offset: Camera offset for world-to-screen conversion
        """
        # Calculate screen position
        screen_x = self.position.x - camera_offset.x
        screen_y = self.position.y - camera_offset.y
        
        # Draw player body (suit)
        body_rect = pygame.Rect(
            screen_x - self.width / 2,
            screen_y - self.height,
            self.width,
            self.height
        )
        pygame.draw.rect(screen, COLOR_PLAYER_SUIT, body_rect)
        
        # Draw visor
        visor_rect = pygame.Rect(
            screen_x - self.width / 4,
            screen_y - self.height + 8,
            self.width / 2,
            self.height / 4
        )
        pygame.draw.rect(screen, COLOR_PLAYER_VISOR, visor_rect)
        
        # Draw fuel bar above player
        self._draw_fuel_bar(screen, screen_x, screen_y)
    
    def _draw_fuel_bar(self, screen: pygame.Surface, x: float, y: float):
        """Draws the fuel bar above the player."""
        bar_width = 50
        bar_height = 6
        bar_x = x - bar_width / 2
        bar_y = y - self.height - 15
        
        # Background
        pygame.draw.rect(screen, (50, 50, 50), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Fuel amount
        fuel_ratio = self.fuel / MAX_FUEL
        fuel_width = bar_width * fuel_ratio
        
        # Interpolate color from green to red
        r = int(255 * (1 - fuel_ratio))
        g = int(255 * fuel_ratio)
        fuel_color = (r, g, 0)
        
        pygame.draw.rect(screen, fuel_color,
                        (bar_x, bar_y, fuel_width, bar_height))


class Platform:
    """
    A landing platform with visual representation.
    """
    
    def __init__(self, x: float, y: float, index: int = 0):
        self.x = x
        self.y = y
        self.width = PLATFORM_WIDTH
        self.height = PLATFORM_HEIGHT
        self.base_height = PLATFORM_BASE_HEIGHT
        self.index = index  # Platform number for scoring
        
        # Generate random terrain rocks around platform
        self.rocks = self._generate_rocks()
    
    def _generate_rocks(self) -> list:
        """Generates decorative rock positions around the platform."""
        rocks = []
        num_rocks = random.randint(3, 7)
        for _ in range(num_rocks):
            rock_x = self.x + random.randint(-100, self.width + 100)
            rock_y = self.y + random.randint(0, 30)
            rock_size = random.randint(5, 15)
            rocks.append((rock_x, rock_y, rock_size))
        return rocks
    
    @property
    def rect(self) -> pygame.Rect:
        """Returns the collision rectangle for the platform top."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def top(self) -> float:
        """Returns the Y coordinate of the platform top."""
        return self.y
    
    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """
        Draws the platform on screen.
        Args:
            screen: Pygame surface to draw on
            camera_offset: Camera offset for world-to-screen conversion
        """
        screen_x = self.x - camera_offset.x
        screen_y = self.y - camera_offset.y
        
        # Draw base (dark grey)
        base_rect = pygame.Rect(
            screen_x,
            screen_y + self.height,
            self.width,
            self.base_height
        )
        pygame.draw.rect(screen, COLOR_PLATFORM_BASE, base_rect)
        
        # Draw landing pad (white)
        pad_rect = pygame.Rect(
            screen_x,
            screen_y,
            self.width,
            self.height
        )
        pygame.draw.rect(screen, COLOR_PLATFORM_PAD, pad_rect)
        
        # Draw terrain rocks
        for rock_x, rock_y, rock_size in self.rocks:
            rock_screen_x = rock_x - camera_offset.x
            rock_screen_y = rock_y - camera_offset.y
            pygame.draw.circle(screen, COLOR_GROUND, 
                             (int(rock_screen_x), int(rock_screen_y)), 
                             rock_size)


class PlatformManager:
    """
    Manages platform generation and cleanup.
    Spawns platforms procedurally as the player progresses.
    """
    
    def __init__(self):
        self.platforms = []
        self.next_index = 0
        
        # Spawn initial platform
        self.spawn_initial_platform()
    
    def spawn_initial_platform(self):
        """Spawns the first platform at a fixed location."""
        initial_platform = Platform(
            x=SCREEN_WIDTH / 2 - PLATFORM_WIDTH / 2,
            y=GROUND_LEVEL,
            index=0
        )
        self.platforms.append(initial_platform)
        self.next_index = 1
        
        # Pre-spawn a few platforms
        for _ in range(3):
            self.spawn_next_platform()
    
    def spawn_next_platform(self):
        """Spawns the next platform based on the last platform position."""
        if not self.platforms:
            return
        
        last_platform = self.platforms[-1]
        
        # Calculate next platform position with randomization
        distance_x = random.randint(PLATFORM_MIN_DISTANCE_X, PLATFORM_MAX_DISTANCE_X)
        distance_y = random.randint(PLATFORM_MIN_DISTANCE_Y, PLATFORM_MAX_DISTANCE_Y)
        
        new_x = last_platform.x + last_platform.width + distance_x
        new_y = last_platform.y + distance_y
        
        # Clamp Y to reasonable bounds
        new_y = max(200, min(GROUND_LEVEL, new_y))
        
        new_platform = Platform(x=new_x, y=new_y, index=self.next_index)
        self.platforms.append(new_platform)
        self.next_index += 1
    
    def cleanup_old_platforms(self, camera_x: float):
        """
        Removes platforms that are far behind the camera.
        Args:
            camera_x: Current camera X position
        """
        # Keep platforms that are within view or ahead
        self.platforms = [p for p in self.platforms 
                         if p.x + p.width > camera_x - SCREEN_WIDTH]
    
    def get_current_platform(self, player_x: float) -> Platform:
        """
        Gets the platform closest to the player's X position.
        Args:
            player_x: Player's X position
        Returns: The closest platform
        """
        if not self.platforms:
            return None
        
        closest = min(self.platforms, 
                     key=lambda p: abs(p.x + p.width/2 - player_x))
        return closest
    
    def draw(self, screen: pygame.Surface, camera_offset: Vector2):
        """Draws all visible platforms."""
        for platform in self.platforms:
            platform.draw(screen, camera_offset)
