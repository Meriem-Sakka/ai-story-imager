"""
Unit tests for Gemini client
"""

import pytest
import os
from unittest.mock import patch, Mock
from PIL import Image
from ai_story_imager.services.gemini_client import GeminiClient
from ai_story_imager.core.errors import (
    APIConfigurationError,
    APITimeoutError,
    APIRateLimitError,
    APIInvalidResponseError,
    APIError
)


class TestGeminiClient:
    """Test Gemini client functionality"""
    
    def test_mock_mode_initialization(self):
        """Test client initialization in mock mode"""
        client = GeminiClient(mock_mode=True)
        assert client._mock_mode is True
        assert client.model is None
    
    def test_mock_generate_success(self, mock_image):
        """Test mock generation with success scenario"""
        client = GeminiClient(mock_mode=True)
        
        result = client.generate([mock_image], "Test prompt", {'mock_scenario': 'success'})
        
        assert result['success'] is True
        assert 'text' in result
        assert len(result['text']) > 0
        assert result['error'] is None
    
    def test_mock_generate_timeout(self, mock_image):
        """Test mock generation with timeout scenario"""
        client = GeminiClient(mock_mode=True)
        
        with pytest.raises(APITimeoutError):
            client.generate([mock_image], "Test prompt", {'mock_scenario': 'timeout'})
    
    def test_mock_generate_rate_limit(self, mock_image):
        """Test mock generation with rate limit scenario"""
        client = GeminiClient(mock_mode=True)
        
        with pytest.raises(APIRateLimitError):
            client.generate([mock_image], "Test prompt", {'mock_scenario': 'rate_limit'})
    
    def test_mock_generate_invalid_response(self, mock_image):
        """Test mock generation with invalid response scenario"""
        client = GeminiClient(mock_mode=True)
        
        with pytest.raises(APIInvalidResponseError):
            client.generate([mock_image], "Test prompt", {'mock_scenario': 'invalid_response'})
    
    def test_mock_generate_error(self, mock_image):
        """Test mock generation with generic error scenario"""
        client = GeminiClient(mock_mode=True)
        
        with pytest.raises(APIError):
            client.generate([mock_image], "Test prompt", {'mock_scenario': 'error'})
    
    def test_api_key_validation_missing(self):
        """Test API key validation when missing (default behavior - UI only)"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('ai_story_imager.core.config.get_config') as mock_config:
                from ai_story_imager.core.config import Config
                mock_config.return_value = Config(test_mode=False, gemini_api_key=None)
                with pytest.raises(APIConfigurationError) as exc_info:
                    GeminiClient(mock_mode=False)
                
                # Should show UI-only message when ALLOW_ENV_API_KEY is not set
                assert 'Please enter your Gemini API key in the sidebar' in str(exc_info.value)
    
    def test_api_key_validation_invalid_format(self):
        """Test API key validation with invalid format (requires ALLOW_ENV_API_KEY)"""
        # Enable env API key to test format validation
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'invalid_key',
            'ALLOW_ENV_API_KEY': '1'
        }):
            with patch('ai_story_imager.core.config.get_config') as mock_config:
                from ai_story_imager.core.config import Config
                # Mock config to return the invalid key
                mock_config.return_value = Config(test_mode=False, gemini_api_key='invalid_key')
                # Also need to patch _get_api_key to return the invalid key from config
                with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='invalid_key'):
                    with pytest.raises(APIConfigurationError) as exc_info:
                        GeminiClient(mock_mode=False)
                    
                    assert 'format appears invalid' in str(exc_info.value)
    
    def test_get_api_key_from_env(self):
        """Test API key retrieval from environment variable"""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'AIzaSyTestKey123'}):
            # In mock mode, we don't need to validate the key format
            client = GeminiClient(mock_mode=True)
            assert client._mock_mode is True
    
    def test_generate_with_multiple_images(self, mock_image):
        """Test generation with multiple images"""
        client = GeminiClient(mock_mode=True)
        images = [mock_image, mock_image]
        
        result = client.generate(images, "Test prompt")
        
        assert result['success'] is True
        assert 'text' in result
    
    def test_api_key_missing_with_allow_env_enabled(self):
        """Test API key missing when ALLOW_ENV_API_KEY is enabled (line 48)"""
        with patch.dict(os.environ, {'ALLOW_ENV_API_KEY': '1'}, clear=True):
            with patch('ai_story_imager.core.config.get_config') as mock_config:
                from ai_story_imager.core.config import Config
                mock_config.return_value = Config(test_mode=False, gemini_api_key=None)
                with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value=''):
                    with pytest.raises(APIConfigurationError) as exc_info:
                        GeminiClient(mock_mode=False)
                    
                    # Should show the env-enabled error message (line 48-54)
                    assert 'GEMINI_API_KEY not found' in str(exc_info.value)
                    assert 'Sidebar API Key input' in str(exc_info.value)
                    assert '.env file' in str(exc_info.value)
    
    def test_api_key_missing_without_allow_env(self):
        """Test API key missing when ALLOW_ENV_API_KEY is disabled (line 57-62)"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('ai_story_imager.core.config.get_config') as mock_config:
                from ai_story_imager.core.config import Config
                mock_config.return_value = Config(test_mode=False, gemini_api_key=None)
                with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value=''):
                    with pytest.raises(APIConfigurationError) as exc_info:
                        GeminiClient(mock_mode=False)
                    
                    # Should show UI-only message (line 57-62)
                    assert 'Please enter your Gemini API key in the sidebar' in str(exc_info.value)
                    assert 'Environment variables are disabled' in str(exc_info.value)
    
    def test_model_initialization_success(self):
        """Test successful model initialization (lines 75-99)"""
        with patch('google.generativeai.configure') as mock_configure:
            with patch('google.generativeai.GenerativeModel') as mock_model:
                mock_model_instance = Mock()
                mock_model.return_value = mock_model_instance
                
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        client = GeminiClient(mock_mode=False)
                        
                        # Verify genai.configure was called (line 75)
                        mock_configure.assert_called_once_with(api_key='AIzaSyTestKey123')
                        # Verify GenerativeModel was called (line 93)
                        mock_model.assert_called()
                        assert client.model is not None
    
    def test_model_initialization_fallback_chain(self):
        """Test model initialization with fallback chain (lines 82-96)"""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model:
                # First model fails, second succeeds
                mock_model.side_effect = [Exception("Model not found"), Mock()]
                
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        client = GeminiClient(mock_mode=False)
                        
                        # Should have tried multiple models (line 91-96)
                        assert mock_model.call_count >= 2
                        assert client.model is not None
    
    def test_model_initialization_all_fail(self):
        """Test model initialization when all models fail (line 98-99)"""
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel') as mock_model:
                # All models fail
                mock_model.side_effect = Exception("Model not found")
                
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        with pytest.raises(APIConfigurationError) as exc_info:
                            GeminiClient(mock_mode=False)
                        
                        # Should raise error when all models fail (line 99)
                        assert 'Failed to initialize any Gemini model' in str(exc_info.value)
    
    def test_get_api_key_from_session_state(self):
        """Test API key retrieval from session state (lines 114-118)"""
        with patch('streamlit.session_state', {'api_key': 'AIzaSySessionKey123'}, create=True):
            with patch('ai_story_imager.core.config.get_config') as mock_config:
                from ai_story_imager.core.config import Config
                mock_config.return_value = Config(test_mode=False, gemini_api_key=None)
                
                client = GeminiClient(mock_mode=False, api_key=None)
                # Should use session state key
                api_key = client._get_api_key()
                assert api_key == 'AIzaSySessionKey123'
    
    def test_get_api_key_from_session_state_empty(self):
        """Test API key retrieval when session state has empty key (line 115)"""
        # Test _get_api_key directly without initializing client
        with patch('streamlit.session_state', {'api_key': ''}, create=True):
            with patch.dict(os.environ, {}, clear=True):
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(test_mode=False, gemini_api_key=None)
                    
                    # Create client in mock mode to avoid initialization errors
                    client = GeminiClient(mock_mode=True)
                    # Test _get_api_key directly (line 115 check fails, returns empty)
                    api_key = client._get_api_key()
                    assert api_key == ''
    
    def test_get_api_key_from_streamlit_secrets(self):
        """Test API key retrieval from Streamlit secrets (lines 124-128)"""
        with patch.dict(os.environ, {'ALLOW_ENV_API_KEY': '1'}):
            # Mock streamlit secrets
            mock_secrets = {'GEMINI_API_KEY': 'AIzaSySecretsKey123'}
            with patch('streamlit.secrets', mock_secrets, create=True):
                with patch('streamlit.session_state', {}, create=True):
                    with patch('ai_story_imager.core.config.get_config') as mock_config:
                        from ai_story_imager.core.config import Config
                        mock_config.return_value = Config(test_mode=False, gemini_api_key=None)
                        
                        client = GeminiClient(mock_mode=False, api_key=None)
                        api_key = client._get_api_key()
                        # Should return from secrets (line 127)
                        assert api_key == 'AIzaSySecretsKey123'
    
    def test_get_api_key_from_config_env(self):
        """Test API key retrieval from config/env (lines 131-134)"""
        with patch.dict(os.environ, {'ALLOW_ENV_API_KEY': '1'}):
            with patch('streamlit.session_state', {}, create=True):
                with patch('streamlit.secrets', {}, create=True):
                    # Mock get_config to return config with API key
                    from ai_story_imager.core.config import Config
                    test_config = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyConfigKey123'
                    )
                    
                    # Patch get_config in both places it's called
                    with patch('ai_story_imager.services.gemini_client.get_config', return_value=test_config):
                        with patch('ai_story_imager.core.config.get_config', return_value=test_config):
                            # Create client in mock mode to avoid initialization
                            client = GeminiClient(mock_mode=True)
                            api_key = client._get_api_key()
                            # Should return from config (line 133)
                            assert api_key == 'AIzaSyConfigKey123'
    
    def test_generate_real_api_success(self, mock_image):
        """Test real API generate() with success response (lines 160-175)"""
        # Create a mock response object
        mock_response = Mock()
        mock_response.text = "Generated story text"
        
        # Create a mock model
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel', return_value=mock_model):
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        client = GeminiClient(mock_mode=False)
                        
                        # Test generate() in real mode (not mock)
                        result = client.generate([mock_image], "Test prompt")
                        
                        # Should parse success response (lines 171-175)
                        assert result['success'] is True
                        assert result['text'] == "Generated story text"
                        assert result['error'] is None
                        # Verify model.generate_content was called (line 169)
                        mock_model.generate_content.assert_called_once()
    
    def test_generate_real_api_timeout(self, mock_image):
        """Test real API generate() with timeout exception (lines 181-182)"""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("Request timed out after 30 seconds")
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel', return_value=mock_model):
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        client = GeminiClient(mock_mode=False)
                        
                        # Should raise APITimeoutError (line 182)
                        with pytest.raises(APITimeoutError) as exc_info:
                            client.generate([mock_image], "Test prompt")
                        
                        # Error message should contain timeout (already contains "timed out")
                        error_msg = str(exc_info.value).lower()
                        assert 'timeout' in error_msg or 'timed out' in error_msg
    
    def test_generate_real_api_rate_limit(self, mock_image):
        """Test real API generate() with rate limit exception (lines 183-184)"""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("429 Rate limit exceeded")
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel', return_value=mock_model):
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        client = GeminiClient(mock_mode=False)
                        
                        # Should raise APIRateLimitError (line 184)
                        with pytest.raises(APIRateLimitError) as exc_info:
                            client.generate([mock_image], "Test prompt")
                        
                        assert 'rate limit' in str(exc_info.value).lower()
    
    def test_generate_real_api_rate_limit_quota(self, mock_image):
        """Test real API generate() with quota exceeded (line 183)"""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("Quota exceeded for this API")
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel', return_value=mock_model):
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        client = GeminiClient(mock_mode=False)
                        
                        # Should raise APIRateLimitError (quota branch, line 183)
                        with pytest.raises(APIRateLimitError):
                            client.generate([mock_image], "Test prompt")
    
    def test_generate_real_api_invalid_response(self, mock_image):
        """Test real API generate() with invalid response (lines 185-186)"""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("Invalid response format")
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel', return_value=mock_model):
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        client = GeminiClient(mock_mode=False)
                        
                        # Should raise APIInvalidResponseError (line 186)
                        with pytest.raises(APIInvalidResponseError) as exc_info:
                            client.generate([mock_image], "Test prompt")
                        
                        assert 'invalid' in str(exc_info.value).lower()
    
    def test_generate_real_api_malformed_response(self, mock_image):
        """Test real API generate() with malformed response (line 185)"""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("Malformed JSON response")
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel', return_value=mock_model):
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        client = GeminiClient(mock_mode=False)
                        
                        # Should raise APIInvalidResponseError (malformed branch, line 185)
                        with pytest.raises(APIInvalidResponseError):
                            client.generate([mock_image], "Test prompt")
    
    def test_generate_real_api_generic_error(self, mock_image):
        """Test real API generate() with generic error (lines 187-188)"""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("Network connection failed")
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel', return_value=mock_model):
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        client = GeminiClient(mock_mode=False)
                        
                        # Should raise generic APIError (line 188)
                        with pytest.raises(APIError) as exc_info:
                            client.generate([mock_image], "Test prompt")
                        
                        assert 'API error' in str(exc_info.value)
    
    def test_generate_real_api_multiple_images(self, mock_image):
        """Test real API generate() with multiple images (lines 165-166)"""
        mock_response = Mock()
        mock_response.text = "Story with multiple images"
        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        
        with patch('google.generativeai.configure'):
            with patch('google.generativeai.GenerativeModel', return_value=mock_model):
                with patch('ai_story_imager.core.config.get_config') as mock_config:
                    from ai_story_imager.core.config import Config
                    mock_config.return_value = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyTestKey123',
                        default_model='gemini-2.5-flash'
                    )
                    with patch('ai_story_imager.services.gemini_client.GeminiClient._get_api_key', return_value='AIzaSyTestKey123'):
                        client = GeminiClient(mock_mode=False)
                        
                        images = [mock_image, mock_image, mock_image]
                        result = client.generate(images, "Test prompt")
                        
                        # Verify all images were added to content (line 165-166)
                        call_args = mock_model.generate_content.call_args[0][0]
                        assert len(call_args) == 4  # prompt + 3 images
                        assert call_args[0] == "Test prompt"
                        assert result['success'] is True
    
    def test_get_api_key_session_state_exception(self):
        """Test API key retrieval when session state access raises exception (lines 117-118)"""
        # Patch streamlit module to raise exception when accessed
        with patch.dict(os.environ, {}, clear=True):
            with patch('ai_story_imager.core.config.get_config') as mock_config:
                from ai_story_imager.core.config import Config
                mock_config.return_value = Config(test_mode=False, gemini_api_key=None)
                
                # Create a mock that raises exception when hasattr is called
                mock_streamlit = Mock()
                mock_streamlit.session_state = Mock(side_effect=AttributeError("No session"))
                
                # Patch sys.modules to replace streamlit with our mock
                import sys
                original_streamlit = sys.modules.get('streamlit')
                sys.modules['streamlit'] = mock_streamlit
                
                try:
                    client = GeminiClient(mock_mode=True)
                    # Should catch exception and continue (line 117-118)
                    api_key = client._get_api_key()
                    assert api_key == ''
                finally:
                    # Restore original
                    if original_streamlit:
                        sys.modules['streamlit'] = original_streamlit
                    elif 'streamlit' in sys.modules:
                        del sys.modules['streamlit']
    
    def test_get_api_key_secrets_exception(self):
        """Test API key retrieval when secrets access raises exception (lines 128-129)"""
        with patch.dict(os.environ, {'ALLOW_ENV_API_KEY': '1'}):
            with patch('streamlit.session_state', {}, create=True):
                # Mock streamlit.secrets to raise exception when accessing
                def raise_on_access(*args, **kwargs):
                    raise AttributeError("No secrets")
                
                with patch('streamlit.secrets', create=True) as mock_secrets:
                    # Make accessing secrets raise exception
                    mock_secrets.__getitem__ = raise_on_access
                    mock_secrets.__contains__ = raise_on_access
                    
                    # Mock get_config to return config with API key
                    from ai_story_imager.core.config import Config
                    test_config = Config(
                        test_mode=False,
                        gemini_api_key='AIzaSyConfigKey123'
                    )
                    
                    with patch('ai_story_imager.services.gemini_client.get_config', return_value=test_config):
                        with patch('ai_story_imager.core.config.get_config', return_value=test_config):
                            client = GeminiClient(mock_mode=True)
                            # Should catch exception and continue to config (line 128-129)
                            api_key = client._get_api_key()
                            assert api_key == 'AIzaSyConfigKey123'
    
    def test_mock_generate_analysis_scenario(self, mock_image):
        """Test mock generation with analysis scenario (line 215)"""
        client = GeminiClient(mock_mode=True)
        
        result = client.generate([mock_image], "Analyze images", {'mock_scenario': 'analysis'})
        
        # Should return analysis text (line 215)
        assert result['success'] is True
        assert 'OBJECTS:' in result['text']
        assert 'SCENE:' in result['text']
        assert result['error'] is None
    
    def test_mock_generate_story_with_visual_details(self, mock_image):
        """Test mock generation with visual details in prompt (line 241)"""
        client = GeminiClient(mock_mode=True)
        
        prompt = "Generate story with VISUAL DETAILS FROM IMAGES: Objects, scene, mood"
        result = client.generate([mock_image], prompt, {'mock_scenario': 'success'})
        
        # Should return story with visual grounding (line 241)
        assert result['success'] is True
        assert 'Sunset Voyage' in result['text'] or 'sunset' in result['text'].lower()
        assert len(result['text']) >= 100  # Should be at least 100 chars
        assert result['error'] is None
    
    def test_mock_generate_story_fallback(self, mock_image):
        """Test mock generation fallback when no visual details (line 247-248)"""
        client = GeminiClient(mock_mode=True)
        
        # Prompt without visual details triggers fallback
        prompt = "Generate a story"
        result = client.generate([mock_image], prompt, {'mock_scenario': 'success'})
        
        # Should return fallback story (line 247-248)
        assert result['success'] is True
        assert 'Enchanted Forest' in result['text'] or 'forest' in result['text'].lower()
        assert result['error'] is None






