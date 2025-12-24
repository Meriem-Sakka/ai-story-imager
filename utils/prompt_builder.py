"""
Prompt Builder
Constructs optimized prompts for Gemini API based on user settings.
"""

from typing import Dict, Any

class PromptBuilder:
    """Builds prompts for story generation"""
    
    def build_prompt(self, settings: Dict[str, Any]) -> str:
        """
        Build a comprehensive prompt from user settings
        
        Args:
            settings: Dictionary containing all story settings
            
        Returns:
            Formatted prompt string
        """
        genre = settings.get('genre', 'Fantasy')
        writing_style = settings.get('writing_style', 'Cinematic')
        story_tone = settings.get('story_tone', 'Light')
        language = settings.get('language', 'English')
        story_length = settings.get('story_length', 'medium')
        narrative_perspective = settings.get('narrative_perspective', 'Third person limited')
        target_audience = settings.get('target_audience', 'Adults')
        creativity = settings.get('creativity', 7)
        allow_emojis = settings.get('allow_emojis', False)
        include_title = settings.get('include_title', True)
        
        # Map length to word count
        length_map = {
            'short': '300-500 words',
            'medium': '800-1200 words',
            'long': '1500+ words'
        }
        word_count = length_map.get(story_length, '800-1200 words')
        
        # Build creativity description
        creativity_desc = self._get_creativity_description(creativity)
        
        # Build the main prompt
        prompt = f"""Analyze the following images and write a {genre.lower()} story.

STORY REQUIREMENTS:
- Genre: {genre}
- Writing Style: {writing_style}
- Tone: {story_tone}
- Language: {language}
- Length: {word_count}
- Narrative Perspective: {narrative_perspective}
- Target Audience: {target_audience}
- Creativity Level: {creativity_desc}

STORY GUIDELINES:
1. Use the images as the main inspiration for:
   - Characters and their appearance
   - Setting and environment
   - Plot and story events
   - Mood and atmosphere

2. Write in a {writing_style.lower()} style with a {story_tone.lower()} tone.

3. The story should be appropriate for {target_audience.lower()}.

4. Use {narrative_perspective.lower()} perspective throughout.

5. Make the story approximately {word_count} in length.

6. Be {creativity_desc} in your interpretation of the images.

7. Create engaging characters and a compelling narrative arc.

8. Ensure the story flows naturally and is well-structured.

"""
        
        if include_title:
            prompt += "9. Start the story with a creative, engaging title on the first line.\n\n"
        
        if allow_emojis:
            prompt += "10. You may use emojis sparingly to enhance the narrative (optional).\n\n"
        else:
            prompt += "10. Do not use emojis in the story.\n\n"
        
        prompt += """IMPORTANT:
- The story should be inspired by and reference the visual elements in the images
- Make it immersive, engaging, and memorable
- Ensure proper paragraph breaks and formatting
- Write the story directly, starting with the title if requested

Begin writing the story now:"""
        
        return prompt
    
    def _get_creativity_description(self, creativity: int) -> str:
        """Get creativity level description"""
        if creativity <= 3:
            return "literal and straightforward"
        elif creativity <= 6:
            return "moderately creative with some imaginative elements"
        elif creativity <= 8:
            return "highly creative and imaginative"
        else:
            return "extremely creative, imaginative, and unconventional"

