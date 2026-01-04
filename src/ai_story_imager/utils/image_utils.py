"""
Image Utilities
Handles image validation, processing, and optimization.
"""

from typing import List, Dict, Any
from PIL import Image
import io
from ai_story_imager.core.config import get_config


def _convert_to_rgb(image: Image.Image) -> Image.Image:
    """Convert image to RGB mode if necessary"""
    if image.mode != 'RGB':
        return image.convert('RGB')
    return image


def _resize_if_needed(image: Image.Image, max_dimension: int) -> Image.Image:
    """Resize image if it exceeds maximum dimension"""
    if image.size[0] > max_dimension or image.size[1] > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return image


def _process_single_image(image: Image.Image, max_dimension: int) -> Image.Image:
    """Process a single image: convert to RGB and resize if needed"""
    image = _convert_to_rgb(image)
    image = _resize_if_needed(image, max_dimension)
    return image


def validate_images(uploaded_files) -> List[Image.Image]:
    """
    Validate and process uploaded images
    
    Args:
        uploaded_files: List of uploaded file objects from Streamlit
        
    Returns:
        List of validated PIL Image objects
    """
    config = get_config()
    valid_images = []
    
    for uploaded_file in uploaded_files:
        try:
            # Check file size
            uploaded_file.seek(0, 2)  # Seek to end
            file_size = uploaded_file.tell()
            uploaded_file.seek(0)  # Reset to beginning
            
            max_file_size = config.max_image_size_mb * 1024 * 1024
            if file_size > max_file_size:
                continue  # Skip files that are too large
            
            # Open and validate image
            image = Image.open(uploaded_file)
            image = _process_single_image(image, config.max_image_dimension)
            valid_images.append(image)
        
        except Exception as e:
            # Skip invalid images
            continue
    
    return valid_images


def process_images(images: List[Image.Image]) -> List[Image.Image]:
    """
    Process images for optimal API usage
    
    Args:
        images: List of PIL Image objects
        
    Returns:
        List of processed PIL Image objects
    """
    config = get_config()
    return [_process_single_image(img, config.max_image_dimension) for img in images]


def get_image_info(image: Image.Image) -> Dict[str, Any]:
    """
    Get information about an image
    
    Args:
        image: PIL Image object
        
    Returns:
        Dictionary with 'size', 'mode', and 'format' keys
    """
    format_value = image.format if hasattr(image, 'format') else 'Unknown'
    return {
        'size': image.size,
        'mode': image.mode,
        'format': format_value
    }

