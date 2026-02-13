import re
import json
import itertools
from django.db.models import Q
from timeline.models import Character, WorldEntry, Event, CharacterRelationship, RelationshipAnalysisCache

class ContextResolver:
    """
    Scans text for keywords (Character names, World locations) AND 
    retrieves their profiles to inject into AI prompts.
    """

    def __init__(self, user):
        self.user = user
        self.char_map = self._build_character_map()
        self.world_map = self._build_world_map()
        self.global_overview = self._build_global_overview()

    def _build_global_overview(self):
        """Builds a very compact list of all known characters and locations."""
        chars = Character.objects.filter(user=self.user).only('name', 'role')
        world = WorldEntry.objects.filter(user=self.user).only('title', 'category')
        
        overview = "[GLOBAL STORY BIBLE LIST]:\n"
        if chars:
            overview += "- Characters: " + ", ".join([f"{c.name} ({c.get_role_display()})" for c in chars]) + "\n"
        if world:
            overview += "- World/Locations: " + ", ".join([f"{w.title} ({w.get_category_display()})" for w in world]) + "\n"
        return overview

    def _build_character_map(self):
        """Map names & aliases to Character objects."""
        mapping = {}
        chars = Character.objects.filter(user=self.user)
        for char in chars:
            # Primary name
            mapping[char.name.lower()] = char
            
            # Auto-index First Name if it's a multi-word name
            name_parts = char.name.split()
            if len(name_parts) > 1:
                first_name = name_parts[0].lower()
                # Don't overwrite if another character already has this as a primary name
                if first_name not in mapping:
                    mapping[first_name] = char

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

    def _get_deep_insights(self, characters):
        """Finds R1 analysis and shared scene summaries for character pairs."""
        if len(characters) < 2:
            return ""
        
        insights = ["\n[DEEP STORY BIBLE INSIGHTS]:"]
        for char_a, char_b in itertools.combinations(characters, 2):
            # 1. Fetch R1 Relationship Analysis
            analysis = RelationshipAnalysisCache.objects.filter(
                Q(character_a=char_a, character_b=char_b) | 
                Q(character_a=char_b, character_b=char_a)
            ).first()
            
            if analysis:
                data = analysis.full_json
                insights.append(f"- Relationship Analysis ({char_a.name} & {char_b.name}):")
                insights.append(f"  * Dynamic: {data.get('dynamic_summary', 'Unknown')}")
                insights.append(f"  * Secrets: {data.get('shared_secrets', 'None')}")
                insights.append(f"  * Core Conflict: {data.get('core_conflict', 'None')}")

            # 2. Fetch Shared Events/Scenes
            shared_events = Event.objects.filter(
                characters=char_a
            ).filter(
                characters=char_b
            ).distinct().order_by('chronological_order')[:3]

            if shared_events.exists():
                insights.append(f"- Key Shared Scenes ({char_a.name} & {char_b.name}):")
                for ev in shared_events:
                    status = "Written" if ev.is_written else "Outline"
                    insights.append(f"  * [{status}] {ev.title}: {ev.description[:150]}...")

        return "\n".join(insights) if len(insights) > 1 else ""

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
                if obj.traits:
                     info += f". Traits: {obj.traits[:100]}"
                
                # Add Relationships
                rels = CharacterRelationship.objects.filter(
                    Q(character_a=obj) | Q(character_b=obj)
                ).select_related('character_a', 'character_b')
                
                if rels.exists():
                    rel_summaries = []
                    for r in rels:
                        other = r.character_b if r.character_a == obj else r.character_a
                        summary = f"{r.get_relationship_type_display()} with {other.name}"
                        if r.description:
                             summary += f" ({r.description[:50]}..)"
                        
                        # New Deep Insights
                        if r.shared_secret:
                            summary += f" [Secret: {r.shared_secret[:50]}]"
                        if r.vulnerability:
                            summary += f" [Vulnerability: {r.vulnerability[:50]}]"
                        if r.first_impression:
                            summary += f" [First Impression: {r.first_impression[:50]}]"
                        if r.conflict_source:
                            summary += f" [Conflict: {r.conflict_source[:50]}]"
                            
                        rel_summaries.append(summary)
                    info += ". RELATIONS: " + ", ".join(rel_summaries)
                
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
        
        # Pull specific profiles
        specific_context = self.format_context(objects)
        
        # Pull deep insights for character pairs
        chars = [obj for obj in objects if isinstance(obj, Character)]
        deep_insights = self._get_deep_insights(chars)
        
        return self.global_overview + "\n" + specific_context + "\n" + deep_insights
