"""
AI Story Imager
A Streamlit app that generates stories from images using Google Gemini API.

Run with: streamlit run app.py
"""

import streamlit as st
import os
from PIL import Image
import io
from utils.gemini_client import GeminiClient
from utils.prompt_builder import PromptBuilder
from utils.image_utils import process_images, validate_images

# Page configuration
st.set_page_config(
    page_title="AI Story Imager",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
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
""", unsafe_allow_html=True)

# Initialize session state
if 'story_generated' not in st.session_state:
    st.session_state.story_generated = False
if 'generated_story' not in st.session_state:
    st.session_state.generated_story = ""
if 'story_title' not in st.session_state:
    st.session_state.story_title = ""
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

def main():
    # Header - Big Bold App Name
    st.markdown('<div style="text-align: center; margin: 3rem 0;">', unsafe_allow_html=True)
    st.markdown('<h1 class="app-name">AI Story Imager</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Transform your images into captivating stories with AI ✨</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Sidebar for settings
    with st.sidebar:
        # API Key Configuration Section
        st.header("🔑 API Configuration")
        st.markdown("---")
        
        api_key_input = st.text_input(
            "Gemini API Key",
            value=st.session_state.api_key,
            type="password",
            help="Enter your Google Gemini API key. Get one from https://makersuite.google.com/app/apikey",
            placeholder="AIzaSy..."
        )
        
        if api_key_input:
            st.session_state.api_key = api_key_input
            if api_key_input.startswith('AIza'):
                st.success("✅ API Key saved!")
            else:
                st.warning("⚠️ API key format may be incorrect (should start with 'AIza')")
        else:
            st.info("💡 Enter your API key above to generate stories")
        
        # Show API key status
        if st.session_state.api_key:
            st.caption(f"Key: {st.session_state.api_key[:10]}...{st.session_state.api_key[-4:]}")
            if st.button("🗑️ Clear API Key"):
                st.session_state.api_key = ""
                st.rerun()
        
        st.markdown("---")
        st.header("⚙️ Story Settings")
        
        # Genre selection
        genre_options = [
            "Fantasy", "Sci-Fi", "Romance", "Horror", "Mystery", 
            "Adventure", "Slice of Life", "Custom"
        ]
        genre = st.selectbox("🎭 Genre", genre_options)
        
        if genre == "Custom":
            genre = st.text_input("Enter custom genre", value="")
        
        # Writing Style
        style_options = [
            "Cinematic", "Poetic", "Dark", "Humorous", 
            "Children's book", "Epic", "Minimalist"
        ]
        writing_style = st.selectbox("✍️ Writing Style", style_options)
        
        # Story Tone
        tone_options = ["Light", "Emotional", "Dramatic", "Dark", "Inspirational"]
        story_tone = st.radio("🎨 Story Tone", tone_options, horizontal=True)
        
        # Language
        language_options = ["English", "French", "Spanish", "Arabic", "German", "Custom"]
        language = st.selectbox("🌍 Language", language_options)
        
        if language == "Custom":
            language = st.text_input("Enter custom language", value="English")
        
        # Story Length
        length_options = {
            "Short (300-500 words)": "short",
            "Medium (800-1200 words)": "medium",
            "Long (1500+ words)": "long"
        }
        length_label = st.selectbox("📏 Story Length", list(length_options.keys()))
        story_length = length_options[length_label]
        
        # Narrative Perspective
        perspective_options = [
            "First person",
            "Third person limited",
            "Third person omniscient"
        ]
        narrative_perspective = st.selectbox("👁️ Narrative Perspective", perspective_options)
        
        # Target Audience
        audience_options = ["Kids", "Teens", "Adults"]
        target_audience = st.selectbox("👥 Target Audience", audience_options)
        
        # Creativity Level
        creativity = st.slider("🎨 Creativity Level", 1, 10, 7, 
                              help="Low = literal interpretation, High = very imaginative")
        
        st.divider()
        
        # Advanced options
        with st.expander("🔧 Advanced Options"):
            include_title = st.checkbox("Generate Story Title", value=True)
            include_chapters = st.checkbox("Format as Chapters", value=False)
            allow_emojis = st.checkbox("Allow Emojis in Story", value=False)
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("🖼️ Upload Images")
        
        uploaded_files = st.file_uploader(
            "Choose images...",
            type=['jpg', 'jpeg', 'png', 'webp'],
            accept_multiple_files=True,
            help="Upload one or more images to inspire your story"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} image(s) uploaded successfully!")
            
            # Display image previews
            st.subheader("📸 Image Previews")
            for idx, uploaded_file in enumerate(uploaded_files):
                try:
                    image = Image.open(uploaded_file)
                    # Resize for display if too large
                    if image.size[0] > 800 or image.size[1] > 800:
                        image.thumbnail((800, 800), Image.Resampling.LANCZOS)
                    st.image(image, caption=f"Image {idx + 1}", use_container_width=True)
                except Exception as e:
                    st.error(f"Error displaying image {idx + 1}: {str(e)}")
    
    with col2:
        st.header("📖 Generated Story")
        
        if st.button("🚀 Generate Story", type="primary", use_container_width=True):
            if not uploaded_files:
                st.error("❌ Please upload at least one image first!")
            elif not st.session_state.api_key and not os.getenv('GEMINI_API_KEY'):
                st.error("❌ Please enter your Gemini API key in the sidebar first!")
                st.info("💡 Go to the sidebar → 🔑 API Configuration → Enter your API key\n"
                       "Get your key from: https://makersuite.google.com/app/apikey")
            else:
                generate_story(uploaded_files, {
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
                })
        
        # Display generated story
        if st.session_state.story_generated:
            st.markdown('<div class="story-container">', unsafe_allow_html=True)
            
            if st.session_state.story_title:
                st.markdown(f"## {st.session_state.story_title}")
                st.divider()
            
            st.markdown(st.session_state.generated_story)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Action buttons
            col_btn1, col_btn2, col_btn3 = st.columns(3)
            
            with col_btn1:
                if st.button("🔄 Regenerate Story"):
                    if uploaded_files:
                        generate_story(uploaded_files, {
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
                        })
            
            with col_btn2:
                if st.button("💾 Download Story"):
                    download_story()
            
            with col_btn3:
                if st.button("🗑️ Clear Story"):
                    st.session_state.story_generated = False
                    st.session_state.generated_story = ""
                    st.session_state.story_title = ""
                    st.rerun()
        else:
            st.info("👆 Upload images and click 'Generate Story' to create your AI-powered story!")

def generate_story(uploaded_files, settings):
    """Generate story from images using Gemini API"""
    
    try:
        with st.spinner("🤖 AI is crafting your story... This may take a moment..."):
            # Validate and process images
            images = validate_images(uploaded_files)
            if not images:
                st.error("❌ Failed to process images. Please try again.")
                return
            
            # Initialize Gemini client
            try:
                gemini_client = GeminiClient()
            except Exception as e:
                st.error(f"❌ API Configuration Error: {str(e)}")
                st.info("💡 Please enter your API key in the sidebar (🔑 API Configuration section) or set it in:\n"
                       "• Sidebar API Key input (recommended)\n"
                       "• .env file (GEMINI_API_KEY=your_key)\n"
                       "• .streamlit/secrets.toml\n"
                       "• Environment variables\n\n"
                       "Get your API key from: https://makersuite.google.com/app/apikey")
                return
            
            # Build prompt
            prompt_builder = PromptBuilder()
            prompt = prompt_builder.build_prompt(settings)
            
            # Generate story
            result = gemini_client.generate_story(images, prompt, settings)
            
            if result['success']:
                st.session_state.generated_story = result['story']
                st.session_state.story_title = result.get('title', '')
                st.session_state.story_generated = True
                st.success("✨ Story generated successfully!")
                st.rerun()
            else:
                st.error(f"❌ Story generation failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        st.error(f"❌ An error occurred: {str(e)}")
        st.info("💡 Please try again or check your API key configuration")

def download_story():
    """Download the generated story as a text file"""
    if st.session_state.generated_story:
        story_text = ""
        if st.session_state.story_title:
            story_text = f"{st.session_state.story_title}\n\n"
        story_text += st.session_state.generated_story
        
        st.download_button(
            label="📥 Download Story (TXT)",
            data=story_text,
            file_name=f"story_{st.session_state.story_title.replace(' ', '_') if st.session_state.story_title else 'untitled'}.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()

