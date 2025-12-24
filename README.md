# AI Story Imager

A Streamlit web application that transforms images into captivating stories using Google's Gemini AI. Upload images, configure your story preferences, and generate creative narratives inspired by your visuals.

## Features

- Multi-image upload support (JPG, PNG, WEBP)
- AI-powered story generation using Google Gemini
- Comprehensive story customization (genre, style, tone, length, perspective, audience)
- Real-time API key management via sidebar
- Story export functionality
- Clean, responsive user interface

## Installation

### Prerequisites

- Python 3.10 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**

   Choose one of the following methods:

   **Option A: Sidebar Input (Recommended)**
   - Run the app and enter your API key in the sidebar

   **Option B: Environment File**
   - Create a `.env` file in the project root:
     ```
     GEMINI_API_KEY=your_actual_api_key_here
     ```

   **Option C: Streamlit Secrets**
   - Create `.streamlit/secrets.toml`:
     ```toml
     GEMINI_API_KEY = "your_actual_api_key_here"
     ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

   The application will open at `http://localhost:8501`

## Usage

1. Enter your Gemini API key in the sidebar (API Configuration section)
2. Upload one or more images using the file uploader
3. Configure story settings in the sidebar (genre, style, tone, length, etc.)
4. Click "Generate Story" to create your narrative
5. Download or regenerate the story as needed

## Project Structure

```
ai-story-generator/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
└── utils/
    ├── gemini_client.py  # Gemini API client
    ├── prompt_builder.py # Prompt construction
    └── image_utils.py    # Image processing
```

## Dependencies

- streamlit>=1.28.0
- google-generativeai>=0.3.0
- pillow>=10.0.0
- python-dotenv>=1.0.0

## License

This project is open source and available for personal use.
