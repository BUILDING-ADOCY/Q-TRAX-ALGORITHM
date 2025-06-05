"""
Application configuration and constants.
"""
from pydantic_settings import BaseSettings # type: ignore


class Settings(BaseSettings):  # type: ignore
    max_iterations: int = 10000
    start_temp: float = 1000.0
    cooling_rate: float = 0.995
    min_temp: float = 1e-3
    random_seed: int = 42
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()

