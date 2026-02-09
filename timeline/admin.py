"""
Admin configuration for the Timeline app.
This allows you to manage all your models through Django's admin interface.
"""

from django.contrib import admin
from .models import Book, Chapter, Character, Event, Tag, CharacterRelationship


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['series_order', 'title', 'status', 'current_word_count', 'word_count_target', 'progress_percentage']
    list_filter = ['status', 'user']
    search_fields = ['title', 'description']
    ordering = ['series_order']


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ['book', 'chapter_number', 'title', 'word_count', 'is_complete']
    list_filter = ['book', 'is_complete']
    search_fields = ['title', 'description']
    ordering = ['book', 'chapter_number']


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'introduction_book', 'is_active', 'color_code']
    list_filter = ['role', 'is_active', 'introduction_book']
    search_fields = ['name', 'nickname', 'description']
    ordering = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'color']
    list_filter = ['category']
    search_fields = ['name', 'description']
    ordering = ['category', 'name']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'book', 'chapter', 'sequence_order', 'pov_character', 'emotional_tone', 'tension_level', 'is_written']
    list_filter = ['book', 'emotional_tone', 'story_beat', 'is_written', 'pov_character']
    search_fields = ['title', 'description', 'location']
    filter_horizontal = ['characters', 'tags']
    ordering = ['sequence_order']


@admin.register(CharacterRelationship)
class CharacterRelationshipAdmin(admin.ModelAdmin):
    list_display = ['character_a', 'character_b', 'relationship_type', 'strength']
    list_filter = ['relationship_type']
    search_fields = ['character_a__name', 'character_b__name', 'description']
