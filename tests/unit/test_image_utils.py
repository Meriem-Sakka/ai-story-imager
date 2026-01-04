"""
Unit tests for image_utils module
Tests the utility functions directly, not through StoryService
"""

import pytest
import io
from PIL import Image
from unittest.mock import patch
from ai_story_imager.utils import image_utils
from ai_story_imager.utils.image_utils import (
    validate_images,
    process_images,
    get_image_info
)


class MockUploadedFile(io.BytesIO):
    """
    Helper class that simulates Streamlit UploadedFile
    Extends BytesIO to add file-like behavior with name and type attributes
    """
    def __init__(self, data: bytes, name: str = "test.jpg", type: str = "image/jpeg"):
        super().__init__(data)
        self.name = name
        self.type = type
    
    def seek(self, offset, whence=io.SEEK_SET):
        """Override seek to ensure it works correctly"""
        return super().seek(offset, whence)
    
    def tell(self):
        """Override tell to return current position"""
        return super().tell()
    
    def read(self, size=-1):
        """Override read to return bytes"""
        return super().read(size)


class TestValidateImages:
    """Test validate_images function"""
    
    def test_validate_normal_image(self):
        """Test loading and validating a normal image"""
        # Create a valid JPEG image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Use real file-like object
        uploaded_file = MockUploadedFile(img_bytes.getvalue(), "test.jpg", "image/jpeg")
        
        result = validate_images([uploaded_file])
        
        assert len(result) == 1
        assert isinstance(result[0], Image.Image)
        assert result[0].mode == 'RGB'
        assert result[0].size == (100, 100)
    
    def test_validate_multiple_images(self):
        """Test validating multiple images"""
        # Create two valid images
        img1 = Image.new('RGB', (50, 50), color='blue')
        img1_bytes = io.BytesIO()
        img1.save(img1_bytes, format='JPEG')
        
        img2 = Image.new('RGB', (75, 75), color='green')
        img2_bytes = io.BytesIO()
        img2.save(img2_bytes, format='PNG')
        
        uploaded_file1 = MockUploadedFile(img1_bytes.getvalue(), "test1.jpg", "image/jpeg")
        uploaded_file2 = MockUploadedFile(img2_bytes.getvalue(), "test2.png", "image/png")
        
        result = validate_images([uploaded_file1, uploaded_file2])
        
        assert len(result) == 2
        assert all(isinstance(img, Image.Image) for img in result)
        assert all(img.mode == 'RGB' for img in result)
    
    def test_handle_none_file_input(self):
        """Test handling of None file input"""
        # None should be handled gracefully
        result = validate_images([None])
        assert len(result) == 0
    
    def test_handle_empty_file_zero_size(self):
        """Test handling of empty/zero-size file"""
        # Create an empty file
        empty_file = MockUploadedFile(b'', "empty.jpg", "image/jpeg")
        
        result = validate_images([empty_file])
        
        # Should skip empty files (Image.open will fail)
        assert len(result) == 0
    
    def test_handle_invalid_file_path_missing_file(self):
        """Test handling of missing/invalid file path - exception during Image.open"""
        # Create a file that will cause Image.open to raise an error
        invalid_data = b'invalid image data'
        invalid_file = MockUploadedFile(invalid_data, "invalid.jpg", "image/jpeg")
        
        # Image.open will raise an exception when trying to open invalid data
        result = validate_images([invalid_file])
        
        # Should skip invalid files and return empty list (caught by except block)
        assert len(result) == 0
    
    def test_handle_corrupted_bytes(self):
        """Test handling of corrupted image bytes (not a valid image)"""
        # Create corrupted bytes that look like they might be an image but aren't
        # This will cause Image.open to raise an exception
        corrupt_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb' + b'x' * 100
        corrupt_file = MockUploadedFile(corrupt_bytes, "corrupt.jpg", "image/jpeg")
        
        # Image.open will fail on corrupted data (triggers except block)
        result = validate_images([corrupt_file])
        
        # Should skip corrupted images and return empty list
        assert len(result) == 0
    
    def test_handle_unsupported_content_non_image_bytes(self):
        """Test that unsupported content (non-image bytes) is rejected"""
        # Create a text file (not an image) - triggers exception in Image.open
        text_content = b"This is not an image file at all, just plain text"
        text_file = MockUploadedFile(text_content, "text.txt", "text/plain")
        
        # Image.open will fail on non-image data (triggers except block)
        result = validate_images([text_file])
        
        # Should skip unsupported files
        assert len(result) == 0
    
    def test_resize_large_image_dimension_branch(self):
        """Test that large images trigger resize branch (image.size[0] > max_dimension)"""
        # Create a large image (3000x3000) - triggers resize branch
        large_img = Image.new('RGB', (3000, 3000), color='purple')
        img_bytes = io.BytesIO()
        large_img.save(img_bytes, format='JPEG')
        
        uploaded_file = MockUploadedFile(img_bytes.getvalue(), "large.jpg", "image/jpeg")
        
        result = validate_images([uploaded_file])
        
        assert len(result) == 1
        # Should be resized to max 2048x2048 (triggers line 45-46)
        assert result[0].size[0] <= 2048
        assert result[0].size[1] <= 2048
    
    def test_resize_large_image_height_branch(self):
        """Test resize branch when height exceeds max_dimension"""
        # Create image where height > max_dimension (triggers line 45)
        tall_img = Image.new('RGB', (1000, 3000), color='blue')
        img_bytes = io.BytesIO()
        tall_img.save(img_bytes, format='JPEG')
        
        uploaded_file = MockUploadedFile(img_bytes.getvalue(), "tall.jpg", "image/jpeg")
        
        result = validate_images([uploaded_file])
        
        assert len(result) == 1
        assert result[0].size[1] <= 2048  # Height should be resized
    
    def test_convert_rgba_to_rgb_mode_branch(self):
        """Test that RGBA images trigger mode conversion branch (image.mode != 'RGB')"""
        # Create RGBA image - triggers line 40-41
        rgba_img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img_bytes = io.BytesIO()
        rgba_img.save(img_bytes, format='PNG')
        
        uploaded_file = MockUploadedFile(img_bytes.getvalue(), "rgba.png", "image/png")
        
        result = validate_images([uploaded_file])
        
        assert len(result) == 1
        assert result[0].mode == 'RGB'  # Should be converted from RGBA (line 41)
    
    def test_image_already_rgb_no_conversion(self):
        """Test that RGB images don't trigger conversion branch"""
        # Create RGB image - should NOT trigger line 40-41
        rgb_img = Image.new('RGB', (100, 100), color='green')
        img_bytes = io.BytesIO()
        rgb_img.save(img_bytes, format='JPEG')
        
        uploaded_file = MockUploadedFile(img_bytes.getvalue(), "rgb.jpg", "image/jpeg")
        
        result = validate_images([uploaded_file])
        
        assert len(result) == 1
        assert result[0].mode == 'RGB'  # Already RGB, no conversion needed
    
    def test_convert_palette_to_rgb(self):
        """Test that palette mode images trigger mode conversion branch"""
        # Create a palette mode image - triggers line 40-41
        palette_img = Image.new('P', (100, 100))
        # Create a valid palette (256 colors * 3 RGB values = 768 values, each 0-255)
        palette_data = [min(i % 256, 255) for i in range(768)]
        palette_img.putpalette(palette_data)
        img_bytes = io.BytesIO()
        palette_img.save(img_bytes, format='PNG')
        
        uploaded_file = MockUploadedFile(img_bytes.getvalue(), "palette.png", "image/png")
        
        result = validate_images([uploaded_file])
        
        assert len(result) == 1
        assert result[0].mode == 'RGB'  # Should be converted from P (line 41)
    
    def test_skip_oversized_file_size_limit_branch(self):
        """Test that files exceeding size limit trigger continue branch (line 33-34)"""
        # Create a large file that exceeds size limit
        # We need actual bytes to make tell() work correctly
        large_data = b'x' * (21 * 1024 * 1024)  # 21MB (exceeds 20MB default)
        large_file = MockUploadedFile(large_data, "large.jpg", "image/jpeg")
        
        result = validate_images([large_file])
        
        # Should skip oversized files (triggers line 33-34 continue)
        assert len(result) == 0
    
    def test_file_within_size_limit(self):
        """Test that files within size limit are processed"""
        # Create a small valid image (well under 20MB)
        small_img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        small_img.save(img_bytes, format='JPEG')
        
        uploaded_file = MockUploadedFile(img_bytes.getvalue(), "small.jpg", "image/jpeg")
        
        result = validate_images([uploaded_file])
        
        # Should process file (does NOT trigger line 33-34)
        assert len(result) == 1
    
    def test_empty_file_list(self):
        """Test handling of empty file list"""
        result = validate_images([])
        assert result == []
    
    def test_mixed_valid_invalid_files(self):
        """Test that valid files are kept and invalid ones are skipped (triggers except block)"""
        # Valid image
        valid_img = Image.new('RGB', (50, 50), color='red')
        valid_bytes = io.BytesIO()
        valid_img.save(valid_bytes, format='JPEG')
        
        uploaded_valid = MockUploadedFile(valid_bytes.getvalue(), "valid.jpg", "image/jpeg")
        
        # Invalid file (corrupted) - will trigger except block (line 50-52)
        corrupt_bytes = b'not an image at all'
        uploaded_invalid = MockUploadedFile(corrupt_bytes, "invalid.jpg", "image/jpeg")
        
        result = validate_images([uploaded_valid, uploaded_invalid])
        
        # Should only return the valid image (invalid caught by except block)
        assert len(result) == 1
        assert isinstance(result[0], Image.Image)
    
    def test_exception_during_seek_operation(self):
        """Test exception handling when seek operation fails"""
        # Create a file-like object that raises exception on seek
        class FaultyFile(io.BytesIO):
            def seek(self, offset, whence=io.SEEK_SET):
                raise IOError("Seek failed")
        
        faulty_file = FaultyFile(b'some data')
        faulty_file.name = "faulty.jpg"
        faulty_file.type = "image/jpeg"
        
        # Should catch exception and skip file (triggers except block line 50-52)
        result = validate_images([faulty_file])
        assert len(result) == 0
    
    def test_exception_during_tell_operation(self):
        """Test exception handling when tell operation fails"""
        # Create a file-like object that raises exception on tell
        class FaultyFile(io.BytesIO):
            def tell(self):
                raise IOError("Tell failed")
        
        faulty_file = FaultyFile(b'some data')
        faulty_file.name = "faulty.jpg"
        faulty_file.type = "image/jpeg"
        
        # Should catch exception and skip file (triggers except block line 50-52)
        result = validate_images([faulty_file])
        assert len(result) == 0


