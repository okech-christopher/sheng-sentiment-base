"""Configuration management for Project Sheng."""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration.
    
    Environment variables override defaults:
        SHENG_DATA_DIR: Base data directory
        SHENG_LOG_LEVEL: Logging level
        SHENG_RATE_LIMIT: Requests per minute for scraping
    """
    
    # Data paths
    data_dir: str = "data"
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    dictionary_path: str = "data/dictionaries/sheng_dictionary.json"
    
    # Scraping settings
    rate_limit_per_minute: int = 20
    max_retries: int = 3
    timeout_seconds: int = 30
    
    # Processing settings
    batch_size: int = 100
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "logs/sheng.log"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            data_dir=os.getenv("SHENG_DATA_DIR", "data"),
            rate_limit_per_minute=int(os.getenv("SHENG_RATE_LIMIT", "20")),
            log_level=os.getenv("SHENG_LOG_LEVEL", "INFO"),
        )
    
    def ensure_directories(self) -> None:
        """Create required directory structure."""
        for path in [self.raw_dir, self.processed_dir, "logs", "tests"]:
            Path(path).mkdir(parents=True, exist_ok=True)
