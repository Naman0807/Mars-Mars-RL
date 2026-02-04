# Mars: Mars - PPO Training Script
# Trains an AI agent to play Mars: Mars using stable-baselines3

import os
from datetime import datetime

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback

from mars_env import MarsGym


def make_env():
    """Create environment factory."""
    def _init():
        return MarsGym(render_mode=None)
    return _init


def train(
    total_timesteps: int = 100_000,
    learning_rate: float = 3e-4,
    n_steps: int = 2048,
    batch_size: int = 64,
    n_epochs: int = 10,
    ent_coef: float = 0.01,
    save_freq: int = 10_000,
    eval_freq: int = 5_000,
    n_eval_episodes: int = 5,
    verbose: int = 1,
):
    """
    Train PPO agent on Mars: Mars environment.
    
    Args:
        total_timesteps: Total training timesteps
        learning_rate: PPO learning rate
        n_steps: Steps per update
        batch_size: Minibatch size
        n_epochs: Number of training epochs per update
        ent_coef: Entropy coefficient for exploration
        save_freq: Save checkpoint every N steps
        eval_freq: Evaluate every N steps
        n_eval_episodes: Episodes per evaluation
        verbose: Verbosity level
    """
    # Create directories
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Timestamp for unique run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create vectorized environment
    env = DummyVecEnv([make_env()])
    eval_env = DummyVecEnv([make_env()])
    
    # Initialize PPO model
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=learning_rate,
        n_steps=n_steps,
        batch_size=batch_size,
        n_epochs=n_epochs,
        ent_coef=ent_coef,
        verbose=verbose,
        tensorboard_log="logs/",
    )
    
    # Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=save_freq,
        save_path="models/",
        name_prefix=f"mars_ppo_{timestamp}"
    )
    
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path="models/best/",
        log_path="logs/",
        eval_freq=eval_freq,
        n_eval_episodes=n_eval_episodes,
        deterministic=True,
    )
    
    print("=" * 60)
    print("Mars: Mars RL Training")
    print("=" * 60)
    print(f"Total timesteps: {total_timesteps:,}")
    print(f"Learning rate: {learning_rate}")
    print(f"Entropy coefficient: {ent_coef}")
    print("=" * 60)
    
    # Train
    model.learn(
        total_timesteps=total_timesteps,
        callback=[checkpoint_callback, eval_callback],
        progress_bar=True,
    )
    
    # Save final model
    final_path = f"models/mars_ppo_final_{timestamp}"
    model.save(final_path)
    print(f"\nFinal model saved to: {final_path}.zip")
    
    env.close()
    eval_env.close()
    
    return model


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Mars: Mars RL Agent")
    parser.add_argument("--timesteps", type=int, default=100_000, help="Total training timesteps")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate")
    parser.add_argument("--ent-coef", type=float, default=0.01, help="Entropy coefficient")
    parser.add_argument("--n-steps", type=int, default=2048, help="Steps per update")
    parser.add_argument("--batch-size", type=int, default=64, help="Minibatch size")
    
    args = parser.parse_args()
    
    train(
        total_timesteps=args.timesteps,
        learning_rate=args.lr,
        ent_coef=args.ent_coef,
        n_steps=args.n_steps,
        batch_size=args.batch_size,
    )
