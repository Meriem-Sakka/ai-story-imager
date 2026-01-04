"""
Unit tests for prompt builder
"""

import pytest
from ai_story_imager.utils.prompt_builder import PromptBuilder


class TestPromptBuilder:
    """Test prompt building functionality"""
    
    def test_build_prompt_default_settings(self):
        """Test prompt building with default settings"""
        builder = PromptBuilder()
        settings = {
            'genre': 'Fantasy',
            'writing_style': 'Cinematic',
            'story_tone': 'Light',
            'language': 'English',
            'story_length': 'medium',
            'narrative_perspective': 'Third person limited',
            'target_audience': 'Adults',
            'creativity': 7,
            'include_title': True,
            'allow_emojis': False
        }
        
        prompt = builder.build_prompt(settings)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert 'Fantasy' in prompt
        assert 'Cinematic' in prompt
        assert 'Light' in prompt
        assert 'English' in prompt
        assert '800-1200 words' in prompt
        assert 'Third person limited' in prompt
        assert 'Adults' in prompt
    
    def test_build_prompt_custom_genre(self):
        """Test prompt with custom genre"""
        builder = PromptBuilder()
        settings = {
            'genre': 'Cyberpunk Noir',
            'writing_style': 'Dark',
            'story_tone': 'Dark',
            'language': 'English',
            'story_length': 'short',
            'narrative_perspective': 'First person',
            'target_audience': 'Adults',
            'creativity': 9,
            'include_title': True,
            'allow_emojis': False
        }
        
        prompt = builder.build_prompt(settings)
        
        assert 'Cyberpunk Noir' in prompt
        assert '300-500 words' in prompt
        assert 'First person' in prompt
    
    def test_build_prompt_with_title(self):
        """Test prompt includes title instruction when enabled"""
        builder = PromptBuilder()
        settings = {
            'genre': 'Fantasy',
            'writing_style': 'Cinematic',
            'story_tone': 'Light',
            'language': 'English',
            'story_length': 'medium',
            'narrative_perspective': 'Third person limited',
            'target_audience': 'Adults',
            'creativity': 7,
            'include_title': True,
            'allow_emojis': False
        }
        
        prompt = builder.build_prompt(settings)
        
        assert 'title' in prompt.lower()
        assert 'first line' in prompt.lower()
    
    def test_build_prompt_without_title(self):
        """Test prompt excludes title instruction when disabled"""
        builder = PromptBuilder()
        settings = {
            'genre': 'Fantasy',
            'writing_style': 'Cinematic',
            'story_tone': 'Light',
            'language': 'English',
            'story_length': 'medium',
            'narrative_perspective': 'Third person limited',
            'target_audience': 'Adults',
            'creativity': 7,
            'include_title': False,
            'allow_emojis': False
        }
        
        prompt = builder.build_prompt(settings)
        
        # Title instruction should not be prominent
        assert 'title' not in prompt.lower() or 'Start the story with' not in prompt
    
    def test_build_prompt_with_emojis(self):
        """Test prompt includes emoji instruction when enabled"""
        builder = PromptBuilder()
        settings = {
            'genre': 'Fantasy',
            'writing_style': 'Cinematic',
            'story_tone': 'Light',
            'language': 'English',
            'story_length': 'medium',
            'narrative_perspective': 'Third person limited',
            'target_audience': 'Adults',
            'creativity': 7,
            'include_title': True,
            'allow_emojis': True
        }
        
        prompt = builder.build_prompt(settings)
        
        assert 'emoji' in prompt.lower()
    
    def test_build_prompt_without_emojis(self):
        """Test prompt excludes emojis when disabled"""
        builder = PromptBuilder()
        settings = {
            'genre': 'Fantasy',
            'writing_style': 'Cinematic',
            'story_tone': 'Light',
            'language': 'English',
            'story_length': 'medium',
            'narrative_perspective': 'Third person limited',
            'target_audience': 'Adults',
            'creativity': 7,
            'include_title': True,
            'allow_emojis': False
        }
        
        prompt = builder.build_prompt(settings)
        
        assert 'do not use emojis' in prompt.lower() or 'no emojis' in prompt.lower()
    
    def test_build_prompt_different_lengths(self):
        """Test prompt with different story lengths"""
        builder = PromptBuilder()
        
        # Test short
        settings_short = {
            'genre': 'Fantasy',
            'writing_style': 'Cinematic',
            'story_tone': 'Light',
            'language': 'English',
            'story_length': 'short',
            'narrative_perspective': 'Third person limited',
            'target_audience': 'Adults',
            'creativity': 7,
            'include_title': True,
            'allow_emojis': False
        }
        prompt_short = builder.build_prompt(settings_short)
        assert '300-500 words' in prompt_short
        
        # Test long
        settings_long = {
            'genre': 'Fantasy',
            'writing_style': 'Cinematic',
            'story_tone': 'Light',
            'language': 'English',
            'story_length': 'long',
            'narrative_perspective': 'Third person limited',
            'target_audience': 'Adults',
            'creativity': 7,
            'include_title': True,
            'allow_emojis': False
        }
        prompt_long = builder.build_prompt(settings_long)
        assert '1500+ words' in prompt_long
    
    def test_creativity_description(self):
        """Test creativity level descriptions"""
        builder = PromptBuilder()
        
        # Low creativity
        settings_low = {
            'genre': 'Fantasy',
            'writing_style': 'Cinematic',
            'story_tone': 'Light',
            'language': 'English',
            'story_length': 'medium',
            'narrative_perspective': 'Third person limited',
            'target_audience': 'Adults',
            'creativity': 2,
            'include_title': True,
            'allow_emojis': False
        }
        prompt_low = builder.build_prompt(settings_low)
        assert 'literal' in prompt_low.lower() or 'straightforward' in prompt_low.lower()
        
        # High creativity
        settings_high = {
            'genre': 'Fantasy',
            'writing_style': 'Cinematic',
            'story_tone': 'Light',
            'language': 'English',
            'story_length': 'medium',
            'narrative_perspective': 'Third person limited',
            'target_audience': 'Adults',
            'creativity': 10,
            'include_title': True,
            'allow_emojis': False
        }
        prompt_high = builder.build_prompt(settings_high)
        assert 'creative' in prompt_high.lower() or 'imaginative' in prompt_high.lower()


