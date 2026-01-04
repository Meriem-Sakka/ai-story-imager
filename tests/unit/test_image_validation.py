"""
Unit tests for image validation
"""

import pytest
import io
from PIL import Image
from ai_story_imager.services.story_service import StoryService
from ai_story_imager.core.errors import ImageValidationError


class TestImageValidation:
    """Test image validation functionality"""
    
    def test_valid_jpg_image(self, mock_image_bytes):
        """Test validation of valid JPG image"""
        service = StoryService()
        image, metadata = service.validate_image(
            mock_image_bytes,
            'image/jpeg',
            len(mock_image_bytes)
        )
        
        assert isinstance(image, Image.Image)
        assert image.mode == 'RGB'
        assert 'size' in metadata
        assert 'mode' in metadata
    
    def test_valid_png_image(self):
        """Test validation of valid PNG image"""
        service = StoryService()
        img = Image.new('RGB', (200, 200), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        png_bytes = img_bytes.getvalue()
        
        image, metadata = service.validate_image(
            png_bytes,
            'image/png',
            len(png_bytes)
        )
        
        assert isinstance(image, Image.Image)
        assert image.mode == 'RGB'
    
    def test_invalid_file_type(self):
        """Test rejection of invalid file type"""
        service = StoryService()
        invalid_bytes = b"This is not an image"
        
        with pytest.raises(ImageValidationError) as exc_info:
            service.validate_image(invalid_bytes, 'text/plain', len(invalid_bytes))
        
        assert 'Invalid file type' in str(exc_info.value)
    
    def test_oversized_image(self):
        """Test rejection of oversized image"""
        service = StoryService()
        # Create a large image (simulate >20MB)
        large_bytes = b'x' * (21 * 1024 * 1024)  # 21MB
        
        with pytest.raises(ImageValidationError) as exc_info:
            service.validate_image(large_bytes, 'image/jpeg', len(large_bytes))
        
        assert 'too large' in str(exc_info.value).lower()
        assert '20MB' in str(exc_info.value)
    
    def test_corrupt_image(self):
        """Test handling of corrupt image file"""
        service = StoryService()
        corrupt_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF'  # Invalid JPG header
        
        with pytest.raises(ImageValidationError):
            service.validate_image(corrupt_bytes, 'image/jpeg', len(corrupt_bytes))
    
    def test_empty_file(self):
        """Test rejection of empty file"""
        service = StoryService()
        empty_bytes = b''
        
        with pytest.raises(ImageValidationError):
            service.validate_image(empty_bytes, 'image/jpeg', 0)
    
    def test_image_resize_large_dimensions(self):
        """Test that large images are resized to max 2048x2048"""
        service = StoryService()
        # Create a large image (3000x3000)
        large_img = Image.new('RGB', (3000, 3000), color='red')
        img_bytes = io.BytesIO()
        large_img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        large_bytes = img_bytes.getvalue()
        
        image, metadata = service.validate_image(
            large_bytes,
            'image/jpeg',
            len(large_bytes)
        )
        
        # Should be resized to max 2048x2048
        assert image.size[0] <= 2048
        assert image.size[1] <= 2048
    
    def test_rgba_to_rgb_conversion(self):
        """Test that RGBA images are converted to RGB"""
        service = StoryService()
        rgba_img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img_bytes = io.BytesIO()
        rgba_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        rgba_bytes = img_bytes.getvalue()
        
        image, metadata = service.validate_image(
            rgba_bytes,
            'image/png',
            len(rgba_bytes)
        )
        
        assert image.mode == 'RGB'
    
    def test_webp_image(self):
        """Test validation of WEBP image"""
        service = StoryService()
        img = Image.new('RGB', (100, 100), color='purple')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='WEBP')
        img_bytes.seek(0)
        webp_bytes = img_bytes.getvalue()
        
        image, metadata = service.validate_image(
            webp_bytes,
            'image/webp',
            len(webp_bytes)
        )
        
        assert isinstance(image, Image.Image)
        assert image.mode == 'RGB'






