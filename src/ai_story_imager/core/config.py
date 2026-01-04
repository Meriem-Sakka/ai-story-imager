"""
Configuration management for AI Story Imager
Centralizes environment variable reading and default values.
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class Config:
    """Application configuration"""
    gemini_api_key: Optional[str] = None
    test_mode: bool = False
    default_model: str = "gemini-2.5-flash"
    max_image_size_mb: int = 20
    max_image_dimension: int = 2048
    
    @classmethod
    def from_env(cls) -> 'Config':
        """
        Create config from environment variables
        
        Returns:
            Config instance with values from environment
        """
        test_mode = cls._is_test_mode_enabled()
        
        return cls(
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
            test_mode=test_mode,
            default_model=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
            max_image_size_mb=int(os.getenv('MAX_IMAGE_SIZE_MB', '20')),
            max_image_dimension=int(os.getenv('MAX_IMAGE_DIMENSION', '2048')),
        )
    
    @staticmethod
    def _is_test_mode_enabled() -> bool:
        """Check if test mode is enabled via environment variables"""
        test_mode_env = os.getenv('TEST_MODE', '').lower() in ('1', 'true', 'yes')
        mock_gemini_env = os.getenv('MOCK_GEMINI', '').lower() in ('1', 'true', 'yes')
        return test_mode_env or mock_gemini_env


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def reset_config():
    """Reset the global config (useful for testing)"""
    global _config
    _config = None

