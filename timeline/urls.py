"""
URL patterns for the timeline app.
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='timeline/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    
    # Home/Dashboard
    path('', views.home, name='timeline_home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('home-preview/', views.home_preview, name='home_preview'),
    
    # Books
    path('books/', views.book_list, name='book_list'),
    path('books/create/', views.book_create, name='book_create'),
    path('books/import/', views.book_import, name='book_import'),
    path('book/new/', views.book_create, name='book_create'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('book/<int:pk>/edit/', views.book_edit, name='book_edit'),
    path('book/<int:pk>/delete/', views.book_delete, name='book_delete'),
    path('book/<int:pk>/export/', views.export_story_bible, name='book_export'),
    path('api/books/<int:pk>/progress/', views.api_book_progress, name='api_book_progress'),
    
    # Chapters
    path('chapters/', views.chapter_list, name='chapter_list'),
    path('books/<int:book_pk>/chapters/create/', views.chapter_create, name='chapter_create'),
    path('books/<int:book_pk>/chapters/upload/', views.chapter_bulk_upload, name='chapter_bulk_upload'),
    path('chapters/<int:pk>/', views.chapter_detail, name='chapter_detail'),
    path('chapters/<int:pk>/edit/', views.chapter_edit, name='chapter_edit'),
    path('chapters/<int:pk>/delete/', views.chapter_delete, name='chapter_delete'),
    path('api/chapters/<int:pk>/scene-outline/', views.api_scene_outline, name='api_scene_outline'),
    path('api/chapters/<int:pk>/summary/', views.api_chapter_summary, name='api_chapter_summary'),
    
    # Characters
    path('characters/', views.character_list, name='character_list'),
    path('characters/create/', views.character_create, name='character_create'),
    path('characters/<int:pk>/', views.character_detail, name='character_detail'),
    path('characters/<int:pk>/edit/', views.character_edit, name='character_edit'),
    path('characters/<int:pk>/delete/', views.character_delete, name='character_delete'),
    
    # Events (Timeline)
    path('timeline/', views.timeline_view, name='timeline_view'),
    path('timeline/horizontal/', views.horizontal_timeline, name='horizontal_timeline'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/edit/', views.event_edit, name='event_edit'),
    path('events/<int:pk>/delete/', views.event_delete, name='event_delete'),
    path('events/<int:pk>/reorder/', views.event_reorder, name='event_reorder'),
    
    # Relationship Views
    path('relationships/', views.relationship_list, name='relationship_list'),
    path('relationships/map/', views.relationship_map, name='relationship_map'),
    path('relationships/new/', views.relationship_create, name='relationship_create'),
    path('relationships/<int:pk>/edit/', views.relationship_edit, name='relationship_edit'),
    path('relationships/<int:pk>/delete/', views.relationship_delete, name='relationship_delete'),
    path('api/relationships/data/', views.api_relationship_data, name='api_relationship_data'),
    path('api/relationships/manage/', views.api_manage_relationship, name='api_manage_relationship'),
    path('api/relationships/suggest/', views.api_suggest_relationship, name='api_suggest_relationship'),
    
    # Tags
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/<int:pk>/edit/', views.tag_edit, name='tag_edit'),
    path('tags/<int:pk>/delete/', views.tag_delete, name='tag_delete'),
    
    # World Wiki
    path('world/', views.world_list, name='world_list'),
    path('world/create/', views.world_create, name='world_create'),
    path('world/<int:pk>/', views.world_detail, name='world_detail'),
    path('world/<int:pk>/edit/', views.world_edit, name='world_edit'),
    path('world/<int:pk>/delete/', views.world_delete, name='world_delete'),
    
    # API endpoints for AJAX (we'll use these later for drag-and-drop)
    path('api/events/reorder/', views.api_event_reorder, name='api_event_reorder'),
    path('api/ai/consultant/', views.api_ai_consultant, name='api_ai_consultant'),
    path('api/ai/focus-tasks/<int:pk>/toggle/', views.api_toggle_focus_task, name='api_toggle_focus_task'),
    path('api/ai/character-deep-dive/', views.api_character_deep_dive, name='api_character_deep_dive'),
    path('api/ai/character-sync/', views.api_sync_character_data, name='api_character_sync'),
    path('api/books/<int:book_id>/deep-scan/trigger/', views.api_trigger_deep_scan, name='api_trigger_deep_scan'),
    path('api/books/<int:book_id>/deep-scan/status/', views.api_deep_scan_status, name='api_deep_scan_status'),
    path('account/', views.account, name='account'),
]
