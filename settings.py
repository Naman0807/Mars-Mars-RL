# Mars: Mars - Game Settings & Constants
# All tunable values in one place

import pygame

# ===== DISPLAY =====
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# ===== COLORS (From Style Guide) =====
# Background
COLOR_MARS_RED = (193, 68, 14)       # #C1440E
COLOR_SUNSET_ORANGE = (231, 125, 17) # #E77D11

# Terrain
COLOR_GROUND = (78, 26, 8)           # #4E1A08

# Player
COLOR_PLAYER_SUIT = (255, 255, 255)  # White
COLOR_PLAYER_VISOR = (34, 34, 34)    # #222222

# Platforms
COLOR_PLATFORM_PAD = (255, 255, 255) # White
COLOR_PLATFORM_BASE = (51, 51, 51)   # #333333

# UI
COLOR_FUEL_FULL = (0, 255, 0)        # Green
COLOR_FUEL_LOW = (255, 0, 0)         # Red
COLOR_UI_TEXT = (255, 255, 255)      # White

# ===== PHYSICS =====
GRAVITY = 800.0                      # Pixels per second^2 (Increased from 800)
DRAG = 0.98                         # Air resistance multiplier (Less drag = harder)
TERMINAL_VELOCITY = 600.0            # Max fall speed

# Thrust settings
THRUST_POWER = 1400.0                # Upward thrust force
THRUST_HORIZONTAL = 700.0            # Horizontal thrust force

# ===== PLAYER =====
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 50
MAX_FUEL = 100.0
FUEL_DRAIN_RATE = 50.0               # Fuel units per second (Increased from 40)

# Landing conditions (Harder)
MAX_LANDING_SPEED_Y = 220.0          # Max vertical speed (Decreased from 220)
MAX_LANDING_SPEED_X = 180.0          # Max horizontal speed (Decreased from 180)

# ===== PLATFORMS =====
PLATFORM_WIDTH = 100                 # Smaller platforms (Decreased from 120)
PLATFORM_HEIGHT = 20
PLATFORM_BASE_HEIGHT = 40

# Platform generation ranges (Further apart)
PLATFORM_MIN_DISTANCE_X = 300        # Increased from 200
PLATFORM_MAX_DISTANCE_X = 600        # Increased from 400
PLATFORM_MIN_DISTANCE_Y = -150       # Can be above
PLATFORM_MAX_DISTANCE_Y = 100        # Or below

# Ground level
GROUND_LEVEL = SCREEN_HEIGHT - 100

# ===== NEW FEATURES: DIFFICULTY =====
# Wind Settings
WIND_ENABLED = True
WIND_CHANGE_INTERVAL = 100           # Frames between wind changes (approx 2 sec)
MAX_WIND_FORCE = 300.0               # Max lateral force

# Moving Platforms
MOVING_PLATFORMS_ENABLED = True
PLATFORM_MOVE_SPEED = 100.0          # Pixels per second
PLATFORM_MOVE_RANGE = 150.0          # Range of motion +/- from center

# ===== CAMERA =====
CAMERA_SMOOTH = 0.08                 # Lerp factor (lower = smoother)
CAMERA_LOOK_AHEAD_X = 200            # How far ahead to look
CAMERA_VERTICAL_OFFSET = -100        # Offset to keep player visible

# ===== PARTICLES =====
EXHAUST_PARTICLE_COUNT = 3           # Particles per frame when thrusting
EXHAUST_PARTICLE_LIFETIME = 0.3      # Seconds
EXHAUST_PARTICLE_SIZE = 8            # Initial size
EXPLOSION_PARTICLE_COUNT = 50        # Particles on crash

# ===== SCREEN SHAKE =====
THRUST_SHAKE_MAGNITUDE = 2           # Pixels
CRASH_SHAKE_MAGNITUDE = 15           # Pixels
SHAKE_DECAY = 0.9                    # Decay rate per frame

# ===== GAME STATES =====
STATE_START = "start"
STATE_PLAYING = "playing"
STATE_LANDED = "landed"
STATE_CRASHED = "crashed"

# ===== REINFORCEMENT LEARNING REWARDS =====
# Tuning these values shapes the AI's behavior
REWARD_LANDING = 100.0
REWARD_CRASH_GROUND = -100.0
REWARD_CRASH_PLATFORM = -30.0  # Less punishment for hitting target too fast vs missing it
REWARD_FUEL_PENALTY = -0.05
REWARD_TIME_PENALTY = -0.01