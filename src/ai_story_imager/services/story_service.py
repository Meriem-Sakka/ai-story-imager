"""
Story Service Layer
Business logic for story generation, image validation, and error handling.
"""

from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import io

from ai_story_imager.core.errors import (
    ImageValidationError,
    StoryGenerationError
)
from ai_story_imager.core.config import get_config
from ai_story_imager.services.gemini_client import GeminiClient
from ai_story_imager.utils.prompt_builder import PromptBuilder

# Constants
VALID_MIME_TYPES: List[str] = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
BYTES_PER_MB: int = 1024 * 1024
TITLE_MAX_LINES: int = 5
TITLE_MAX_LENGTH: int = 100

ANALYSIS_PROMPT: str = """Analyze these images in detail and provide a comprehensive description of what you see.

Extract and describe:
1. OBJECTS: List all visible objects, people, animals, vehicles, structures, etc.
2. SCENE: Describe the setting, location, environment (e.g., beach, forest, city, room)
3. MOOD/ATMOSPHERE: Describe the emotional tone and atmosphere (e.g., peaceful, dramatic, mysterious, joyful)
4. COLORS: Note the dominant colors and color palette
5. TIME OF DAY: Identify if it's morning, afternoon, evening, night, or unclear
6. WEATHER/CONDITIONS: Describe weather, lighting conditions, or environmental conditions
7. COMPOSITION: Note the arrangement, perspective, and focal points
8. ACTIVITY: Describe any actions, movements, or activities visible
9. DETAILS: Note any distinctive features, textures, patterns, or unique elements

Format your response as a structured description that can be used to generate a story that clearly references these visual elements. Be specific and detailed."""


def _convert_image_to_rgb(image: Image.Image) -> Image.Image:
    """Convert image to RGB mode if necessary"""
    if image.mode != 'RGB':
        return image.convert('RGB')
    return image


def _resize_image_if_needed(image: Image.Image, max_dimension: int) -> Image.Image:
    """Resize image if it exceeds maximum dimension"""
    if image.size[0] > max_dimension or image.size[1] > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return image


def _process_image_for_validation(image: Image.Image, max_dimension: int) -> Image.Image:
    """Process image: convert to RGB and resize if needed"""
    image = _convert_image_to_rgb(image)
    image = _resize_image_if_needed(image, max_dimension)
    return image


def _create_image_metadata(image: Image.Image, size_bytes: int) -> Dict[str, Any]:
    """Create metadata dictionary for validated image"""
    return {
        'size': image.size,
        'mode': image.mode,
        'format': image.format or 'Unknown',
        'file_size_bytes': size_bytes
    }


