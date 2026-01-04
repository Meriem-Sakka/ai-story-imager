"""
Gemini API Client
Handles all interactions with Google Gemini API for story generation.
Supports mock mode for testing.
"""

import os
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from PIL import Image

from ai_story_imager.core.config import get_config
from ai_story_imager.core.errors import (
    APIConfigurationError,
    APIError,
    APITimeoutError,
    APIRateLimitError,
    APIInvalidResponseError
)

# Constants
API_KEY_PREFIX: str = 'AIza'
API_KEY_URL: str = "https://makersuite.google.com/app/apikey"

MODEL_FALLBACK_CHAIN: List[str] = [
    'gemini-2.0-flash-exp',
    'gemini-1.5-flash',
    'gemini-pro-vision',
    'gemini-pro'
]


def _build_api_key_error_message(allow_env: bool) -> str:
    """Build API key error message based on environment settings"""
    if allow_env:
        return (
            "GEMINI_API_KEY not found. Please set it in:\n"
            "1. Sidebar API Key input (recommended)\n"
            "2. .env file (GEMINI_API_KEY=your_key)\n"
            "3. .streamlit/secrets.toml (GEMINI_API_KEY = 'your_key')\n"
            "4. Environment variable (export GEMINI_API_KEY=your_key)\n\n"
            f"Get your API key from: {API_KEY_URL}"
        )
    else:
        return (
            "Please enter your Gemini API key in the sidebar.\n\n"
            "Go to: Sidebar → 🔑 API Configuration → Enter your API key\n"
            f"Get your key from: {API_KEY_URL}\n\n"
            "Note: Environment variables are disabled. You must enter the key in the UI."
        )


def _is_env_key_allowed() -> bool:
    """Check if environment variable API keys are allowed"""
    return os.getenv('ALLOW_ENV_API_KEY', '').lower() in ('1', 'true', 'yes')


def _map_exception_to_api_error(exception: Exception) -> APIError:
    """Map generic exception to specific API error type"""
    error_str = str(exception).lower()
    
    if 'timeout' in error_str or 'timed out' in error_str:
        return APITimeoutError(f"API request timed out: {str(exception)}")
    elif '429' in error_str or 'rate limit' in error_str or 'quota' in error_str:
        return APIRateLimitError(f"API rate limit exceeded: {str(exception)}")
    elif 'invalid' in error_str or 'malformed' in error_str or 'parse' in error_str:
        return APIInvalidResponseError(f"Invalid API response: {str(exception)}")
    else:
        return APIError(f"API error: {str(exception)}")


