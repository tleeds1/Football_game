"""
Training script for HaxBall RL Agent.
Uses PPO algorithm from Stable-Baselines3.

T sẽ release bản này sau nếu chạy oke, không có thì tự hiểu =))
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback

from src.rl_env import HaxBallEnv
from src.constants import RL_MODEL_PATH, RL_TRAINING_TIMESTEPS


def train():
    """Train the RL agent."""
    print("=" * 50)
    print("HaxBall RL Training")
    print("=" * 50)
    
    # Create directories
    os.makedirs("models", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Create vectorized environment (4 parallel envs for faster training)
    print("Creating environments...")
    env = make_vec_env(HaxBallEnv, n_envs=4)
    
    # Create evaluation environment
    eval_env = HaxBallEnv()
    
    # Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=50000,
        save_path="./models/",
        name_prefix="haxball_checkpoint"
    )
    
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path="./models/",
        log_path="./logs/",
        eval_freq=10000,
        deterministic=True,
        render=False
    )
    
    # Create PPO model
    print("Creating PPO model...")
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
        verbose=1,
        tensorboard_log="./logs/"
    )
    
    # Train
    print(f"Training for {RL_TRAINING_TIMESTEPS} timesteps...")
    print("This may take a while...")
    print("-" * 50)
    
    model.learn(
        total_timesteps=RL_TRAINING_TIMESTEPS,
        callback=[checkpoint_callback, eval_callback],
        progress_bar=True
    )
    
    # Save final model
    model.save(RL_MODEL_PATH.replace(".zip", ""))
    print("-" * 50)
    print(f"Training complete! Model saved to: {RL_MODEL_PATH}")
    
    # Cleanup
    env.close()
    eval_env.close()


def test_model(model_path=None):
    """Test a trained model."""
    if model_path is None:
        model_path = RL_MODEL_PATH.replace(".zip", "")
    
    print(f"Loading model from: {model_path}")
    model = PPO.load(model_path)
    
    env = HaxBallEnv()
    obs, info = env.reset()
    
    total_reward = 0
    for _ in range(3000):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        
        if terminated or truncated:
            break
    
    print(f"Episode finished. Total reward: {total_reward:.2f}")
    print(f"Final score: {info['score']}")
    env.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="HaxBall RL Training")
    parser.add_argument("--test", action="store_true", help="Test trained model")
    parser.add_argument("--model", type=str, help="Path to model for testing")
    args = parser.parse_args()
    
    if args.test:
        test_model(args.model)
    else:
        train()
