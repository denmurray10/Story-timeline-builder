import re
from django.db.models import Q
from timeline.models import Character, WorldEntry, Event

class ContextResolver:
    """
    Scans text for keywords (Character names, World locations) AND 
    retrieves their profiles to inject into AI prompts.
    """

    def __init__(self, user):
        self.user = user
        self.char_map = self._build_character_map()
        self.world_map = self._build_world_map()

    def _build_character_map(self):
        """Map names & aliases to Character objects."""
        mapping = {}
        chars = Character.objects.filter(user=self.user)
        for char in chars:
            # Primary name
            mapping[char.name.lower()] = char
            # Aliases
            if char.aliases:
                for alias in char.aliases.split(','):
                    alias = alias.strip().lower()
                    if alias:
                        mapping[alias] = char
            # Nickname
            if char.nickname:
                mapping[char.nickname.lower()] = char
        return mapping

    def _build_world_map(self):
        """Map titles to WorldEntry objects."""
        mapping = {}
        entries = WorldEntry.objects.filter(user=self.user)
        for entry in entries:
            mapping[entry.title.lower()] = entry
        return mapping

    def scan_text(self, text):
        """
        Scans the provided text for known keywords.
        Returns a list of unique objects (Characters, WorldEntries).
        """
        if not text:
            return []

        found_objects = set()
        text_lower = text.lower()

        # Simple keyword matching (Scanning is fast, regex can be slower for massive lists)
        # For a story bible < 1000 items, direct iteration is fine.
        
        # 1. Characters
        for name, char_obj in self.char_map.items():
            # Use regex to match whole words only to avoid finding "Cat" in "Catch"
            # Escaping the name is important
            if re.search(r'\b' + re.escape(name) + r'\b', text_lower):
                found_objects.add(char_obj)

        # 2. World Entries
        for title, world_obj in self.world_map.items():
            if re.search(r'\b' + re.escape(title) + r'\b', text_lower):
                found_objects.add(world_obj)

        return list(found_objects)

    def format_context(self, objects):
        """
        Formats a list of objects into a compact string for the AI system prompt.
        """
        if not objects:
            return ""

        context_lines = ["\n[STORY CONTEXT - RELEVANT ENTITIES]:"]
        
        for obj in objects:
            if isinstance(obj, Character):
                info = f"- CHARACTER: {obj.name}"
                if obj.role:
                    info += f" ({obj.get_role_display()})"
                if obj.description:
                    # Truncate to save tokens
                    desc = (obj.description[:200] + '..') if len(obj.description) > 200 else obj.description
                    info += f". Desc: {desc}"
                if obj.motivation:
                     info += f". Motive: {obj.motivation[:100]}"
                context_lines.append(info)
            
            elif isinstance(obj, WorldEntry):
                info = f"- WORLD INFO ({obj.get_category_display()}): {obj.title}"
                if obj.content:
                    desc = (obj.content[:200] + '..') if len(obj.content) > 200 else obj.content
                    info += f". Details: {desc}"
                context_lines.append(info)

        return "\n".join(context_lines)

    def get_context_for_query(self, query, scene_content=None):
        """
        Main entry point. Scans both the user's query and the active scene (if any).
        Returns the formatted context string.
        """
        combined_text = query + "\n" + (scene_content or "")
        objects = self.scan_text(combined_text)
        return self.format_context(objects)
