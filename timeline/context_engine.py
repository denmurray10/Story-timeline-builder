import logging
from .models import Chapter, Event, Character, Book

logger = logging.getLogger(__name__)

class ContextEngine:
    """
    Aggregates story data to build a context-rich prompt for AI generation.
    """
    
    def __init__(self, chapter_id):
        self.chapter = Chapter.objects.get(pk=chapter_id)
        self.book = self.chapter.book
        
    def get_story_context(self):
        """
        Builds a dictionary of relevant story context.
        """
        context = {
            "book_title": self.book.title,
            "book_description": self.book.description,
            "chapter_title": self.chapter.title,
            "chapter_description": self.chapter.description,
            "series_order": self.book.series_order,
            "characters": self._get_active_characters(),
            "recent_events": self._get_recent_events(),
            "tone": "Engaging, Dramatic" # Default tone, could be dynamic later
        }
        return context

    def _get_active_characters(self):
        """
        Identifies characters relevant to this chapter.
        Prioritizes characters linked to events in this chapter.
        """
        # Get characters explicitly tagged in events for this chapter
        events = self.chapter.events.all()
        chars = set()
        for event in events:
            for char in event.characters.all():
                chars.add(char)
        
        # If no characters found in events, maybe fallback to Book's main cast?
        # For now, let's look for characters mentioned in the text (simple heuristic if needed)
        # But relying on structured data is better.
        
        character_data = []
        for char in chars:
            character_data.append({
                "name": char.name,
                "role": char.get_role_display(),
                "traits": char.traits,
                "motivation": char.motivation,
            })
            
        return character_data

    def _get_recent_events(self):
        """
        Summarizes the events in this chapter to guide narrative flow.
        """
        events = self.chapter.events.order_by('sequence_order')
        event_summaries = []
        for event in events:
            event_summaries.append(f"- {event.title}: {event.description} (Tone: {event.get_emotional_tone_display()})")
        return event_summaries

    def build_prompt_packet(self, current_text, instructions="Continue the story naturally."):
        """
        Constructs the final prompt string for the LLM.
        """
        context = self.get_story_context()
        
        # Format Character Info
        char_text = ""
        if context['characters']:
            char_text = "CHARACTERS IN SCENE:\n" + "\n".join(
                [f"- {c['name']} ({c['role']}): {c['traits']}. Motivation: {c['motivation']}" for c in context['characters']]
            )
        else:
            char_text = "CHARACTERS: (No specific characters tagged in this chapter yet. Use general book context.)"

        # Format Event Context
        event_text = ""
        if context['recent_events']:
            event_text = "CHAPTER OUTLINE / BEATS:\n" + "\n".join(context['recent_events'])
        
        prompt = f"""
You are an expert co-author assisting with a novel.
BOOK: {context['book_title']}
PREMISE: {context['book_description']}
CHAPTER: {context['chapter_title']}
SUMMARY: {context['chapter_description']}

{char_text}

{event_text}

TASK: {instructions}
Ensure the writing style matches the context. Maintain character voice and consistency.

CURRENT MANUSCRIPT TEXT:
{current_text[-2000:]} 
(End of current text)

GENERATION:
"""
        return prompt