class TestProcessImages:
    """Test process_images function"""
    
    def test_process_normal_image_no_conversion_no_resize(self):
        """Test processing a normal RGB image - no conversion, no resize branches"""
        # RGB image, small size - should NOT trigger line 72-73 or 77-78
        img = Image.new('RGB', (100, 100), color='blue')
        
        result = process_images([img])
        
        assert len(result) == 1
        assert result[0].mode == 'RGB'
        assert result[0].size == (100, 100)
    
    def test_convert_rgba_to_rgb_mode_branch(self):
        """Test that RGBA images trigger mode conversion branch (line 72-73)"""
        rgba_img = Image.new('RGBA', (100, 100), color=(0, 255, 0, 200))
        
        result = process_images([rgba_img])
        
        assert len(result) == 1
        assert result[0].mode == 'RGB'  # Converted (line 73)
    
    def test_resize_large_image_width_branch(self):
        """Test that large images trigger resize branch (line 77-78)"""
        # Width exceeds max_dimension
        large_img = Image.new('RGB', (3000, 1000), color='yellow')
        
        result = process_images([large_img])
        
        assert len(result) == 1
        assert result[0].size[0] <= 2048  # Resized (line 78)
        assert result[0].size[1] <= 2048
    
    def test_resize_large_image_height_branch(self):
        """Test resize branch when height exceeds max_dimension"""
        # Height exceeds max_dimension
        tall_img = Image.new('RGB', (1000, 3000), color='orange')
        
        result = process_images([tall_img])
        
        assert len(result) == 1
        assert result[0].size[1] <= 2048  # Height resized (line 78)
    
    def test_process_multiple_images(self):
        """Test processing multiple images"""
        img1 = Image.new('RGB', (50, 50), color='red')
        img2 = Image.new('RGBA', (75, 75), color=(0, 0, 255, 150))
        img3 = Image.new('RGB', (2500, 2500), color='green')
        
        result = process_images([img1, img2, img3])
        
        assert len(result) == 3
        assert all(img.mode == 'RGB' for img in result)
        assert result[0].size == (50, 50)  # Small, no resize
        assert result[1].size == (75, 75)  # Small, no resize
        assert result[2].size[0] <= 2048  # Large, resized
        assert result[2].size[1] <= 2048
    
    def test_empty_image_list(self):
        """Test processing empty image list"""
        result = process_images([])
        assert result == []
    
    def test_preserve_aspect_ratio_on_resize(self):
        """Test that aspect ratio is preserved when resizing"""
        # Create a wide image (4000x2000)
        wide_img = Image.new('RGB', (4000, 2000), color='orange')
        
        result = process_images([wide_img])
        
        assert len(result) == 1
        # Should maintain aspect ratio (2:1)
        assert result[0].size[0] <= 2048
        assert result[0].size[1] <= 2048
        # Aspect ratio should be approximately maintained
        aspect_ratio = result[0].size[0] / result[0].size[1]
        assert 1.8 <= aspect_ratio <= 2.2  # Allow small rounding