class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: Optional[bool] = None):
        """
        Initialize Gemini client with API key
        
        Args:
            api_key: Optional API key. If not provided, will be fetched from config/session
            mock_mode: Optional override for mock mode. If None, uses config
        """
        config = get_config()
        self._mock_mode = mock_mode if mock_mode is not None else config.test_mode
        
        if self._mock_mode:
            # In mock mode, we don't need a real API key
            self.model = None
            return
        
        api_key = api_key or self._get_api_key()
        if not api_key:
            error_msg = _build_api_key_error_message(_is_env_key_allowed())
            raise APIConfigurationError(error_msg)
        
        if not api_key.startswith(API_KEY_PREFIX):
            key_preview = api_key[:5] if len(api_key) > 5 else 'too short'
            raise APIConfigurationError(
                f"API key format appears invalid. Gemini API keys typically start with '{API_KEY_PREFIX}'.\n"
                f"Your key starts with: {key_preview}\n"
                f"Please verify your API key or get a new one from:\n"
                f"{API_KEY_URL}"
            )
        
        genai.configure(api_key=api_key)
        self.model = self._initialize_model()
    
    def _initialize_model(self) -> genai.GenerativeModel:
        """
        Initialize Gemini model with fallback chain
        
        Returns:
            Initialized GenerativeModel instance
            
        Raises:
            APIConfigurationError: If all models fail to initialize
        """
        config = get_config()
        models_to_try = [config.default_model] + MODEL_FALLBACK_CHAIN
        
        for model_name in models_to_try:
            try:
                return genai.GenerativeModel(model_name)
            except Exception:
                continue
        
        raise APIConfigurationError("Failed to initialize any Gemini model")
    
    def _get_api_key(self) -> str:
        """
        Get API key from session state (UI input) only.
        
        Dev-only: If ALLOW_ENV_API_KEY is set, also check environment variables.
        This is for development convenience only - production should use UI input.
        
        Returns:
            API key string or empty string if not found
        """
        api_key = self._get_api_key_from_session_state()
        if api_key:
            return api_key
        
        if _is_env_key_allowed():
            api_key = self._get_api_key_from_env()
            if api_key:
                return api_key
        
        return ''
    
    def _get_api_key_from_session_state(self) -> str:
        """Get API key from Streamlit session state (UI input)"""
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and 'api_key' in st.session_state:
                return st.session_state.get('api_key', '') or ''
        except Exception:
            pass
        return ''
    
    def _get_api_key_from_env(self) -> str:
        """Get API key from environment variables (dev-only)"""
        # Try Streamlit secrets first
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
                return st.secrets['GEMINI_API_KEY']
        except Exception:
            pass
        
        # Try config (which reads from env/.env)
        config = get_config()
        return config.gemini_api_key or ''
    
    def generate(self, images: List[Image.Image], prompt: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate content from images and prompt
        
        Args:
            images: List of PIL Image objects
            prompt: Text prompt for generation
            config: Optional configuration dictionary
            
        Returns:
            Dictionary with 'success', 'text', 'error' keys
            
        Raises:
            APITimeoutError: If request times out
            APIRateLimitError: If rate limit exceeded
            APIInvalidResponseError: If response is malformed
            APIError: For other API errors
        """
        if self._mock_mode:
            return self._mock_generate(images, prompt, config)
        
        try:
            # Prepare content for multimodal input
            content = [prompt]
            
            # Add images to content
            for img in images:
                content.append(img)
            
            # Generate content
            response = self.model.generate_content(content)
            
            return {
                'success': True,
                'text': response.text,
                'error': None
            }
        
        except Exception as e:
            raise _map_exception_to_api_error(e)
    
    def _mock_generate(self, images: List[Image.Image], prompt: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Mock generation for testing. Returns deterministic responses based on config.
        
        Args:
            images: List of PIL Image objects (not used in mock)
            prompt: Text prompt (used to determine if this is analysis or story generation)
            config: Optional config dict. Can contain:
                - 'mock_scenario': 'success', 'timeout', 'rate_limit', 'invalid_response', 'error', 'analysis'
        
        Returns:
            Dictionary with mock response
        """
        scenario = (config or {}).get('mock_scenario', 'success')
        
        if scenario == 'timeout':
            raise APITimeoutError("Mock: API request timed out")
        elif scenario == 'rate_limit':
            raise APIRateLimitError("Mock: API rate limit exceeded (429)")
        elif scenario == 'invalid_response':
            raise APIInvalidResponseError("Mock: Invalid API response format")
        elif scenario == 'error':
            raise APIError("Mock: Generic API error")
        elif scenario == 'analysis':
            return self._get_mock_analysis_response()
        else:  # success - story generation
            return self._get_mock_story_response(prompt)
    
    def _get_mock_analysis_response(self) -> Dict[str, Any]:
        """Get mock image analysis response"""
        return {
            'success': True,
            'text': """OBJECTS: A wooden boat with weathered planks, a sandy beach, ocean waves, a setting sun, seagulls in the distance, driftwood scattered along the shore.

SCENE: A serene beach at sunset, with calm ocean waters meeting a sandy shoreline. The scene is peaceful and contemplative.

MOOD/ATMOSPHERE: Tranquil, nostalgic, peaceful, with a sense of ending and transition. The golden hour creates a warm, melancholic atmosphere.

COLORS: Dominant warm colors - golden orange and pink from the sunset, deep blue ocean, beige and white sand, brown wooden boat, soft purple and orange sky.

TIME OF DAY: Evening, during sunset (golden hour).

WEATHER/CONDITIONS: Clear skies, calm weather, gentle ocean breeze, good visibility.

COMPOSITION: The boat is positioned on the beach, with the ocean and sunset in the background. The composition draws the eye to the boat as the focal point.

ACTIVITY: The scene appears still and quiet - the boat is beached, no people visible, suggesting a moment of solitude or abandonment.

DETAILS: The boat shows signs of age and use, with visible wood grain and weathering. The sand has footprints and texture. The sunset creates long shadows and a warm glow across the entire scene.""",
            'error': None
        }
    
    def _get_mock_story_response(self, prompt: str) -> Dict[str, Any]:
        """Get mock story response based on prompt content"""
        has_visual_details = "VISUAL DETAILS FROM IMAGES" in prompt or "OBJECTS:" in prompt
        
        if has_visual_details:
            story_text = (
                "The Sunset Voyage\n\n"
                "As the golden sun dipped below the horizon, casting warm orange and pink hues across the sky, "
                "an old wooden boat rested on the sandy beach. The weathered planks told stories of countless journeys "
                "across the ocean. The calm waves gently lapped at the shore, and seagulls called in the distance. "
                "This was a place where time seemed to stand still, where the boundary between land and sea blurred "
                "in the twilight. The boat, once a vessel of adventure, now sat peacefully on the beach, its journey "
                "complete as the day came to an end. The sunset painted the sky in brilliant colors, creating a moment "
                "of perfect tranquility."
            )
        else:
            story_text = (
                "The Enchanted Forest\n\n"
                "Once upon a time, in a mystical forest filled with ancient trees and glowing fireflies, "
                "a young explorer named Luna discovered a hidden path. The path led to a clearing where magical "
                "creatures danced under the moonlight. As Luna watched in wonder, she realized that this was no "
                "ordinary forest—it was a gateway to another world."
            )
        
        return {
            'success': True,
            'text': story_text,
            'error': None
        }

