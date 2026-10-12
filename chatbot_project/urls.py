"""
URL configuration for chatbot_project project.

Route map:
    /api/v1/   →  chatbot_app.api_urls   (DRF REST API — M3)
    /admin/    →  Django admin
    /          →  chatbot_app.urls       (legacy Django-template UI — replaced in M6)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # M3: REST API  (versioned, JWT-authenticated)
    path('api/v1/', include('chatbot_app.api_urls', namespace='api')),

    # Django admin (unchanged)
    path('admin/', admin.site.urls),

    # Legacy template UI — still served until M6 React SPA replaces it
    path('', include('chatbot_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


