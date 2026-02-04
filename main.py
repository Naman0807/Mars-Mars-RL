# Mars: Mars - Main Game Entry Point
# The complete game loop with all systems integrated

import pygame
import sys
from pygame.math import Vector2

from settings import *
from entities import Player, PlatformManager
from camera import Camera
from particles import ParticleSystem
from utils import check_collision, draw_text, draw_gradient_background


class Game:
    """
    Main game class that manages the game loop and all subsystems.
    """
    
    def __init__(self):
        pygame.init()
        pygame.font.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mars: Mars")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Fonts
        self.font_large = pygame.font.Font(None, 72)
        self.font_medium = pygame.font.Font(None, 48)
        self.font_small = pygame.font.Font(None, 32)
        
        # Pre-render gradient background
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        draw_gradient_background(self.background, COLOR_SUNSET_ORANGE, COLOR_MARS_RED)
        
        # Initialize game
        self.reset_game()
    
    def reset_game(self):
        """Resets all game state for a new game."""
        # Game state
        self.state = STATE_START
        self.score = 0
        self.current_platform_index = 0
        
        # Create subsystems
        self.platform_manager = PlatformManager()
        self.camera = Camera()
        self.particles = ParticleSystem()
        
        # Get starting platform
        start_platform = self.platform_manager.platforms[0]
        
        # Create player on first platform
        self.player = Player(
            x=start_platform.x + start_platform.width / 2,
            y=start_platform.top
        )
        self.player.is_grounded = True
    
    def handle_events(self):
        """Processes pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                # Start game on any key
                if self.state == STATE_START:
                    self.state = STATE_PLAYING
                    self.player.launch()
                
                # Restart on R when crashed
                if self.state == STATE_CRASHED and event.key == pygame.K_r:
                    self.reset_game()
                    self.state = STATE_PLAYING
                    self.player.launch()
                
                # Launch from platform on landed state
                if self.state == STATE_LANDED:
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE):
                        self.state = STATE_PLAYING
                        self.player.launch()
    
    def update(self, dt: float):
        """
        Updates all game systems.
        Args:
            dt: Delta time in seconds
        """
        if self.state == STATE_CRASHED:
            # Only update particles when crashed
            self.particles.update(dt)
            return
        
        if self.state == STATE_START or self.state == STATE_LANDED:
            # Camera still follows in these states
            self.camera.update(self.player.position, dt)
            return
        
        # === PLAYING STATE ===
        
        # Update player physics
        self.player.update(dt)
        
        # Spawn exhaust particles
        if self.player.is_thrusting:
            if self.player.left_thruster and self.player.right_thruster:
                direction = 'both'
            elif self.player.right_thruster:
                direction = 'left'
            elif self.player.left_thruster:
                direction = 'right'
            else:
                direction = 'both'
            
            self.particles.spawn_exhaust(
                self.player.position.x,
                self.player.position.y,
                direction
            )
            
            # Small screen shake while thrusting
            self.camera.add_shake(THRUST_SHAKE_MAGNITUDE)
        
        # Check collisions with platforms
        self._check_platform_collisions()
        
        # Check for crash into ground
        if self.player.position.y > GROUND_LEVEL + 200:
            self._crash()
        
        # Update camera
        self.camera.update(self.player.position, dt)
        
        # Update particles
        self.particles.update(dt)
        
        # Ensure more platforms exist ahead
        while len(self.platform_manager.platforms) < self.current_platform_index + 5:
            self.platform_manager.spawn_next_platform()
        
        # Cleanup old platforms
        self.platform_manager.cleanup_old_platforms(self.camera.position.x)
    
    def _check_platform_collisions(self):
        """Checks for player collision with platforms."""
        player_rect = self.player.rect
        
        for platform in self.platform_manager.platforms:
            collision = check_collision(player_rect, platform.rect)
            
            if collision['colliding']:
                if collision['from_top']:
                    # Check landing safety
                    if self.player.check_landing_safe():
                        self._land(platform)
                    else:
                        self._crash()
                else:
                    # Hit side or bottom = crash
                    self._crash()
                break
    
    def _land(self, platform):
        """
        Handles successful landing on a platform.
        Args:
            platform: The platform landed on
        """
        self.player.land(platform.top)
        self.state = STATE_LANDED
        
        # Score point if this is a new platform
        if platform.index > self.current_platform_index:
            self.score += platform.index - self.current_platform_index
            self.current_platform_index = platform.index
    
    def _crash(self):
        """Handles player crash."""
        self.state = STATE_CRASHED
        
        # Spawn explosion particles
        self.particles.spawn_explosion(
            self.player.position.x,
            self.player.position.y - self.player.height / 2
        )
        
        # Big screen shake
        self.camera.add_shake(CRASH_SHAKE_MAGNITUDE)
    
    def draw(self):
        """Renders all game elements."""
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        # Draw ground
        ground_y = GROUND_LEVEL - self.camera.offset.y
        if ground_y < SCREEN_HEIGHT:
            pygame.draw.rect(
                self.screen,
                COLOR_GROUND,
                (0, ground_y + 60, SCREEN_WIDTH, SCREEN_HEIGHT - ground_y)
            )
        
        # Draw platforms
        self.platform_manager.draw(self.screen, self.camera.offset)
        
        # Draw particles (behind player)
        self.particles.draw(self.screen, self.camera.offset)
        
        # Draw player (unless crashed)
        if self.state != STATE_CRASHED:
            self.player.draw(self.screen, self.camera.offset)
        
        # Draw UI
        self._draw_ui()
        
        pygame.display.flip()
    
    def _draw_ui(self):
        """Draws all UI elements."""
        # Score
        draw_text(
            self.screen,
            f"Score: {self.score}",
            SCREEN_WIDTH / 2,
            40,
            self.font_medium
        )
        
        # State-specific UI
        if self.state == STATE_START:
            draw_text(
                self.screen,
                "MARS: MARS",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 3,
                self.font_large
            )
            draw_text(
                self.screen,
                "Press any key to start",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                self.font_medium
            )
            draw_text(
                self.screen,
                "LEFT/RIGHT arrows to thrust",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2 + 50,
                self.font_small
            )
        
        elif self.state == STATE_CRASHED:
            draw_text(
                self.screen,
                "CRASHED!",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 3,
                self.font_large,
                COLOR_FUEL_LOW
            )
            draw_text(
                self.screen,
                f"Final Score: {self.score}",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2,
                self.font_medium
            )
            draw_text(
                self.screen,
                "Press R to retry",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 2 + 60,
                self.font_small
            )
        
        elif self.state == STATE_LANDED:
            draw_text(
                self.screen,
                "LANDED!",
                SCREEN_WIDTH / 2,
                SCREEN_HEIGHT / 3,
                self.font_large,
                COLOR_FUEL_FULL
            )
        
        # Debug info (velocity)
        if self.state == STATE_PLAYING:
            speed_text = f"VEL: ({self.player.velocity.x:.0f}, {self.player.velocity.y:.0f})"
            draw_text(
                self.screen,
                speed_text,
                100,
                SCREEN_HEIGHT - 30,
                self.font_small,
                (150, 150, 150),
                center=False
            )
    
    def run(self):
        """Main game loop."""
        while self.running:
            # Calculate delta time
            dt = self.clock.tick(FPS) / 1000.0
            
            # Cap dt to prevent physics explosion on frame drops
            dt = min(dt, 0.05)
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
