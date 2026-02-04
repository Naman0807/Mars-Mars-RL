# Mars: Mars - Gymnasium RL Environment
# Wraps the game physics for RL training with stable-baselines3

import math
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from pygame.math import Vector2

from settings import *


class MarsGym(gym.Env):
    """
    Gymnasium environment for Mars: Mars RL training.
    
    Observation Space (8 values):
        0: Player X relative to target platform center
        1: Player Y relative to target platform top  
        2: Velocity X
        3: Velocity Y
        4: Angle (radians, computed from velocity)
        5: Fuel (normalized 0.0-1.0)
        6: Wind Force X (New)
        7: Target Platform Velocity X (New)
    
    Action Space (Discrete 4):
        0: No thrust
        1: Left thruster (pushes right + up)
        2: Right thruster (pushes left + up)
        3: Both thrusters (hover)
    """
    
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}
    
    def __init__(self, render_mode=None, max_steps=1000):
        super().__init__()
        
        self.render_mode = render_mode
        self.max_steps = max_steps
        
        # Observation: [rel_x, rel_y, vel_x, vel_y, angle, fuel, wind_x, target_vel_x]
        self.observation_space = spaces.Box(
            low=np.array([-np.inf, -np.inf, -np.inf, -np.inf, -np.pi, 0.0, -np.inf, -np.inf]),
            high=np.array([np.inf, np.inf, np.inf, np.inf, np.pi, 1.0, np.inf, np.inf]),
            dtype=np.float32
        )
        
        # Actions: 0=none, 1=left, 2=right, 3=both
        self.action_space = spaces.Discrete(4)
        
        # Pygame rendering (lazy init)
        self.screen = None
        self.clock = None
        self.background = None
        
        # Game state
        self.player_pos = Vector2(0, 0)
        self.player_vel = Vector2(0, 0)
        self.fuel = MAX_FUEL
        self.is_grounded = False
        
        # Environmental Forces
        self.wind_force = 0.0
        self.wind_timer = 0
        
        # Platforms
        self.platforms = []
        self.current_platform_idx = 0
        self.target_platform_idx = 1
        
        # Episode tracking
        self.steps = 0
        self.prev_distance = 0
        self.total_time = 0.0
        
        # Track landing counts per platform for repeat landing penalty
        self.platform_landing_counts = {}
        
    def _spawn_platforms(self):
        """Generate initial platforms with movement properties."""
        self.platforms = []
        
        # First platform (starting position, static)
        first_x = SCREEN_WIDTH / 2 - PLATFORM_WIDTH / 2
        first_y = GROUND_LEVEL
        self.platforms.append({
            'x': first_x,
            'y': first_y,
            'width': PLATFORM_WIDTH,
            'height': PLATFORM_HEIGHT,
            'initial_x': first_x,
            'move_speed': 0.0,
            'move_phase': 0.0
        })
        
        # Generate additional platforms
        for i in range(10):
            last = self.platforms[-1]
            distance_x = np.random.randint(PLATFORM_MIN_DISTANCE_X, PLATFORM_MAX_DISTANCE_X)
            distance_y = np.random.randint(PLATFORM_MIN_DISTANCE_Y, PLATFORM_MAX_DISTANCE_Y)
            
            new_x = last['initial_x'] + last['width'] + distance_x
            new_y = max(200, min(GROUND_LEVEL, last['y'] + distance_y))
            
            # Moving Platform Logic
            move_speed = 0.0
            phase = 0.0
            
            if MOVING_PLATFORMS_ENABLED:
                # 50% chance for a platform to be moving
                if np.random.random() > 0.5:
                    move_speed = PLATFORM_MOVE_SPEED * (1 if np.random.random() > 0.5 else -1)
                    phase = np.random.random() * math.pi * 2
            
            self.platforms.append({
                'x': new_x,
                'y': new_y,
                'width': PLATFORM_WIDTH,
                'height': PLATFORM_HEIGHT,
                'initial_x': new_x,
                'move_speed': move_speed,
                'move_phase': phase
            })
    
    def _update_platforms(self, dt):
        """Update platform positions."""
        if not MOVING_PLATFORMS_ENABLED:
            return

        for p in self.platforms:
            if p['move_speed'] != 0:
                # Oscillate using sine wave
                p['move_phase'] += dt * (p['move_speed'] / PLATFORM_MOVE_RANGE)
                offset = math.sin(p['move_phase']) * PLATFORM_MOVE_RANGE
                p['x'] = p['initial_x'] + offset
    
    def _get_target_platform(self):
        """Get the next platform the agent should land on."""
        if self.target_platform_idx < len(self.platforms):
            return self.platforms[self.target_platform_idx]
        return self.platforms[-1]
    
    def _get_target_velocity(self):
        """Calculates current horizontal velocity of the target platform."""
        target = self._get_target_platform()
        if target['move_speed'] == 0:
            return 0.0
        # Derivative of position: d/dt (x0 + A * sin(wt)) = A * w * cos(wt)
        # w = speed / A
        # v = A * (speed/A) * cos(phase) = speed * cos(phase)
        return target['move_speed'] * math.cos(target['move_phase'])

    def _get_observation(self):
        """Build observation vector."""
        target = self._get_target_platform()
        target_center_x = target['x'] + target['width'] / 2
        target_top_y = target['y']
        
        rel_x = self.player_pos.x - target_center_x
        rel_y = self.player_pos.y - target_top_y
        
        # Angle from velocity
        if self.player_vel.length() > 0.1:
            angle = math.atan2(self.player_vel.y, self.player_vel.x)
        else:
            angle = 0.0
        
        fuel_normalized = self.fuel / MAX_FUEL
        target_vel_x = self._get_target_velocity()
        
        return np.array([
            rel_x,
            rel_y,
            self.player_vel.x,
            self.player_vel.y,
            angle,
            fuel_normalized,
            self.wind_force,
            target_vel_x
        ], dtype=np.float32)
    
    def _update_wind(self):
        """Update wind force periodically."""
        if not WIND_ENABLED:
            return
            
        self.wind_timer += 1
        if self.wind_timer >= WIND_CHANGE_INTERVAL:
            self.wind_timer = 0
            # Target wind
            target_wind = np.random.uniform(-MAX_WIND_FORCE, MAX_WIND_FORCE)
            # Smooth transition could be better, but instant change is harder
            self.wind_force = target_wind

    def _apply_action(self, action, dt):
        """Apply thrust based on action."""
        if self.fuel <= 0 or self.is_grounded:
            return False
        
        thrust_applied = False
        thrust_force = Vector2(0, 0)
        
        if action == 1:  # Left thruster - pushes right + up (Note: Logic reversed in description? Left thruster pushes RIGHT)
            # Wait, standard controls: Left Arrow -> Right Thruster fires -> Pushes LEFT
            # Let's align with typical RL: Action 1 = Go Left => Fire Right Thruster
            thrust_force.x = -THRUST_HORIZONTAL
            thrust_force.y = -THRUST_POWER
            thrust_applied = True
        elif action == 2:  # Right thruster - pushes right + up
             # Action 2 = Go Right => Fire Left Thruster
            thrust_force.x = THRUST_HORIZONTAL
            thrust_force.y = -THRUST_POWER
            thrust_applied = True
        elif action == 3:  # Both - hover
            thrust_force.y = -THRUST_POWER * 1.5
            thrust_applied = True
        
        if thrust_applied:
            self.player_vel += thrust_force * dt
            self.fuel -= FUEL_DRAIN_RATE * dt
            self.fuel = max(0, self.fuel)
        
        return thrust_applied
    
    def _update_physics(self, dt):
        """Update player physics."""
        # Apply gravity
        self.player_vel.y += GRAVITY * dt
        
        # Apply drag
        self.player_vel.x *= DRAG
        
        # Apply Wind
        if WIND_ENABLED:
            # Wind affects velocity directly (simplified drag/force)
            # Force = Mass * Accel. We assume mass=1.
            # Only affect if in air
            if not self.is_grounded:
                self.player_vel.x += self.wind_force * dt
        
        # Terminal velocity
        if self.player_vel.y > TERMINAL_VELOCITY:
            self.player_vel.y = TERMINAL_VELOCITY
        
        # Update position
        self.player_pos += self.player_vel * dt
    
    def _check_collisions(self):
        """Check for platform collisions. Returns (landed, crashed)."""
        player_rect = {
            'left': self.player_pos.x - PLAYER_WIDTH / 2,
            'right': self.player_pos.x + PLAYER_WIDTH / 2,
            'top': self.player_pos.y - PLAYER_HEIGHT,
            'bottom': self.player_pos.y
        }
        
        for i, platform in enumerate(self.platforms):
            plat_rect = {
                'left': platform['x'],
                'right': platform['x'] + platform['width'],
                'top': platform['y'],
                'bottom': platform['y'] + platform['height']
            }
            
            # Check collision
            if (player_rect['right'] > plat_rect['left'] and
                player_rect['left'] < plat_rect['right'] and
                player_rect['bottom'] > plat_rect['top'] and
                player_rect['top'] < plat_rect['bottom']):
                
                # Check if landing from top
                overlap = player_rect['bottom'] - plat_rect['top']
                player_center_x = self.player_pos.x
                
                if (0 < overlap < PLAYER_HEIGHT * 0.5 and
                    plat_rect['left'] <= player_center_x <= plat_rect['right']):
                    # Landing - check velocity
                    if (abs(self.player_vel.y) <= MAX_LANDING_SPEED_Y and
                        abs(self.player_vel.x) <= MAX_LANDING_SPEED_X):
                        # Safe landing
                        self.player_pos.y = plat_rect['top']
                        # Match platform velocity if it's moving
                        target_vel = 0
                        if MOVING_PLATFORMS_ENABLED and platform.get('move_speed'):
                             # approximate v
                             target_vel = platform['move_speed'] * math.cos(platform['move_phase'])
                        
                        self.player_vel = Vector2(target_vel, 0)
                        self.is_grounded = True
                        self.fuel = MAX_FUEL
                        
                        # Track which platform was landed on
                        self.last_landed_platform_idx = i
                        
                        if i > self.current_platform_idx:
                            self.current_platform_idx = i
                            self.target_platform_idx = i + 1
                        
                        return True, False
                    else:
                        # Too fast - crash
                        return False, True
                else:
                    # Side collision = crash
                    return False, True
        
        # Check ground crash
        if self.player_pos.y > GROUND_LEVEL + 200:
            return False, True
        
        return False, False
    
    def reset(self, seed=None, options=None):
        """Reset environment for new episode."""
        super().reset(seed=seed)
        
        # Reset platforms
        self._spawn_platforms()
        
        # Reset player on first platform
        first_platform = self.platforms[0]
        self.player_pos = Vector2(
            first_platform['x'] + first_platform['width'] / 2,
            first_platform['y']
        )
        self.player_vel = Vector2(0, 0)
        self.fuel = MAX_FUEL
        self.is_grounded = True
        
        # Reset tracking
        self.current_platform_idx = 0
        self.target_platform_idx = 1
        self.steps = 0
        
        # Reset Environmentals
        self.wind_force = 0.0
        self.wind_timer = 0
        
        self.prev_distance = self._get_distance_to_target()
        self.platform_landing_counts = {}  # Reset landing counts
        
        # Launch player (start in air)
        self.is_grounded = False
        self.player_vel.y = -50  # Small upward push to start
        
        return self._get_observation(), {}
    
    def _get_distance_to_target(self):
        """Calculate distance to target platform center."""
        target = self._get_target_platform()
        target_center = Vector2(
            target['x'] + target['width'] / 2,
            target['y']
        )
        return (self.player_pos - target_center).length()

    def step(self, action):
        """Execute one environment step."""
        self.steps += 1
        dt = 1.0 / 60.0  # Fixed timestep
        self.total_time += dt
        
        reward = 0.0
        terminated = False
        truncated = False
        
        # 1. Update Environmentals
        self._update_wind()
        self._update_platforms(dt)
        
        # 2. Living Penalties
        reward += REWARD_TIME_PENALTY
        
        # 3. Apply action & Fuel Logic
        thrust_applied = self._apply_action(action, dt)
        if thrust_applied:
            reward += REWARD_FUEL_PENALTY
        
        # 4. Physics Update
        self._update_physics(dt)
        
        # 5. Distance Shaping (Dense Reward)
        target = self._get_target_platform()
        target_center_x = target['x'] + target['width'] / 2
        
        # Calculate distance to Moving Target
        dist_x = abs(self.player_pos.x - target_center_x)
        dist_y = abs(self.player_pos.y - target['y'])
        current_distance = math.sqrt(dist_x**2 + dist_y**2)
        
        reward += (self.prev_distance - current_distance) * 5.0
        self.prev_distance = current_distance
        
        # 6. "In the Pipe" Bonus
        if target['x'] < self.player_pos.x < target['x'] + target['width']:
            reward += 0.1
            if self.player_vel.y > 0:
                reward += 0.05
            if self.player_pos.y > target['y'] - 100:
                speed = self.player_vel.length()
                if speed < 50:
                    reward += 0.1

        # 7. Check Collisions
        landed, crashed = self._check_collisions()
        
        if crashed:
            terminated = True
            if target['x'] < self.player_pos.x < target['x'] + target['width']:
                if abs(self.player_pos.y - target['y']) < 20:
                    reward += REWARD_CRASH_PLATFORM
                else:
                    reward += REWARD_CRASH_GROUND
            else:
                reward += REWARD_CRASH_GROUND

        elif landed:
            reward += REWARD_LANDING
            landing_speed = self.player_vel.length()
            if landing_speed < 10:
                reward += 10.0
            
            platform_idx = self.last_landed_platform_idx
            self.platform_landing_counts[platform_idx] = self.platform_landing_counts.get(platform_idx, 0) + 1
            if self.platform_landing_counts[platform_idx] > 2:
                reward -= 50.0 * (self.platform_landing_counts[platform_idx] - 1)
            
            if self.target_platform_idx >= len(self.platforms):
                terminated = True
                reward += 200.0
            else:
                self.is_grounded = False
                self.player_vel.y = -50
                
                # Recalculate distance
                new_target = self._get_target_platform()
                n_t_x = new_target['x'] + new_target['width'] / 2
                self.prev_distance = math.sqrt((self.player_pos.x - n_t_x)**2 + (self.player_pos.y - new_target['y'])**2)
        
        # 8. Truncation / Bounds Check
        if self.player_pos.y < -1000 or abs(self.player_pos.x - target_center_x) > 2000:
            reward += REWARD_CRASH_GROUND
            truncated = True

        if self.steps >= self.max_steps:
            truncated = True
        
        info = {
            'score': self.current_platform_idx,
            'fuel': self.fuel,
            'landed': landed,
            'crashed': crashed
        }
        
        return self._get_observation(), reward, terminated, truncated, info
            
    def render(self):
        """Render the environment."""
        if self.render_mode is None:
            return None
        
        # Lazy init pygame
        if self.screen is None:
            import pygame
            pygame.init()
            if self.render_mode == "human":
                self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                pygame.display.set_caption("Mars: Mars RL")
            else:
                self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.clock = pygame.time.Clock()
            
            # Create background
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            for y in range(SCREEN_HEIGHT):
                ratio = y / SCREEN_HEIGHT
                r = int(COLOR_SUNSET_ORANGE[0] + (COLOR_MARS_RED[0] - COLOR_SUNSET_ORANGE[0]) * ratio)
                g = int(COLOR_SUNSET_ORANGE[1] + (COLOR_MARS_RED[1] - COLOR_SUNSET_ORANGE[1]) * ratio)
                b = int(COLOR_SUNSET_ORANGE[2] + (COLOR_MARS_RED[2] - COLOR_SUNSET_ORANGE[2]) * ratio)
                pygame.draw.line(self.background, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        
        import pygame
        
        # Calculate camera offset
        camera_x = self.player_pos.x - SCREEN_WIDTH / 2 + 200
        camera_y = self.player_pos.y - SCREEN_HEIGHT / 2 - 100
        
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        # Draw ground
        ground_screen_y = GROUND_LEVEL - camera_y
        if ground_screen_y < SCREEN_HEIGHT:
            pygame.draw.rect(
                self.screen,
                COLOR_GROUND,
                (0, ground_screen_y + 60, SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        
        # Draw platforms
        for platform in self.platforms:
            screen_x = platform['x'] - camera_x
            screen_y = platform['y'] - camera_y
            
            # Base
            pygame.draw.rect(
                self.screen,
                COLOR_PLATFORM_BASE,
                (screen_x, screen_y + PLATFORM_HEIGHT, platform['width'], PLATFORM_BASE_HEIGHT)
            )
            # Pad
            pygame.draw.rect(
                self.screen,
                COLOR_PLATFORM_PAD,
                (screen_x, screen_y, platform['width'], PLATFORM_HEIGHT)
            )
            
        # Draw Wind Indicator (Arrow)
        if WIND_ENABLED and abs(self.wind_force) > 50:
            arrow_center_x = SCREEN_WIDTH - 100
            arrow_center_y = 60
            length = (self.wind_force / MAX_WIND_FORCE) * 50
            start_pos = (arrow_center_x - length/2, arrow_center_y)
            end_pos = (arrow_center_x + length/2, arrow_center_y)
            pygame.draw.line(self.screen, (200, 200, 200), start_pos, end_pos, 4)
            # Arrowhead
            if self.wind_force > 0:
                pygame.draw.polygon(self.screen, (200, 200, 200), [
                    (end_pos[0], end_pos[1] - 5),
                    (end_pos[0] + 10, end_pos[1]),
                    (end_pos[0], end_pos[1] + 5)
                ])
            else:
                 pygame.draw.polygon(self.screen, (200, 200, 200), [
                    (start_pos[0], start_pos[1] - 5),
                    (start_pos[0] - 10, start_pos[1]),
                    (start_pos[0], start_pos[1] + 5)
                ])
        
        # Draw player
        player_screen_x = self.player_pos.x - camera_x
        player_screen_y = self.player_pos.y - camera_y
        
        pygame.draw.rect(
            self.screen,
            COLOR_PLAYER_SUIT,
            (player_screen_x - PLAYER_WIDTH/2, player_screen_y - PLAYER_HEIGHT,
             PLAYER_WIDTH, PLAYER_HEIGHT)
        )
        pygame.draw.rect(
            self.screen,
            COLOR_PLAYER_VISOR,
            (player_screen_x - PLAYER_WIDTH/4, player_screen_y - PLAYER_HEIGHT + 8,
             PLAYER_WIDTH/2, PLAYER_HEIGHT/4)
        )
        
        # Draw fuel bar
        bar_width = 50
        bar_height = 6
        bar_x = player_screen_x - bar_width / 2
        bar_y = player_screen_y - PLAYER_HEIGHT - 15
        fuel_ratio = self.fuel / MAX_FUEL
        
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(
            self.screen,
            (int(255 * (1 - fuel_ratio)), int(255 * fuel_ratio), 0),
            (bar_x, bar_y, bar_width * fuel_ratio, bar_height)
        )
        
        # Draw score
        font = pygame.font.Font(None, 48)
        text = font.render(f"Score: {self.current_platform_idx}", True, COLOR_UI_TEXT)
        self.screen.blit(text, (SCREEN_WIDTH/2 - text.get_width()/2, 20))
        
        if self.render_mode == "human":
            pygame.display.flip()
            self.clock.tick(self.metadata["render_fps"])
            
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
        
        if self.render_mode == "rgb_array":
            return np.transpose(
                np.array(pygame.surfarray.pixels3d(self.screen)),
                axes=(1, 0, 2)
            )
        
        return None
    
    def close(self):
        """Clean up pygame."""
        if self.screen is not None:
            import pygame
            pygame.quit()
            self.screen = None


# Register the environment
gym.register(
    id="MarsGym-v0",
    entry_point="mars_env:MarsGym",
    max_episode_steps=1000,
)
