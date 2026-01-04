"""
Prompt Builder
Constructs optimized prompts for Gemini API based on user settings.
"""

from typing import Dict, Any

# Constants
LENGTH_MAP: Dict[str, str] = {
    'short': '300-500 words',
    'medium': '800-1200 words',
    'long': '1500+ words'
}

DEFAULT_LENGTH: str = '800-1200 words'


class PromptBuilder:
    """Builds prompts for story generation"""
    
    def build_prompt(self, settings: Dict[str, Any], visual_details: str = "") -> str:
        """
        Build a comprehensive prompt from user settings and visual details
        
        Args:
            settings: Dictionary containing all story settings
            visual_details: String containing extracted visual details from image analysis
            
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
        
        word_count = LENGTH_MAP.get(story_length, DEFAULT_LENGTH)
        
        # Build creativity description
        creativity_desc = self._get_creativity_description(creativity)
        
        # Build the main prompt
        prompt = f"""Write a {genre.lower()} story based on the following images and their visual analysis.

VISUAL DETAILS FROM IMAGES:
{visual_details}

STORY REQUIREMENTS:
- Genre: {genre}
- Writing Style: {writing_style}
- Tone: {story_tone}
- Language: {language}
- Length: {word_count}
- Narrative Perspective: {narrative_perspective}
- Target Audience: {target_audience}
- Creativity Level: {creativity_desc}

CRITICAL STORY GUIDELINES:
1. The story MUST be grounded in the visual details provided above. Reference specific objects, scenes, colors, and elements from the images.

2. If the images show a beach at sunset with a boat, the story MUST mention the beach, sunset, and boat (not a random forest or unrelated scene).

3. Use the visual details as the foundation for:
   - Setting and environment (must match what's in the images)
   - Objects and elements (must reference visible items)
   - Mood and atmosphere (must reflect the visual tone)
   - Characters (if people are visible, describe them accurately; if not, create characters that fit the scene)

4. Write in a {writing_style.lower()} style with a {story_tone.lower()} tone.

5. The story should be appropriate for {target_audience.lower()}.

6. Use {narrative_perspective.lower()} perspective throughout.

7. Make the story approximately {word_count} in length.

8. Be {creativity_desc} in your interpretation, but ALWAYS stay grounded in the visual elements.

9. Create engaging characters and a compelling narrative arc that naturally emerges from the visual scene.

10. Ensure the story flows naturally and is well-structured.

"""
        
        if include_title:
            prompt += "11. Start the story with a creative, engaging title on the first line.\n\n"
        
        if allow_emojis:
            prompt += "12. You may use emojis sparingly to enhance the narrative (optional).\n\n"
        else:
            prompt += "12. Do not use emojis in the story.\n\n"
        
        prompt += """IMPORTANT REMINDERS:
- The story MUST reference and be grounded in the visual details from the images
- Do not create a story about something completely different from what's in the images
- If images show specific objects/scenes, those MUST appear in the story
- Make it immersive, engaging, and memorable while staying true to the visual content
- Ensure proper paragraph breaks and formatting
- Write the story directly, starting with the title if requested

Begin writing the story now:"""
        
        return prompt
    
    def _get_creativity_description(self, creativity: int) -> str:
        """
        Get creativity level description
        
        Args:
            creativity: Integer from 1-10
            
        Returns:
            String description of creativity level
        """
        if creativity <= 3:
            return "literal and straightforward"
        elif creativity <= 6:
            return "moderately creative with some imaginative elements"
        elif creativity <= 8:
            return "highly creative and imaginative"
        else:
            return "extremely creative, imaginative, and unconventional"

