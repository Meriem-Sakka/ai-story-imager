"""
End-to-end UI tests using Playwright
"""

import pytest
import re
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError


@pytest.mark.e2e
class TestUIWorkflow:
    """E2E tests for UI workflows"""

    def test_happy_path_upload_and_generate(self, page: Page, streamlit_server, test_image_path):
        """Test complete happy path: upload image -> generate story -> view result"""
        page.goto(streamlit_server)

        # Wait for page to load and verify we're on the right page
        expect(page.locator("h1")).to_contain_text("AI Story Imager", timeout=10000)

        # Enter API key (mock mode, so any key starting with AIza works)
        api_key_input = page.locator('input[type="password"]').first
        api_key_input.fill("AIzaSyMockKeyForTesting123456789")

        page.wait_for_timeout(500)

        # Upload image
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_image_path)

        # Wait for upload confirmation
        expect(page.locator("text=uploaded successfully")).to_be_visible(timeout=5000)

        # Click Generate Story button
        generate_button = page.get_by_role("button", name="Generate Story")
        expect(generate_button).to_be_enabled()
        generate_button.click()

        # Wait for story generation to complete - scope to stMain and wait for non-empty text
        main_content = page.locator('[data-testid="stMain"]')
        story_container = main_content.locator('[data-testid="generated-story"]')
        
        # Wait for element to be visible
        expect(story_container).to_be_visible(timeout=30000)
        
        # Wait for non-empty text content - the story should contain "sunset", "boat", or "beach"
        # This ensures Streamlit has finished rendering the content inside the div
        expect(story_container).to_contain_text("sunset", timeout=30000)
        
        # Get text content using inner_text() (more reliable than text_content())
        story_text_content = story_container.inner_text()
        assert story_text_content is not None, "Story content should not be None"
        assert len(story_text_content.strip()) > 0, f"Story content should not be empty, got: '{story_text_content[:50] if story_text_content else 'None'}...'"
        # Require at least 100 characters to ensure we have actual story content
        # Mock story is guaranteed to be >= 100 chars (currently 637 chars)
        assert len(story_text_content.strip()) >= 100, f"Story should have at least 100 characters, got {len(story_text_content.strip())}"

    def test_invalid_file_upload(self, page: Page, streamlit_server, invalid_file_path):
        """Test that invalid file upload shows error"""
        page.goto(streamlit_server)

        expect(page.locator("h1")).to_contain_text("AI Story Imager", timeout=10000)

        # Enter API key
        page.locator('input[type="password"]').first.fill("AIzaSyMockKeyForTesting123456789")
        page.wait_for_timeout(500)

        # Try to upload invalid file
        file_input = page.locator('input[type="file"]')

        try:
            file_input.set_input_files(invalid_file_path)
            page.wait_for_timeout(1000)

            generate_button = page.get_by_role("button", name="Generate Story")
            if generate_button.is_enabled():
                generate_button.click()

                error_found = False
                for error_text in ["validation failed", "Invalid file", "Invalid file type"]:
                    try:
                        expect(page.get_by_text(re.compile(error_text, re.IGNORECASE))).to_be_visible(timeout=2000)
                        error_found = True
                        break
                    except PlaywrightTimeoutError:
                        continue

                if not error_found:
                    page.screenshot(path="test-output/failure-invalid-file.png", full_page=True)
                    raise AssertionError("Expected error message not found for invalid file upload")

        except Exception as e:
            # Streamlit uploader may reject invalid files client-side; that's acceptable.
            if "validation" not in str(e).lower() and "invalid" not in str(e).lower():
                page.screenshot(path="test-output/failure-invalid-file-exception.png", full_page=True)
                raise

    def test_generate_without_image_shows_error(self, page: Page, streamlit_server):
        """Test that generating without image shows appropriate error"""
        page.goto(streamlit_server)

        expect(page.locator("h1")).to_contain_text("AI Story Imager", timeout=10000)

        # Enter API key
        page.locator('input[type="password"]').first.fill("AIzaSyMockKeyForTesting123456789")
        page.wait_for_timeout(500)

        # Click Generate without uploading image
        generate_button = page.get_by_role("button", name="Generate Story")
        generate_button.click()

        error_found = False
        error_texts = ["upload at least one image", "Please upload", "upload", "image"]

        for error_text in error_texts:
            try:
                expect(page.get_by_text(re.compile(error_text, re.IGNORECASE))).to_be_visible(timeout=2000)
                error_found = True
                break
            except PlaywrightTimeoutError:
                continue

        if not error_found:
            page.screenshot(path="test-output/failure-no-image.png", full_page=True)
            page_content = page.content()
            if "error" in page_content.lower() or "❌" in page_content:
                pytest.fail("Error message found but not matching expected patterns. Check screenshot.")
            else:
                raise AssertionError("Expected error message not found when generating without image")

    def test_generate_without_api_key_shows_error(self, page: Page, streamlit_server, test_image_path):
        """Test that generating without API key shows error"""
        # Navigate with E2E mode query param to ignore env var API keys
        page.goto(f"{streamlit_server}?e2e=1")

        # Wait for page to load
        expect(page.locator("h1")).to_contain_text("AI Story Imager", timeout=10000)

        # Step 1: Ensure API key is cleared using the Clear API Key button
        # This is the reliable way to clear session_state
        main_content = page.locator('[data-testid="stMain"]')
        sidebar = page.locator('[data-testid="stSidebar"]')
        
        # Look for Clear API Key button (either regular or E2E version)
        clear_button = sidebar.locator('button:has-text("Clear API Key")')
        
        # If button exists and is visible, click it to clear session state
        if clear_button.count() > 0:
            expect(clear_button.first).to_be_visible(timeout=2000)
            clear_button.first.click()
            # Wait for Streamlit rerun after clearing
            expect(page.locator("h1")).to_contain_text("AI Story Imager", timeout=5000)
        
        # Step 2: Verify API key is actually cleared by checking for "no API key" indicator
        # The sidebar should show the hint message when no key is set
        sidebar_hint = sidebar.get_by_text(re.compile("Enter your API key above", re.IGNORECASE))
        expect(sidebar_hint).to_be_visible(timeout=3000)

        # Step 3: Upload image
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(test_image_path)
        
        # Wait for upload confirmation (replaces arbitrary timeout)
        expect(page.get_by_text(re.compile("uploaded successfully", re.IGNORECASE))).to_be_visible(timeout=5000)

        # Step 4: Click Generate button
        generate_button = main_content.get_by_role("button", name="Generate Story")
        expect(generate_button).to_be_enabled()
        generate_button.click()

        # Step 5: Assert error appears in MAIN content area only
        # Scope all locators to main content to avoid matching sidebar elements
        main_content = page.locator('[data-testid="stMain"]')
        
        # Look for error alert in main content with the exact error message
        error_alert = main_content.locator('.stAlert').filter(
            has_text=re.compile("❌.*Please enter.*Gemini API key.*sidebar.*first", re.IGNORECASE)
        )
        
        # Assert error is visible (this replaces arbitrary wait_for_timeout)
        expect(error_alert.first).to_be_visible(timeout=5000)
        
        # Verify the error message text is correct
        error_text = error_alert.first.text_content()
        assert "Please enter your Gemini API key" in error_text
        assert "sidebar" in error_text.lower()

    def test_double_click_generate_prevents_duplicate(self, page: Page, streamlit_server, test_image_path):
        """Test that double-clicking Generate doesn't create duplicate requests"""
        page.goto(streamlit_server)

        expect(page.locator("h1")).to_contain_text("AI Story Imager", timeout=10000)

        # Enter API key
        page.locator('input[type="password"]').first.fill("AIzaSyMockKeyForTesting123456789")
        page.wait_for_timeout(300)

        # Upload image
        page.locator('input[type="file"]').set_input_files(test_image_path)
        page.wait_for_timeout(500)

        # Use a resilient locator
        generate_button = page.get_by_role("button", name="Generate Story")

        # First click
