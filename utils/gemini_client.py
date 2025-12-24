"""
Gemini API Client
Handles all interactions with Google Gemini API for story generation.
"""

import os
import google.generativeai as genai
from typing import List, Dict, Any
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
    def __init__(self):
        """Initialize Gemini client with API key"""
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set it in:\n"
                "1. Sidebar API Key input (recommended)\n"
                "2. .env file (GEMINI_API_KEY=your_key)\n"
                "3. .streamlit/secrets.toml (GEMINI_API_KEY = 'your_key')\n"
                "4. Environment variable (export GEMINI_API_KEY=your_key)\n\n"
                "Get your API key from: https://makersuite.google.com/app/apikey"
            )
        
        # Check if API key looks valid (starts with AIza)
        if not api_key.startswith('AIza'):
            raise ValueError(
                f"API key format appears invalid. Gemini API keys typically start with 'AIza'.\n"
                f"Your key starts with: {api_key[:5] if len(api_key) > 5 else 'too short'}\n"
                f"Please verify your API key in .env file or get a new one from:\n"
                f"https://makersuite.google.com/app/apikey"
            )
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.5 Flash model (or latest available)
        try:
            # Try gemini-2.5-flash first (as requested)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except:
            # Fallback to gemini-2.0-flash-exp (experimental)
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            except:
                # Fallback to gemini-1.5-flash
                try:
                    self.model = genai.GenerativeModel('gemini-1.5-flash')
                except:
                    # Final fallback to older models
                    try:
                        self.model = genai.GenerativeModel('gemini-pro-vision')
                    except:
                        self.model = genai.GenerativeModel('gemini-pro')
    
    def _get_api_key(self) -> str:
        """Get API key from session state, secrets, .env file, or environment variable"""
        # Priority 1: Try session state (user input in sidebar)
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and 'api_key' in st.session_state:
                api_key = st.session_state.get('api_key', '')
                if api_key:
                    return api_key
        except:
            pass
        
        # Priority 2: Try Streamlit secrets
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
                return st.secrets['GEMINI_API_KEY']
        except:
            pass
        
        # Priority 3: Try environment variable (loaded from .env file by dotenv)
        api_key = os.getenv('GEMINI_API_KEY', '')
        if api_key:
            return api_key
        
        # Return empty if not found
        return ''
    
    def generate_story(self, images: List[Image.Image], prompt: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a story from images and prompt
        
        Args:
            images: List of PIL Image objects
            prompt: Text prompt for story generation
            settings: Dictionary of story settings
            
        Returns:
            Dictionary with 'success', 'story', 'title' keys
        """
        try:
            # Prepare content for multimodal input
            content = [prompt]
            
            # Add images to content
            for img in images:
                content.append(img)
            
            # Generate content
            response = self.model.generate_content(content)
            
            story_text = response.text
            
            # Extract title if requested
            title = ""
            if settings.get('include_title', True):
                title = self._extract_title(story_text)
                if title:
                    # Remove title from story text
                    story_text = story_text.replace(title, '', 1).strip()
                    if story_text.startswith('\n'):
                        story_text = story_text[1:].strip()
            
            # Format story if chapters requested
            if settings.get('include_chapters', False):
                story_text = self._format_as_chapters(story_text)
            
            return {
                'success': True,
                'story': story_text,
                'title': title
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'story': '',
                'title': ''
            }
    
    def _extract_title(self, story_text: str) -> str:
        """Extract title from story text (usually first line or after 'Title:')"""
        lines = story_text.split('\n')
        
        # Look for common title patterns
        for i, line in enumerate(lines[:5]):  # Check first 5 lines
            line = line.strip()
            if not line:
                continue
            
            # Check if line looks like a title (short, no period, capitalized)
            if (len(line) < 100 and 
                not line.endswith('.') and 
                not line.endswith('!') and 
                not line.endswith('?') and
                line[0].isupper()):
                return line
        
        # If no title found, return empty
        return ""
    
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

