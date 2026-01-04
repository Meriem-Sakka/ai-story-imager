"""
Pytest configuration and shared fixtures
"""

import pytest
import os
from PIL import Image
import io

# Set mock mode by default for all tests
os.environ['MOCK_GEMINI'] = '1'


@pytest.fixture
def mock_image():
    """Create a mock PIL Image for testing"""
    # Create a simple 100x100 RGB image
    img = Image.new('RGB', (100, 100), color='red')
    return img


@pytest.fixture
def mock_image_bytes():
    """Create mock image bytes (JPG format)"""
    img = Image.new('RGB', (100, 100), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.getvalue()


@pytest.fixture
def sample_settings():
    """Sample story settings for testing"""
    return {
        'genre': 'Fantasy',
        'writing_style': 'Cinematic',
        'story_tone': 'Light',
        'language': 'English',
        'story_length': 'medium',
        'narrative_perspective': 'Third person limited',
        'target_audience': 'Adults',
        'creativity': 7,
        'include_title': True,
        'include_chapters': False,
        'allow_emojis': False
    }


@pytest.fixture
def mock_gemini_client():
    """Create a mock GeminiClient in mock mode"""
    from ai_story_imager.services.gemini_client import GeminiClient
    return GeminiClient(mock_mode=True)






