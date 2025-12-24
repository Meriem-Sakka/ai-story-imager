"""
Image Utilities
Handles image validation, processing, and optimization.
"""

from typing import List, Tuple
from PIL import Image
import io

MAX_IMAGE_SIZE = (2048, 2048)  # Maximum dimensions for Gemini API
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB max file size

def validate_images(uploaded_files) -> List[Image.Image]:
    """
    Validate and process uploaded images
    
    Args:
        uploaded_files: List of uploaded file objects from Streamlit
        
    Returns:
        List of validated PIL Image objects
    """
    valid_images = []
    
    for uploaded_file in uploaded_files:
        try:
            # Check file size
            uploaded_file.seek(0, 2)  # Seek to end
            file_size = uploaded_file.tell()
            uploaded_file.seek(0)  # Reset to beginning
            
            if file_size > MAX_FILE_SIZE:
                continue  # Skip files that are too large
            
            # Open and validate image
            image = Image.open(uploaded_file)
            
            # Convert to RGB if necessary (handles RGBA, P, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            if image.size[0] > MAX_IMAGE_SIZE[0] or image.size[1] > MAX_IMAGE_SIZE[1]:
                image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
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
    processed = []
    
    for img in images:
        # Ensure RGB mode
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if needed
        if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
            img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        processed.append(img)
    
    return processed

def get_image_info(image: Image.Image) -> dict:
    """Get information about an image"""
    return {
        'size': image.size,
        'mode': image.mode,
        'format': image.format if hasattr(image, 'format') else 'Unknown'
    }

