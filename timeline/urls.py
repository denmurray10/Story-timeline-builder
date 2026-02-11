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
    
    # Books
    path('books/', views.book_list, name='book_list'),
    path('books/create/', views.book_create, name='book_create'),
    path('book/new/', views.book_create, name='book_create'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('book/<int:pk>/edit/', views.book_edit, name='book_edit'),
    path('book/<int:pk>/delete/', views.book_delete, name='book_delete'),
    path('book/<int:pk>/export/', views.export_story_bible, name='book_export'),
    
    # Chapters
    path('books/<int:book_pk>/chapters/create/', views.chapter_create, name='chapter_create'),
    path('chapters/<int:pk>/edit/', views.chapter_edit, name='chapter_edit'),
    path('chapters/<int:pk>/delete/', views.chapter_delete, name='chapter_delete'),
    
    # Characters
    path('characters/', views.character_list, name='character_list'),
    path('characters/create/', views.character_create, name='character_create'),
    path('characters/<int:pk>/', views.character_detail, name='character_detail'),
    path('characters/<int:pk>/edit/', views.character_edit, name='character_edit'),
    path('characters/<int:pk>/delete/', views.character_delete, name='character_delete'),
    
    # Events (Timeline)
    path('timeline/', views.timeline_view, name='timeline_view'),
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
    
    # Tags
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/<int:pk>/edit/', views.tag_edit, name='tag_edit'),
    path('tags/<int:pk>/delete/', views.tag_delete, name='tag_delete'),
    
    # API endpoints for AJAX (we'll use these later for drag-and-drop)
    path('api/events/reorder/', views.api_event_reorder, name='api_event_reorder'),
    path('api/ai/consultant/', views.api_ai_consultant, name='api_ai_consultant'),
    path('account/', views.account, name='account'),
]
