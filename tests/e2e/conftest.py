"""
E2E test configuration and fixtures
"""

import pytest
import subprocess
import time
import os
from pathlib import Path
import urllib.request

# Set mock mode for E2E tests
os.environ["MOCK_GEMINI"] = "1"
os.environ["TEST_MODE"] = "1"


def wait_for_url(url: str, timeout_s: int = 30) -> None:
    """Wait for a URL to be ready (HTTP 200 response)"""
    start = time.time()
    last_err = None
    while time.time() - start < timeout_s:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return
        except Exception as e:
            last_err = e
            time.sleep(0.5)
    raise RuntimeError(f"Streamlit not ready at {url} after {timeout_s}s. Last error: {last_err}")


@pytest.fixture(scope="session")
def streamlit_server():
    """Start Streamlit server for E2E tests with proper readiness check"""
    output_dir = Path("test-output")
    output_dir.mkdir(exist_ok=True)

    stdout_path = output_dir / "streamlit-stdout.log"
    stderr_path = output_dir / "streamlit-stderr.log"

    env = {**os.environ, "MOCK_GEMINI": "1", "TEST_MODE": "1"}

    with open(stdout_path, "wb") as out, open(stderr_path, "wb") as err:
        process = subprocess.Popen(
            ["streamlit", "run", "app/streamlit_app.py", "--server.port", "8502", "--server.headless", "true"],
            stdout=out,
            stderr=err,
            env=env,
        )

        base_url = "http://localhost:8502"
        wait_for_url(base_url, timeout_s=45)

        yield base_url

        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture
def test_image_path():
    """Path to test image fixture"""
    # Use the tests/fixtures directory (parent of e2e)
    fixture_dir = Path(__file__).parent.parent / "fixtures"
    fixture_dir.mkdir(exist_ok=True)
    
    # Create a simple test image if it doesn't exist
    image_path = fixture_dir / "test_image.jpg"
    if not image_path.exists():
        from PIL import Image
        img = Image.new('RGB', (200, 200), color='blue')
        img.save(image_path, 'JPEG')
    
    return str(image_path)


@pytest.fixture
def invalid_file_path(tmp_path):
    """Path to invalid test file"""
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("This is not an image")
    return str(invalid_file)


@pytest.fixture(autouse=True)
def setup_test_output_dir(tmp_path):
    """Create test output directory for screenshots and traces"""
    output_dir = Path("test-output")
    output_dir.mkdir(exist_ok=True)
    yield output_dir


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Take screenshot on test failure"""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        # Get the page fixture if available
        if "page" in item.funcargs:
            page = item.funcargs["page"]
            try:
                # Take screenshot
                screenshot_path = f"test-output/failure-{item.name}.png"
                page.screenshot(path=screenshot_path, full_page=True)
                # Save page content for debugging
                content_path = f"test-output/failure-{item.name}.html"
                with open(content_path, "w", encoding="utf-8") as f:
                    f.write(page.content())
            except Exception as e:
                # If screenshot fails, log but don't fail the test
                print(f"Failed to take screenshot: {e}")
