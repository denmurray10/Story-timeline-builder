"""
Main URL configuration for timeline_project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('blog/', include('blog.urls')),
    path('', include('timeline.urls')),
]

handler404 = 'timeline.views.handler404'
handler500 = 'timeline.views.handler500'

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
