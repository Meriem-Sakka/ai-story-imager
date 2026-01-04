"""
AI Story Imager
A Streamlit app that generates stories from images using Google Gemini API.

Run with: streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import streamlit as st
import os
import html
from PIL import Image
from ai_story_imager.services.story_service import StoryService
from ai_story_imager.core.errors import (
    ImageValidationError,
    APIConfigurationError,
    APITimeoutError,
    APIRateLimitError,
    APIInvalidResponseError,
    StoryGenerationError
)

# Constants
API_KEY_URL = "https://makersuite.google.com/app/apikey"
API_KEY_PREFIX = "AIza"
IMAGE_PREVIEW_MAX_SIZE = 800
E2E_QUERY_PARAM = "e2e"

# UI Option Lists
GENRE_OPTIONS = [
    "Fantasy", "Sci-Fi", "Romance", "Horror", "Mystery",
    "Adventure", "Slice of Life", "Custom"
]

WRITING_STYLE_OPTIONS = [
    "Cinematic", "Poetic", "Dark", "Humorous",
    "Children's book", "Epic", "Minimalist"
]

TONE_OPTIONS = ["Light", "Emotional", "Dramatic", "Dark", "Inspirational"]

LANGUAGE_OPTIONS = ["English", "French", "Spanish", "Arabic", "German", "Custom"]

PERSPECTIVE_OPTIONS = [
    "First person",
    "Third person limited",
    "Third person omniscient"
]

AUDIENCE_OPTIONS = ["Kids", "Teens", "Adults"]

LENGTH_OPTIONS = {
    "Short (300-500 words)": "short",
    "Medium (800-1200 words)": "medium",
    "Long (1500+ words)": "long"
}

# CSS Styles
CUSTOM_CSS = """
    <style>
    .main-header {
        font-size: 4rem;
        font-weight: 900;
        color: #1f2937;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }
    .app-name {
        font-size: 5rem;
        font-weight: 900;
        color: #0ea5e9;
        text-align: center;
        margin: 2rem 0;
        letter-spacing: -0.02em;
        line-height: 1.1;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.5rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 400;
    }
    .story-container {
        background-color: #f9fafb;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        margin-top: 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
"""


def _is_e2e_mode() -> bool:
    """Check if E2E test mode is enabled via query parameter"""
    try:
        if hasattr(st, 'query_params'):
            e2e_param = st.query_params.get(E2E_QUERY_PARAM)
            return e2e_param == "1" if e2e_param is not None else False
    except (AttributeError, KeyError, TypeError):
        pass
    return False


def _is_env_api_key_allowed() -> bool:
    """Check if environment variable API keys are allowed"""
    return os.getenv('ALLOW_ENV_API_KEY', '').lower() in ('1', 'true', 'yes')


def _initialize_session_state() -> None:
    """Initialize Streamlit session state variables"""
    defaults = {
        'story_generated': False,
        'generated_story': "",
        'story_title': "",
        'api_key': ""
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def _render_header() -> None:
    """Render the application header"""
    st.markdown('<div style="text-align: center; margin: 3rem 0;">', unsafe_allow_html=True)
    st.markdown('<h1 class="app-name">AI Story Imager</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transform your images into captivating stories with AI ✨</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def _render_api_key_section(e2e_mode: bool) -> None:
    """Render API key configuration section in sidebar"""
    st.header("🔑 API Configuration")
    st.markdown("---")
    
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        help=f"Enter your Google Gemini API key. Get one from {API_KEY_URL}",
        placeholder="AIzaSy..."
    )
    
    if api_key_input:
        st.session_state.api_key = api_key_input
        if api_key_input.startswith(API_KEY_PREFIX):
            st.success("✅ API Key saved!")
        else:
            st.warning(f"⚠️ API key format may be incorrect (should start with '{API_KEY_PREFIX}')")
    else:
        st.info("💡 Enter your API key above to generate stories")
    
    # Show API key status and clear button
    if st.session_state.api_key:
        key_preview = f"{st.session_state.api_key[:10]}...{st.session_state.api_key[-4:]}"
        st.caption(f"Key: {key_preview}")
        if st.button("🗑️ Clear API Key"):
            st.session_state.api_key = ""
            st.rerun()
    elif e2e_mode:
        # Always show clear button in E2E mode for deterministic testing
        if st.button("🗑️ Clear API Key (E2E)", key="clear_api_key_e2e"):
            st.session_state.api_key = ""
            st.rerun()


def _render_story_settings() -> Dict[str, Any]:
    """Render story settings section and return settings dictionary"""
    st.markdown("---")
    st.header("⚙️ Story Settings")
    
    # Genre selection
    genre = st.selectbox("🎭 Genre", GENRE_OPTIONS)
    if genre == "Custom":
        genre = st.text_input("Enter custom genre", value="")
    
    # Writing Style
    writing_style = st.selectbox("✍️ Writing Style", WRITING_STYLE_OPTIONS)
    
    # Story Tone
    story_tone = st.radio("🎨 Story Tone", TONE_OPTIONS, horizontal=True)
    
    # Language
    language = st.selectbox("🌍 Language", LANGUAGE_OPTIONS)
    if language == "Custom":
        language = st.text_input("Enter custom language", value="English")
    
    # Story Length
    length_label = st.selectbox("📏 Story Length", list(LENGTH_OPTIONS.keys()))
    story_length = LENGTH_OPTIONS[length_label]
    
    # Narrative Perspective
    narrative_perspective = st.selectbox("👁️ Narrative Perspective", PERSPECTIVE_OPTIONS)
    
    # Target Audience
    target_audience = st.selectbox("👥 Target Audience", AUDIENCE_OPTIONS)
    
    # Creativity Level
    creativity = st.slider(
        "🎨 Creativity Level", 1, 10, 7,
        help="Low = literal interpretation, High = very imaginative"
    )
    
    st.divider()
    
    # Advanced options
    with st.expander("🔧 Advanced Options"):
        include_title = st.checkbox("Generate Story Title", value=True)
        include_chapters = st.checkbox("Format as Chapters", value=False)
        allow_emojis = st.checkbox("Allow Emojis in Story", value=False)
    
    return {
        'genre': genre,
        'writing_style': writing_style,
        'story_tone': story_tone,
        'language': language,
        'story_length': story_length,
        'narrative_perspective': narrative_perspective,
        'target_audience': target_audience,
        'creativity': creativity,
        'include_title': include_title,
        'include_chapters': include_chapters,
        'allow_emojis': allow_emojis
    }


def _render_image_upload_section() -> Optional[List]:
    """Render image upload section and return uploaded files"""
    st.header("🖼️ Upload Images")
    
    uploaded_files = st.file_uploader(
        "Choose images...",
        type=['jpg', 'jpeg', 'png', 'webp'],
        accept_multiple_files=True,
        help="Upload one or more images to inspire your story"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} image(s) uploaded successfully!")
        _render_image_previews(uploaded_files)
    
    return uploaded_files


def _render_image_previews(uploaded_files: List) -> None:
    """Render preview thumbnails for uploaded images"""
    st.subheader("📸 Image Previews")
    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            image = Image.open(uploaded_file)
            if image.size[0] > IMAGE_PREVIEW_MAX_SIZE or image.size[1] > IMAGE_PREVIEW_MAX_SIZE:
                image.thumbnail((IMAGE_PREVIEW_MAX_SIZE, IMAGE_PREVIEW_MAX_SIZE), Image.Resampling.LANCZOS)
            st.image(image, caption=f"Image {idx + 1}", use_container_width=True)
        except Exception as e:
            st.error(f"Error displaying image {idx + 1}: {str(e)}")


def _render_story_display(uploaded_files: Optional[List], settings: Dict[str, Any]) -> None:
    """Render story generation section and display generated story"""
    st.header("📖 Generated Story")
    
    if st.button("🚀 Generate Story", type="primary", use_container_width=True):
        if not uploaded_files:
            st.error("❌ Please upload at least one image first!")
        elif not _has_valid_api_key():
            st.error("❌ Please enter your Gemini API key in the sidebar first!")
            st.info(f"💡 Go to the sidebar → 🔑 API Configuration → Enter your API key\n"
                   f"Get your key from: {API_KEY_URL}")
        else:
            generate_story(uploaded_files, settings)
    
    if st.session_state.story_generated:
        _display_generated_story(uploaded_files, settings)
    else:
        st.info("👆 Upload images and click 'Generate Story' to create your AI-powered story!")


def _has_valid_api_key() -> bool:
    """Check if a valid API key is available (UI or env if allowed)"""
    ui_api_key = st.session_state.api_key
    env_api_key = None
    
    e2e_mode = _is_e2e_mode()
    allow_env = _is_env_api_key_allowed()
    
    if allow_env and not e2e_mode:
        env_api_key = os.getenv('GEMINI_API_KEY')
    
    return bool(ui_api_key) or bool(env_api_key)


def _display_generated_story(uploaded_files: Optional[List], settings: Dict[str, Any]) -> None:
    """Display the generated story with action buttons"""
    story_html = '<div class="story-container" data-testid="generated-story">'
    
    if st.session_state.story_title:
        title_escaped = html.escape(st.session_state.story_title)
        story_html += f'<h2>{title_escaped}</h2><hr/>'
    
    story_escaped = html.escape(st.session_state.generated_story)
    story_paragraphs = story_escaped.split('\n\n')
    formatted_story = ''.join([
        f'<p>{para.replace(chr(10), "<br/>")}</p>'
        for para in story_paragraphs
        if para.strip()
    ])
    story_html += formatted_story
    story_html += '</div>'
    
    st.markdown(story_html, unsafe_allow_html=True)
    
    # Action buttons
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("🔄 Regenerate Story"):
            if uploaded_files:
                generate_story(uploaded_files, settings)
    
    with col_btn2:
        if st.button("💾 Download Story"):
            download_story()
    
    with col_btn3:
        if st.button("🗑️ Clear Story"):
            _clear_story_state()


def _clear_story_state() -> None:
    """Clear story-related session state"""
    st.session_state.story_generated = False
    st.session_state.generated_story = ""
    st.session_state.story_title = ""
    st.rerun()


def _format_story_for_download() -> str:
    """Format story text for download (with title if available)"""
    story_text = ""
    if st.session_state.story_title:
        story_text = f"{st.session_state.story_title}\n\n"
    story_text += st.session_state.generated_story
    return story_text


def _get_download_filename() -> str:
    """Generate filename for story download"""
    if st.session_state.story_title:
        safe_title = st.session_state.story_title.replace(' ', '_')
        return f"story_{safe_title}.txt"
    return "story_untitled.txt"


def _handle_api_configuration_error(error: APIConfigurationError) -> None:
    """Handle API configuration errors with user-friendly messages"""
    st.error(f"❌ API Configuration Error: {str(error)}")
    st.info(
        f"💡 Please enter your API key in the sidebar (🔑 API Configuration section) or set it in:\n"
        f"• Sidebar API Key input (recommended)\n"
        f"• .env file (GEMINI_API_KEY=your_key)\n"
        f"• .streamlit/secrets.toml\n"
        f"• Environment variables\n\n"
        f"Get your API key from: {API_KEY_URL}"
    )


def _handle_api_error(error: Exception, error_type: str) -> None:
    """Handle API errors with standardized messages"""
    error_messages = {
        'timeout': ("❌ Request timed out", "💡 The API request took too long. Please try again or check your internet connection."),
        'rate_limit': ("❌ Rate limit exceeded", "💡 You've exceeded the API rate limit. Please wait a moment and try again."),
        'invalid_response': ("❌ Invalid API response", "💡 The API returned an unexpected response. Please try again."),
        'story_generation': ("❌ Story generation failed", None),
        'unexpected': ("❌ An unexpected error occurred", "💡 Please try again or check your configuration")
    }
    
    error_msg, info_msg = error_messages.get(error_type, error_messages['unexpected'])
    st.error(f"{error_msg}: {str(error)}")
    if info_msg:
        st.info(info_msg)


def _process_uploaded_images(uploaded_files: List, story_service: StoryService) -> List[Image.Image]:
    """Process and validate uploaded images"""
    images = []
    for uploaded_file in uploaded_files:
        try:
            uploaded_file.seek(0)
            file_bytes = uploaded_file.read()
            mime_type = uploaded_file.type
            size_bytes = len(file_bytes)
            
            image, _ = story_service.validate_image(file_bytes, mime_type, size_bytes)
            images.append(image)
        except ImageValidationError as e:
            st.error(f"❌ Image validation failed: {str(e)}")
            return []
        except Exception as e:
            st.error(f"❌ Failed to process image: {str(e)}")
            return []
    
    return images


def generate_story(uploaded_files: List, settings: Dict[str, Any]) -> None:
    """Generate story from images using Gemini API"""
    try:
        with st.spinner("🤖 AI is crafting your story... This may take a moment..."):
            try:
                story_service = StoryService()
            except APIConfigurationError as e:
                _handle_api_configuration_error(e)
                return
            
            images = _process_uploaded_images(uploaded_files, story_service)
            if not images:
                st.error("❌ No valid images to process. Please upload valid image files.")
                return
            
            result = story_service.generate_story(images, settings)
            
            if result['success']:
                st.session_state.generated_story = result['story']
                st.session_state.story_title = result.get('title', '')
                st.session_state.story_generated = True
                st.success("✨ Story generated successfully!")
                st.rerun()
            else:
                st.error(f"❌ Story generation failed: {result.get('error', 'Unknown error')}")
    
    except APITimeoutError as e:
        _handle_api_error(e, 'timeout')
    except APIRateLimitError as e:
        _handle_api_error(e, 'rate_limit')
    except APIInvalidResponseError as e:
        _handle_api_error(e, 'invalid_response')
    except StoryGenerationError as e:
        _handle_api_error(e, 'story_generation')
    except Exception as e:
        _handle_api_error(e, 'unexpected')


def download_story() -> None:
    """Download the generated story as a text file"""
    if st.session_state.generated_story:
        story_text = _format_story_for_download()
        filename = _get_download_filename()
        
        st.download_button(
            label="📥 Download Story (TXT)",
            data=story_text,
            file_name=filename,
            mime="text/plain"
        )


def main() -> None:
    """Main application entry point"""
    _initialize_session_state()
    _render_header()
    
    e2e_mode = _is_e2e_mode()
    
    # Sidebar for settings
    with st.sidebar:
        _render_api_key_section(e2e_mode)
        settings = _render_story_settings()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_files = _render_image_upload_section()
    
    with col2:
        _render_story_display(uploaded_files, settings)


if __name__ == "__main__":
    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Page configuration
    st.set_page_config(
        page_title="AI Story Imager",
        page_icon="📖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    main()
