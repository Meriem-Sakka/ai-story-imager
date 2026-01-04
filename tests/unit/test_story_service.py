"""
Unit tests for story service layer
"""

import pytest
from unittest.mock import Mock, patch
from ai_story_imager.services.story_service import StoryService
from ai_story_imager.core.errors import (
    StoryGenerationError,
    APITimeoutError,
    APIRateLimitError,
    APIInvalidResponseError
)
from ai_story_imager.services.gemini_client import GeminiClient


@pytest.fixture
def service(mock_gemini_client):
    """StoryService instance with mock client"""
    return StoryService(gemini_client=mock_gemini_client)


def settings_with(**overrides):
    """Helper to create settings with overrides"""
    base = {
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
    return {**base, **overrides}


def client_generate_side_effect(*responses):
    """Helper to create mock client with generate side_effect"""
    client = Mock()
    client.generate.side_effect = responses
    client._mock_mode = False
    return client


class TestGenerateStory:
    """Tests for generate_story method"""
    
    def test_success(self, service, mock_image, sample_settings):
        """Successful story generation"""
        result = service.generate_story([mock_image], sample_settings)
        
        assert result['success'] is True
        assert 'story' in result
        assert len(result['story']) > 0
        assert 'title' in result
        assert result['error'] is None
    
    def test_with_title(self, service, mock_image, sample_settings):
        """Story generation with title extraction"""
        settings = settings_with(include_title=True)
        result = service.generate_story([mock_image], settings)
        
        assert result['success'] is True
        assert 'title' in result
    
    def test_without_title(self, service, mock_image, sample_settings):
        """Story generation without title"""
        settings = settings_with(include_title=False)
        result = service.generate_story([mock_image], settings)
        
        assert result['success'] is True
        assert result.get('title', '') == ''
    
    def test_with_chapters(self, service, mock_image, sample_settings):
        """Story generation with chapter formatting"""
        settings = settings_with(include_chapters=True)
        result = service.generate_story([mock_image], settings)
        
        assert result['success'] is True
        assert '## Chapter' in result['story'] or len(result['story']) > 0
    
    def test_no_images(self, service, sample_settings):
        """Fails with no images"""
        with pytest.raises(StoryGenerationError) as exc_info:
            service.generate_story([], sample_settings)
        
        assert 'No images' in str(exc_info.value)
    
    def test_multiple_images(self, service, mock_image, sample_settings):
        """Story generation with multiple images"""
        images = [mock_image, mock_image, mock_image]
        result = service.generate_story(images, sample_settings)
        
        assert result['success'] is True
        assert 'story' in result
    
    @pytest.mark.parametrize('scenario,error_class', [
        ('timeout', APITimeoutError),
        ('rate_limit', APIRateLimitError),
        ('invalid_response', APIInvalidResponseError),
    ])
    def test_api_errors(self, mock_image, sample_settings, scenario, error_class):
        """Test handling of API errors"""
        client = GeminiClient(mock_mode=True)
        service = StoryService(gemini_client=client)
        settings = settings_with(mock_scenario=scenario)
        
        with pytest.raises(error_class):
            service.generate_story([mock_image], settings)
    
    @pytest.mark.parametrize('error_key,expected_msg', [
        ('error', 'Analysis failed'),
        (None, 'Image analysis failed'),
    ])
    def test_analysis_failure(self, mock_image, sample_settings, error_key, expected_msg):
        """Test generate_story when analysis fails"""
        client = GeminiClient(mock_mode=True)
        service = StoryService(gemini_client=client)
        
        result = {'success': False}
        if error_key:
            result['error'] = 'Analysis failed'
        
        with patch.object(service, 'analyze_images', return_value=result):
            with pytest.raises(StoryGenerationError) as exc_info:
                service.generate_story([mock_image], sample_settings)
            
            assert expected_msg in str(exc_info.value)
    
    @pytest.mark.parametrize('error_key,expected_msg', [
        ('error', 'Story generation failed'),
        (None, 'Unknown error'),
    ])
    def test_api_failure(self, mock_image, sample_settings, error_key, expected_msg):
        """Test generate_story when API returns failure"""
        responses = [{'success': True, 'text': 'Analysis text'}]
        failure = {'success': False}
        if error_key:
            failure['error'] = 'Story generation failed'
        responses.append(failure)
        
        client = client_generate_side_effect(*responses)
        service = StoryService(gemini_client=client)
        
        with pytest.raises(StoryGenerationError) as exc_info:
            service.generate_story([mock_image], sample_settings)
        
        assert expected_msg in str(exc_info.value)
    
    def test_unexpected_exception(self, mock_image, sample_settings):
        """Test generate_story when unexpected exception is raised"""
        client = client_generate_side_effect(
            {'success': True, 'text': 'Analysis text'},
            RuntimeError("Unexpected runtime error")
        )
        service = StoryService(gemini_client=client)
        
        with pytest.raises(StoryGenerationError) as exc_info:
            service.generate_story([mock_image], sample_settings)
        
        assert 'Story generation failed' in str(exc_info.value)
        assert 'Unexpected runtime error' in str(exc_info.value)
    
    def test_story_generation_error_passthrough(self, mock_image, sample_settings):
        """Test generate_story re-raises StoryGenerationError"""
        original_error = StoryGenerationError("Original story error")
        client = client_generate_side_effect(
            {'success': True, 'text': 'Analysis text'},
            original_error
        )
        service = StoryService(gemini_client=client)
        
        with pytest.raises(StoryGenerationError) as exc_info:
            service.generate_story([mock_image], sample_settings)
        
        assert exc_info.value is original_error
    
    def test_title_extraction_with_newline_removal(self, mock_image, sample_settings):
        """Test title extraction and newline removal after title removal"""
        client = GeminiClient(mock_mode=True)
        service = StoryService(gemini_client=client)
        settings = settings_with(include_title=True)
        
        story_with_title = "The Great Adventure\n\nOnce upon a time..."
        
        with patch.object(client, 'generate', side_effect=[
            {'success': True, 'text': 'Analysis text'},
            {'success': True, 'text': story_with_title}
        ]):
            result = service.generate_story([mock_image], settings)
            
            assert result['title'] == "The Great Adventure"
            assert not result['story'].startswith('\n')
            assert result['story'].startswith('Once upon a time')
    
    def test_no_title_found(self, mock_image):
        """Test title extraction when no title can be extracted"""
        client = GeminiClient(mock_mode=True)
        service = StoryService(gemini_client=client)
        settings = settings_with(include_title=True, genre='Fantasy')
        
        story_without_title = "Once upon a time, there was a great adventure that began..."
        
        with patch.object(client, 'generate', side_effect=[
            {'success': True, 'text': 'Analysis text'},
            {'success': True, 'text': story_without_title}
        ]):
            result = service.generate_story([mock_image], settings)
            
            assert result['title'] == ""
            assert result['story'] == story_without_title


class TestAnalyzeImages:
    """Tests for analyze_images method"""
    
    def test_no_images(self, service):
        """Raises error when no images provided"""
        with pytest.raises(StoryGenerationError) as exc_info:
            service.analyze_images([])
        
        assert 'No images provided for analysis' in str(exc_info.value)
    
    @pytest.mark.parametrize('error_key,expected_msg', [
        ('error', 'Analysis failed due to API error'),
        (None, 'Image analysis failed'),
    ])
    def test_failure_response(self, service, mock_image, error_key, expected_msg):
        """Test analyze_images when client returns failure"""
        result = {'success': False}
        if error_key:
            result['error'] = 'Analysis failed due to API error'
        
        client = Mock()
        client.generate.return_value = result
        client._mock_mode = False
        
        with pytest.raises(StoryGenerationError) as exc_info:
            service.analyze_images([mock_image], client)
        
        assert expected_msg in str(exc_info.value)
    
    def test_unexpected_exception(self, service, mock_image):
        """Test analyze_images when client raises unexpected exception"""
        client = Mock()
        client.generate.side_effect = RuntimeError("Unexpected error occurred")
        client._mock_mode = False
        
        with pytest.raises(StoryGenerationError) as exc_info:
            service.analyze_images([mock_image], client)
        
        assert 'Image analysis failed' in str(exc_info.value)
        assert 'Unexpected error occurred' in str(exc_info.value)
    
    def test_story_generation_error_passthrough(self, service, mock_image):
        """Test analyze_images re-raises StoryGenerationError"""
        original_error = StoryGenerationError("Original analysis error")
        client = Mock()
        client.generate.side_effect = original_error
        client._mock_mode = False
        
        with pytest.raises(StoryGenerationError) as exc_info:
            service.analyze_images([mock_image], client)
        
        assert exc_info.value is original_error


class TestFormattingHelpers:
    """Tests for formatting helper methods"""
    
    def test_extract_title_with_title(self, service):
        """Title extraction from story with title"""
        story_with_title = "The Great Adventure\n\nOnce upon a time..."
        title = service._extract_title(story_with_title)
        assert title == "The Great Adventure"
    
    def test_extract_title_without_title(self, service):
        """Title extraction from story without title"""
        story_no_title = "Once upon a time, there was a..."
        title = service._extract_title(story_no_title)
        assert title == ""
    
    def test_extract_title_skips_empty_lines(self, service):
        """Title extraction skips empty lines"""
        story_text = "\n\n\nThe Great Adventure\n\nOnce upon a time..."
        title = service._extract_title(story_text)
        assert title == "The Great Adventure"
    
    def test_format_as_chapters(self, service):
        """Chapter formatting with multiple paragraphs"""
        story_text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        formatted = service._format_as_chapters(story_text)
        
        assert "## Chapter 1" in formatted
        assert "## Chapter 2" in formatted
        assert "## Chapter 3" in formatted
    
    def test_format_as_chapters_single_paragraph(self, service):
        """Chapter formatting with single paragraph"""
        story_text = "This is a single paragraph story with no breaks."
        formatted = service._format_as_chapters(story_text)
        
        assert "## Chapter 1" in formatted
        assert story_text in formatted
    
    def test_format_as_chapters_empty_paragraphs(self, service):
        """Chapter formatting skips empty paragraphs"""
        story_text = "Chapter one.\n\n\n\nChapter two."
        formatted = service._format_as_chapters(story_text)
        
        assert "## Chapter 1" in formatted
        assert "## Chapter 2" in formatted
        assert formatted.count("## Chapter") == 2
