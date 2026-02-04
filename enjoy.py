# Mars: Mars - Watch Trained Agent Play
# Loads a trained model and visualizes gameplay

import os
import argparse
import time

from stable_baselines3 import PPO

from mars_env import MarsGym


def enjoy(
    # model_path: str = "models/best/best_model",
    model_path: str = "models/best/best_model",
    episodes: int = 1000,
    fps: int = 60,
    deterministic: bool = True,
):
    """
    Watch a trained agent play Mars: Mars.
    
    Args:
        model_path: Path to trained model (without .zip)
        episodes: Number of episodes to play
        fps: Target frames per second
        deterministic: Use deterministic actions (no exploration)
    """
    # Check if model exists
    if not os.path.exists(f"{model_path}.zip"):
        print(f"Error: Model not found at {model_path}.zip")
        print("\nAvailable models:")
        if os.path.exists("models"):
            for f in os.listdir("models"):
                if f.endswith(".zip"):
                    print(f"  - models/{f[:-4]}")
            if os.path.exists("models/best"):
                for f in os.listdir("models/best"):
                    if f.endswith(".zip"):
                        print(f"  - models/best/{f[:-4]}")
        return
    
    print("=" * 60)
    print("Mars: Mars RL - Watching Agent Play")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Episodes: {episodes}")
    print(f"Deterministic: {deterministic}")
    print("=" * 60)
    print("Press Ctrl+C to exit\n")
    
    # Load model
    model = PPO.load(model_path)
    
    # Create environment with rendering
    env = MarsGym(render_mode="human")
    
    try:
        for episode in range(1, episodes + 1):
            obs, info = env.reset()
            done = False
            total_reward = 0
            steps = 0
            
            while not done:
                # Get action from model
                action, _ = model.predict(obs, deterministic=deterministic)
                
                # Execute action
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                
                total_reward += reward
                steps += 1
                
                # Render
                env.render()
                
                # Small delay for watchability
                time.sleep(1.0 / fps)
            
            print(f"Episode {episode}: Score={info['score']}, Steps={steps}, Reward={total_reward:.1f}")
    
    except KeyboardInterrupt:
        print("\nExiting...")
    
    finally:
        env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Watch trained Mars: Mars agent")
    parser.add_argument(
        "--model", 
        type=str, 
        default="models/best/best_model",
        help="Path to model (without .zip)"
    )
    parser.add_argument(
        "--episodes", 
        type=int, 
        default=1000,
        help="Number of episodes to run"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="Frames per second"
    )
    parser.add_argument(
        "--stochastic",
        action="store_true",
        help="Use stochastic actions (exploration)"
    )
    
    args = parser.parse_args()
    
    enjoy(
        model_path=args.model,
        episodes=args.episodes,
        fps=args.fps,
        deterministic=not args.stochastic,
    )
