"""
chatbot_app/api_urls.py — REST API URL patterns for /api/v1/

M3: ARCH-5a

/api/v1/auth/token/          POST  Obtain JWT access + refresh token pair
/api/v1/auth/token/refresh/  POST  Rotate: exchange refresh → new access token
/api/v1/chat/                POST  Bangla NLP chat (JWT required)
/api/v1/weather/             POST  Open-Meteo weather (JWT required)
/api/v1/disease/             POST  YOLOv8-nano disease detection (JWT required)
/api/v1/history/             GET   Paginated chat history (JWT required)
/api/v1/history/             DELETE Clear chat history (JWT required)
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .api_views import (
    ChatAPIView,
    ChatHistoryAPIView,
    DiseaseAPIView,
    WeatherAPIView,
)

app_name = 'api'

urlpatterns = [
    # -- Authentication (simplejwt) -----------------------------------------
    path('auth/token/',         TokenObtainPairView.as_view(), name='token_obtain'),
    path('auth/token/refresh/', TokenRefreshView.as_view(),   name='token_refresh'),

    # -- Core API endpoints -------------------------------------------------
    path('chat/',    ChatAPIView.as_view(),    name='chat'),
    path('weather/', WeatherAPIView.as_view(), name='weather'),
    path('disease/', DiseaseAPIView.as_view(), name='disease'),
    path('history/', ChatHistoryAPIView.as_view(), name='history'),
]
