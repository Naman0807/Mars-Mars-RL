# Mars: Mars RL

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![pygame](https://img.shields.io/badge/pygame-2.5+-green.svg)
![gymnasium](https://img.shields.io/badge/gymnasium-0.29+-purple.svg)
![stable--baselines3](https://img.shields.io/badge/stable--baselines3-2.0+-orange.svg)

A Mars-themed 2D platform landing game with an integrated Reinforcement Learning environment. Pilot an astronaut with a jetpack to safely land on procedurally generated platforms across the Martian surface.

## Description

**Mars: Mars** combines classic platformer gameplay with modern RL training capabilities. Navigate your astronaut through challenging Martian conditions including dynamic wind systems, moving platforms, and limited fuel to reach landing pads across the red planet's rugged terrain.

The project includes a fully Gymnasium-compatible RL environment for training autonomous agents using PPO (Proximal Policy Optimization) from stable-baselines3.

## Features

### Gameplay
- **Jetpack Physics** - Dual thruster controls with realistic physics simulation
- **Procedural Platforms** - Randomly generated platforms with varying distances and heights
- **Moving Platforms** - Horizontally oscillating platforms for added challenge
- **Dynamic Wind System** - Wind forces that affect trajectory
- **Fuel Management** - Limited fuel requiring strategic thrust usage
- **Crash Detection** - Landing too fast results in crash
- **Particle Effects** - Exhaust flames and explosion effects
- **Camera System** - Smooth following camera with screen shake

### RL Environment
- **Gymnasium Compatible** - Full integration with OpenAI Gymnasium
- **Dense Rewards** - Shaped reward function for efficient learning
- **PPO Training** - State-of-the-art reinforcement learning algorithm
- **TensorBoard Logging** - Monitor training progress

## Installation

### Prerequisites
- Python 3.8 or higher

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Requirements
```
pygame>=2.5.0
gymnasium>=0.29.0
stable-baselines3>=2.0.0
numpy>=1.24.0
tensorboard>=2.14.0
tqdm>=4.65.0
```

## Quick Start

### Play the Game Manually

```bash
python main.py
```

### Train an Agent

```bash
python train.py --timesteps 100000
```

### Watch Trained Agent

```bash
python enjoy.py
```

## Controls

| Key | Action |
|-----|--------|
| **Left Arrow** | Fire right thruster (push left + up) |
| **Right Arrow** | Fire left thruster (push right + up) |
| **Both Arrows** | Fire both thrusters (hover) |
| **R** | Restart after crash |

## RL Environment Documentation

### Observation Space (8 values)

| Index | Description | Range |
|-------|-------------|-------|
| 0 | Player X relative to target platform center | `[-inf, inf]` |
| 1 | Player Y relative to target platform top | `[-inf, inf]` |
| 2 | Player velocity X | `[-inf, inf]` |
| 3 | Player velocity Y | `[-inf, inf]` |
| 4 | Angle (radians from velocity) | `[-pi, pi]` |
| 5 | Fuel normalized | `[0.0, 1.0]` |
| 6 | Wind force X | `[-inf, inf]` |
| 7 | Target platform velocity X | `[-inf, inf]` |

### Action Space (Discrete 4)

| Action | Description |
|--------|-------------|
| 0 | No thrust |
| 1 | Left thruster (push right + up) |
| 2 | Right thruster (push left + up) |
| 3 | Both thrusters (hover) |

### Reward Structure

| Event | Reward |
|-------|--------|
| Successful landing | +100 |
| Crash | -100 |
| Distance to target | Proportional improvement |
| Fuel usage | -0.05 per use |
| Time alive | -0.01 per step |
| Landing on moving platform | Bonus based on velocity match |

### Environment Configuration

```python
from mars_env import MarsGym

env = MarsGym(render_mode="human")  # For visualization
env = MarsGym(render_mode=None)     # For training (faster)
```

## Project Structure

```
Mars Mars RL/
├── main.py          # Main game loop (playable pygame game)
├── mars_env.py      # Gymnasium RL environment
├── train.py         # PPO training script
├── enjoy.py         # Watch trained agent
├── entities.py      # Player and Platform classes
├── settings.py      # Game constants and physics values
├── camera.py        # Camera system
├── particles.py     # Particle effects
├── utils.py         # Utility functions
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Training

### Basic Training

```bash
python train.py --timesteps 100000
```

### Custom Parameters

```bash
python train.py --timesteps 500000 --lr 1e-4 --ent-coef 0.02
```

### Training Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--timesteps` | 100000 | Total training timesteps |
| `--lr` | 3e-4 | Learning rate |
| `--ent-coef` | 0.01 | Entropy coefficient |
| `--n-steps` | 2048 | Steps per update |
| `--batch-size` | 64 | Minibatch size |

### Monitoring Training

Training logs are saved to `logs/` and models are saved to `models/`. Use TensorBoard to monitor progress:

```bash
tensorboard --logdir logs/
```

## Configuration

All game constants are centralized in `settings.py`:

- **Physics**: Gravity, thrust power, drag, terminal velocity
- **Platforms**: Width, height, generation ranges
- **Wind**: Enable/disable, change interval, max force
- **Moving Platforms**: Speed, range of motion
- **Rewards**: Reward values for RL training