class TestGetImageInfo:
    """Test get_image_info function"""
    
    def test_get_info_rgb_image(self):
        """Test getting info from RGB image"""
        img = Image.new('RGB', (200, 150), color='red')
        
        info = get_image_info(img)
        
        assert info['size'] == (200, 150)
        assert info['mode'] == 'RGB'
        assert 'format' in info
    
    def test_get_info_rgba_image(self):
        """Test getting info from RGBA image"""
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        
        info = get_image_info(img)
        
        assert info['size'] == (100, 100)
        assert info['mode'] == 'RGBA'
    
    def test_get_info_with_format_hasattr_branch(self):
        """Test get_info when image has format attribute (line 90)"""
        img = Image.new('RGB', (50, 50), color='blue')
        # Save to give it a format
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        img_with_format = Image.open(img_bytes)
        
        info = get_image_info(img_with_format)
        
        assert info['size'] == (50, 50)
        assert info['mode'] == 'RGB'
        # Format should be present (triggers line 90 hasattr check)
        assert 'format' in info
    
    def test_get_info_no_format_hasattr_false_branch(self):
        """Test get_info when image has no format attribute (line 90 else branch)"""
        # Create a custom image class without format attribute
        class ImageWithoutFormat(Image.Image):
            def __init__(self, size, mode='RGB'):
                # Create a minimal image-like object
                super().__init__()
                self._size = size
                self._mode = mode
        
        # Create image and manually remove format attribute
        img = Image.new('RGB', (50, 50), color='blue')
        
        # Use patch to make hasattr return False for format
        with patch('builtins.hasattr') as mock_hasattr:
            def hasattr_side_effect(obj, attr):
                if attr == 'format':
                    return False
                return hasattr(obj, attr)
            mock_hasattr.side_effect = hasattr_side_effect
            
            info = get_image_info(img)
            
            assert info['size'] == (50, 50)
            assert info['mode'] == 'RGB'
            # Should return 'Unknown' when format not available (line 90 else branch)
            assert info['format'] == 'Unknown'
    
    def test_get_info_all_fields(self):
        """Test that all expected fields are present"""
        img = Image.new('RGB', (300, 400), color='purple')
        
        info = get_image_info(img)
        
        assert 'size' in info
        assert 'mode' in info
        assert 'format' in info
        assert isinstance(info['size'], tuple)
        assert isinstance(info['mode'], str)
        assert len(info['size']) == 2

