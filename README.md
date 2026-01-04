# AI Story Imager 📖✨

> Image-grounded storytelling powered by Google Gemini

AI Story Imager is a production-quality AI web application that analyzes one or more images and generates coherent, creative stories grounded in their visual content (objects, scenes, mood, colors).

Built with a clean architecture, strong error handling, and extensive automated testing, this project demonstrates how to design, test, and maintain an AI-driven system reliably.

## 🚀 Why this project matters

This project demonstrates real-world AI engineering and QA practices, not just model usage:

- Robust integration of a multimodal LLM (Google Gemini)
- Clear separation between AI logic, services, utilities, and UI
- Defensive handling of AI failures, invalid inputs, and edge cases
- 99% automated test coverage (unit, integration, E2E)
- CI pipeline enforcing quality gates

## 🧠 What it does

- Analyzes uploaded images to extract visual context
- Builds structured prompts grounded in image content
- Generates stories aligned with user preferences
- Optionally extracts titles and formats stories into chapters
- Provides a clean UI for interaction and export

## ✨ Key features

### Image-grounded story generation
Stories reference actual visual elements (objects, scenes, mood).

### Multi-image support
Combine multiple images into a single coherent narrative.

### Rich customization
Genre, style, tone, length, perspective, creativity level, audience.

### Resilient AI orchestration
Graceful handling of API timeouts, rate limits, and malformed responses.

### Secure API key handling
UI-based key input by default, environment variables disabled unless explicitly enabled.

### Exportable output
Download generated stories for offline use.

## 🧩 Architecture overview

```
UI (Streamlit)
   ↓
StoryService (business orchestration)
   ├─ Image analysis & validation
   ├─ Prompt construction
   ├─ Gemini client interaction
   └─ Post-processing (title, chapters)
   ↓
GeminiClient (LLM abstraction with mock support)
```

### Design principles

- Clean Architecture (core / services / utils)
- Side-effects isolated from pure logic
- Testability first (mockable AI, deterministic tests)

## 🛠️ Tech stack

- **Frontend**: Streamlit
- **AI / LLM**: Google Gemini API (gemini-2.5-flash)
- **Image processing**: Pillow (PIL)
- **Testing**:
  - pytest (unit & integration)
  - Playwright (E2E)
  - pytest-cov (coverage)
- **Code quality**: Ruff, Black
- **CI/CD**: GitHub Actions

## 🧪 Testing & quality

- 117 automated tests
- 99% total code coverage
- Unit, integration, and end-to-end coverage
- Mocked AI calls for deterministic tests
- Coverage enforced in CI

### Run tests locally

```bash
pytest -v
pytest --cov=ai_story_imager --cov-report=term-missing --cov-fail-under=80
```

## ⚙️ Running the project

### Prerequisites

- Python 3.10+
- Google Gemini API key

### Install & run

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

The app opens at `http://localhost:8501`.

### API key usage

- Enter the key directly in the UI (default & recommended)
- Environment variables are disabled unless explicitly enabled for development

## 📁 Project structure

```
src/ai_story_imager/
├── core/        # Configuration & custom errors
├── services/    # Business logic & AI orchestration
├── utils/       # Image processing & prompt construction
app/
├── streamlit_app.py   # UI entrypoint
tests/
├── unit/
├── integration/
├── e2e/
```

## 🔄 CI pipeline

- Linting (Ruff)
- Formatting check (Black)
- Unit & integration tests with coverage
- End-to-end UI tests (Playwright)
- Coverage threshold enforcement

## 🧠 What this project demonstrates

- Designing testable AI systems
- Handling unreliable AI outputs safely
- Writing meaningful tests for AI pipelines
- Enforcing quality gates with CI
- Clean separation of concerns in a real application

## 📄 License

Open-source, for personal and educational use.
