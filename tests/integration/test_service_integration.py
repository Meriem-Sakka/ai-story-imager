"""
Integration tests for service layer with Gemini client
"""

import pytest
from PIL import Image
from ai_story_imager.services.story_service import StoryService
from ai_story_imager.services.gemini_client import GeminiClient
from ai_story_imager.core.errors import APITimeoutError, APIRateLimitError


class TestServiceIntegration:
    """Integration tests for service + client interaction"""
    
    def test_full_story_generation_flow(self, mock_image, sample_settings):
        """Test complete story generation flow with mocked client"""
        # Create mock client
        mock_client = GeminiClient(mock_mode=True)
        service = StoryService(gemini_client=mock_client)
        
        # Generate story
        result = service.generate_story([mock_image], sample_settings, mock_client)
        
        # Verify result
        assert result['success'] is True
        assert 'story' in result
        assert 'title' in result
        assert len(result['story']) > 0
    
    def test_error_propagation_timeout(self, mock_image, sample_settings):
        """Test that API errors propagate correctly through service layer"""
        mock_client = GeminiClient(mock_mode=True)
        service = StoryService(gemini_client=mock_client)
        settings = {**sample_settings, 'mock_scenario': 'timeout'}
        
        with pytest.raises(APITimeoutError):
            service.generate_story([mock_image], settings, mock_client)
    
    def test_error_propagation_rate_limit(self, mock_image, sample_settings):
        """Test rate limit error propagation"""
        mock_client = GeminiClient(mock_mode=True)
        service = StoryService(gemini_client=mock_client)
        settings = {**sample_settings, 'mock_scenario': 'rate_limit'}
        
        with pytest.raises(APIRateLimitError):
            service.generate_story([mock_image], settings, mock_client)
    
    def test_prompt_building_integration(self, mock_image, sample_settings):
        """Test that prompt builder integrates correctly with service"""
        mock_client = GeminiClient(mock_mode=True)
        service = StoryService(gemini_client=mock_client)
        
        # Test with different settings
        settings_custom = {
            **sample_settings,
            'genre': 'Custom Genre',
            'creativity': 10
        }
        
        result = service.generate_story([mock_image], settings_custom, mock_client)
        assert result['success'] is True
    
    def test_multiple_images_processing(self, mock_image, sample_settings):
        """Test processing of multiple images through service"""
        mock_client = GeminiClient(mock_mode=True)
        service = StoryService(gemini_client=mock_client)
        
        images = [mock_image, mock_image, mock_image]
        result = service.generate_story(images, sample_settings, mock_client)
        
        assert result['success'] is True
        # All images should be processed
        assert len(images) == 3






