from django.shortcuts import get_object_or_404
from ..models import Book, Character, ActivityLog
from .ai_clients import _call_ai_json
import json

def synthesize_book_summary(book, use_reasoner=True):
    """
    Synthesises a global story summary from chapters and characters.
    Uses DeepSeek Reasoner for high-quality global understanding.
    """
    
    # 1. Gather Context
    chapters = book.chapters.all().order_by('chapter_number')
    # Filter to main characters for better focus
    characters = Character.objects.filter(user=book.user, introduction_book=book, role__in=['protagonist', 'antagonist'])
    if not characters.exists():
        characters = Character.objects.filter(user=book.user, role__in=['protagonist', 'antagonist'])[:5]
    
    # Only include chapters that have summaries
    summarized_chapters = [c for c in chapters if c.description]
    chapter_context = "\n".join([f"Ch {c.chapter_number} ({c.title}): {c.description[:1200]}" for c in summarized_chapters])
    char_context = "\n".join([f"- {c.name} ({c.get_role_display()}): {c.description[:600]}" for c in characters if c.description])
    
    if not chapter_context:
        return None, "No chapter summaries found. Please run a 'Deep Story Scan' first."

    prompt = f"""
    Write a compelling, professional story summary for the manuscript: "{book.title}".
    
    CHAPTER SUMMARIES:
    {chapter_context}
    
    KEY CHARACTERS:
    {char_context}
    
    INSTRUCTIONS:
    - Synthesise the above data into a high-level premise and plot summary (200-400 words).
    - Focus on the central conflict, key character arcs, and core themes.
    - Write in a professional, engaging literary tone suitable for a book jacket or query letter.
    - Use British English (UK English) spelling and grammar (e.g. 'colour', 'realise', 'characterisation').
    - Do NOT mention 'the author', 'the writer', or use any meta-commentary about the writing process. Focus entirely on the story world and characters.
    - Return the result in a JSON object with a 'summary' field containing the text.
    """
    
    model = "deepseek-reasoner" if use_reasoner else "deepseek-chat"
    res = _call_ai_json(
        prompt, 
        deepseek_model=model, 
        system_message="You are a professional literary agent and senior editor at a major publishing house. You focus strictly on the narrative and never mention the author.",
        user=book.user
    )
    
    if res and res.get('summary'):
        summary_text = res['summary'].strip()
        book.description = summary_text
        book.save(update_fields=['description'])
        
        # Log the activity
        ActivityLog.objects.create(
            user=book.user,
            action='update',
            model_name='Book',
            object_name=f"Summary for {book.title}"
        )
        
        return summary_text, None
    
    return None, "AI failed to synthesize the summary."