class StoryService:
    """Service layer for story generation"""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize story service
        
        Args:
            gemini_client: Optional GeminiClient instance. If None, creates a new one.
        """
        self.gemini_client = gemini_client or GeminiClient()
        self.prompt_builder = PromptBuilder()
        self.config = get_config()
    
    def validate_image(
        self, 
        file_bytes: bytes, 
        mime_type: str, 
        size_bytes: int,
        max_size_mb: Optional[int] = None
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        """
        Validate an uploaded image
        
        Args:
            file_bytes: Image file bytes
            mime_type: MIME type of the file
            size_bytes: File size in bytes
            max_size_mb: Maximum file size in MB (uses config default if None)
            
        Returns:
            Tuple of (validated PIL Image, metadata dict)
            
        Raises:
            ImageValidationError: If validation fails
        """
        max_size_mb = max_size_mb or self.config.max_image_size_mb
        max_size_bytes = max_size_mb * BYTES_PER_MB
        
        if size_bytes > max_size_bytes:
            file_size_mb = size_bytes / BYTES_PER_MB
            raise ImageValidationError(
                f"Image file too large. Maximum size is {max_size_mb}MB, "
                f"but file is {file_size_mb:.2f}MB"
            )
        
        if mime_type.lower() not in VALID_MIME_TYPES:
            raise ImageValidationError(
                f"Invalid file type: {mime_type}. "
                f"Supported types: {', '.join(VALID_MIME_TYPES)}"
            )
        
        try:
            image = Image.open(io.BytesIO(file_bytes))
            image = _process_image_for_validation(image, self.config.max_image_dimension)
            metadata = _create_image_metadata(image, size_bytes)
            return image, metadata
        except Exception as e:
            raise ImageValidationError(f"Failed to process image: {str(e)}")
    
    def analyze_images(
        self,
        images: List[Image.Image],
        gemini_client: Optional[GeminiClient] = None
    ) -> Dict[str, Any]:
        """
        Analyze images to extract visual details (objects, scene, mood, colors, etc.)
        
        Args:
            images: List of validated PIL Image objects
            gemini_client: Optional GeminiClient instance (for dependency injection in tests)
            
        Returns:
            Dictionary with 'success', 'details', 'error' keys
            'details' contains: objects, scene, mood, colors, time_of_day, weather, etc.
            
        Raises:
            StoryGenerationError: If image analysis fails
        """
        if not images:
            raise StoryGenerationError("No images provided for analysis")
        
        client = gemini_client or self.gemini_client
        config = self._get_mock_config(client, 'analysis')
        
        try:
            result = client.generate(images, ANALYSIS_PROMPT, config)
            
            if not result['success']:
                error_msg = result.get('error', 'Image analysis failed')
                raise StoryGenerationError(error_msg)
            
            return {
                'success': True,
                'details': result['text'],
                'error': None
            }
        except StoryGenerationError:
            raise
        except Exception as e:
            raise StoryGenerationError(f"Image analysis failed: {str(e)}")
    
    def generate_story(
        self,
        images: List[Image.Image],
        settings: Dict[str, Any],
        gemini_client: Optional[GeminiClient] = None
    ) -> Dict[str, Any]:
        """
        Generate a story from images and settings
        
        Args:
            images: List of validated PIL Image objects
            settings: Dictionary of story settings
            gemini_client: Optional GeminiClient instance (for dependency injection in tests)
            
        Returns:
            Dictionary with 'success', 'story', 'title', 'error' keys
            
        Raises:
            StoryGenerationError: If story generation fails
        """
        if not images:
            raise StoryGenerationError("No images provided for story generation")
        
        client = gemini_client or self.gemini_client
        
        try:
            analysis_result = self.analyze_images(images, client)
            if not analysis_result['success']:
                error_msg = analysis_result.get('error', 'Image analysis failed')
                raise StoryGenerationError(error_msg)
            
            prompt = self.prompt_builder.build_prompt(settings, analysis_result['details'])
            config = self._get_mock_config(client, settings.get('mock_scenario', 'success'))
            
            result = client.generate(images, prompt, config)
            if not result['success']:
                error_msg = result.get('error', 'Unknown error')
                raise StoryGenerationError(error_msg)
            
            story_text = result['text']
            title, story_text = self._extract_and_remove_title(story_text, settings)
            
            if settings.get('include_chapters', False):
                story_text = self._format_as_chapters(story_text)
            
            return {
                'success': True,
                'story': story_text,
                'title': title,
                'error': None
            }
        except StoryGenerationError:
            raise
        except Exception as e:
            raise StoryGenerationError(f"Story generation failed: {str(e)}")
    
    def _get_mock_config(self, client: GeminiClient, default_scenario: str) -> Dict[str, Any]:
        """Get mock config if client is in mock mode"""
        config = {}
        if hasattr(client, '_mock_mode') and client._mock_mode:
            config['mock_scenario'] = default_scenario
        return config
    
    def _extract_title(self, story_text: str) -> str:
        """
        Extract title from story text (usually first line)
        
        Args:
            story_text: Full story text
            
        Returns:
            Extracted title or empty string
        """
        lines = story_text.split('\n')
        
        for line in lines[:TITLE_MAX_LINES]:
            line = line.strip()
            if not line:
                continue
            
            if self._is_title_line(line):
                return line
        
        return ""
    
    def _is_title_line(self, line: str) -> bool:
        """Check if a line looks like a title"""
        if not line or not line[0].isupper():
            return False
        
        if len(line) >= TITLE_MAX_LENGTH:
            return False
        
        return not line.endswith(('.', '!', '?'))
    
    def _extract_and_remove_title(self, story_text: str, settings: Dict[str, Any]) -> Tuple[str, str]:
        """
        Extract title and remove it from story text if requested
        
        Args:
            story_text: Full story text
            settings: Story settings dictionary
            
        Returns:
            Tuple of (title, modified_story_text)
        """
        if not settings.get('include_title', True):
            return "", story_text
        
        title = self._extract_title(story_text)
        if not title:
            return "", story_text
        
        modified_text = story_text.replace(title, '', 1).strip()
        if modified_text.startswith('\n'):
            modified_text = modified_text[1:].strip()
        
        return title, modified_text
    
    def _format_as_chapters(self, story_text: str) -> str:
        """Format story text as chapters"""
        paragraphs = story_text.split('\n\n')
        formatted = []
        
        chapter_num = 1
        for para in paragraphs:
            if para.strip():
                formatted.append(f"## Chapter {chapter_num}\n\n{para}")
                chapter_num += 1
        
        return '\n\n'.join(formatted)

