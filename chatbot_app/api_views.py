"""
api_views.py — DRF-based REST API views for Chasher-Disha.

M3: ARCH-5a — All endpoints under /api/v1/
M3: SEC-3   — JWT authentication replaces @csrf_exempt
M3: SEC-4   — Per-view rate limiting via custom DRF throttle classes

URL map:
    POST /api/v1/auth/token/           → JWT login  (simplejwt TokenObtainPairView)
    POST /api/v1/auth/token/refresh/   → JWT refresh (simplejwt TokenRefreshView)
    POST /api/v1/chat/                 → ChatAPIView
    POST /api/v1/weather/              → WeatherAPIView
    POST /api/v1/disease/              → DiseaseAPIView
    GET  /api/v1/history/              → ChatHistoryAPIView
    DELETE /api/v1/history/            → ChatHistoryAPIView (clear)
"""

from __future__ import annotations

import json
import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# M3: SEC-4 — Custom throttle classes (ARCH-5 throttle-rate keys)
# ---------------------------------------------------------------------------
class ChatRateThrottle(UserRateThrottle):
    scope = 'chat'     # 20/min — defined in REST_FRAMEWORK.DEFAULT_THROTTLE_RATES


class DiseaseRateThrottle(UserRateThrottle):
    scope = 'disease'  # 10/min


# ---------------------------------------------------------------------------
# Helper: get session key from JWT or fall back to Django session
# ---------------------------------------------------------------------------
def _session_key(request) -> str:
    """
    Return a stable per-user identifier for grouping chat history.
    With JWT: use the user's primary key as a string.
    """
    if request.user and request.user.is_authenticated:
        return f'user_{request.user.pk}'
    # Anonymous fallback (should not reach here with IsAuthenticated)
    return request.session.session_key or 'anon'


# ---------------------------------------------------------------------------
# POST /api/v1/chat/
# ---------------------------------------------------------------------------
class ChatAPIView(APIView):
    """
    Accepts a Bangla text message and returns the NLP-matched response.

    Request body (JSON):
        {"message": "ধানে কী রোগ হয়েছে?"}

    Response (200):
        {
          "response": "...",
          "intent":   "disease_query",      # omitted for sentinels
          "sentinel": "__ASK_DISEASE__"     # present only when NLP returns a sentinel
        }

    Errors:
        400 — missing / empty message
        429 — rate limit exceeded (20/min per user)
    """

    permission_classes = [IsAuthenticated]
    throttle_classes   = [ChatRateThrottle]

    def post(self, request):
        message = (request.data.get('message') or '').strip()
        if not message:
            return Response(
                {'error': 'message ক্ষেত্রটি প্রয়োজন।'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .nlp_model import get_response  # noqa: PLC0415
        bot_response = get_response(message)

        # -- Persist conversation (ARCH-1) -----------------------------------
        from .models import ChatMessage  # noqa: PLC0415
        session = _session_key(request)
        ChatMessage.objects.create(
            session_key=session,
            sender=ChatMessage.SENDER_USER,
            text=message,
        )

        # -- Detect sentinel -------------------------------------------------
        SENTINELS = {'__ASK_WEATHER__', '__ASK_DISEASE__', '__ASK_FERTILIZER__'}
        is_sentinel = bot_response in SENTINELS

        bot_msg = ChatMessage.objects.create(
            session_key=session,
            sender=ChatMessage.SENDER_BOT,
            text=bot_response,
        )

        payload: dict = {'response': bot_response}
        if is_sentinel:
            payload['sentinel'] = bot_response
        return Response(payload, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# POST /api/v1/weather/
# ---------------------------------------------------------------------------
class WeatherAPIView(APIView):
    """
    Returns Bangla weather summary + agricultural advice for supplied coordinates.

    Request body (JSON):
        {"latitude": 23.8103, "longitude": 90.4125}

    Response (200):
        {
          "weather":          "...",
          "agri_advice":      "...",
          "place":            "ঢাকা",
          "condition":        "맑은 আকাশ",
          "temperature":      34.4,
          "humidity":         62,
          "rain_probability": 0,
          "wind_speed":       12.5,
          "uv_index":         7,
          "rain_3day_mm":     0.0,
          "et0_3day_mm":      14.5
        }

    Errors:
        400 — missing / invalid coordinates
        503 — Open-Meteo / Nominatim unreachable
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            lat = float(request.data['latitude'])
            lon = float(request.data['longitude'])
        except (KeyError, TypeError, ValueError):
            return Response(
                {'error': 'latitude ও longitude প্রয়োজন (দশমিক সংখ্যা)।'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return Response(
                {'error': 'latitude বা longitude এর মান সঠিক নয়।'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .weather import fetch_weather, WeatherServiceError  # noqa: PLC0415
        try:
            data = fetch_weather(lat, lon)
        except WeatherServiceError as exc:
            return Response(
                {'error': f'আবহাওয়া তথ্য পাওয়া যায়নি: {exc}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            'weather':          data['message'],
            'agri_advice':      data['agri_advice'],
            'place':            data['place'],
            'condition':        data['condition'],
            'temperature':      data['temperature'],
            'humidity':         data['humidity'],
            'rain_probability': data['rain_probability'],
            'wind_speed':       data['wind_speed'],
            'uv_index':         data['uv_index'],
            'rain_3day_mm':     data['rain_3day'],
            'et0_3day_mm':      data['et0_3day'],
        })


# ---------------------------------------------------------------------------
# POST /api/v1/disease/
# ---------------------------------------------------------------------------
class DiseaseAPIView(APIView):
    """
    Accepts a rice leaf image and returns the YOLOv8-nano disease prediction.

    Request body: multipart/form-data — field name: "image" (JPEG / PNG / WebP)

    Response (200):
        {
          "success":        true,
          "disease":        "Blast",
          "disease_bn":     "ব্লাস্ট রোগ",
          "confidence":     "87.3%",
          "advice":         "ট্রাইসাইক্লাজল ছত্রাকনাশক ব্যবহার করুন।",
          "all_detections": [...]
        }

    Errors:
        400 — no image / invalid file type / too large / corrupt image
        503 — model weights not yet installed
        500 — inference failure
        429 — rate limit exceeded (10/min per user)
    """

    permission_classes = [IsAuthenticated]
    throttle_classes   = [DiseaseRateThrottle]

    def post(self, request):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response(
                {'success': False, 'error': 'ছবি আপলোড করুন।'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_types = {'image/jpeg', 'image/jpg', 'image/png', 'image/webp'}
        content_type  = getattr(image_file, 'content_type', '').lower()
        if content_type and content_type not in allowed_types:
            return Response(
                {'success': False, 'error': 'শুধু JPEG বা PNG ছবি গ্রহণযোগ্য।'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if image_file.size > 10 * 1024 * 1024:
            return Response(
                {'success': False, 'error': 'ছবির আকার ১০ MB-এর বেশি হওয়া উচিত নয়।'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_bytes = image_file.read()

        from .ml.rice_disease import (  # noqa: PLC0415
            ModelNotReadyError, InferenceError, predict,
        )
        try:
            result = predict(image_bytes)
        except ModelNotReadyError as exc:
            return Response(
                {
                    'success': False,
                    'error':   'রোগ শনাক্তকরণ মডেল এখনও প্রস্তুত নয়।',
                    'detail':  str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ValueError as exc:
            return Response(
                {'success': False, 'error': f'ছবি পড়া যায়নি: {exc}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InferenceError as exc:
            return Response(
                {'success': False, 'error': f'মডেল ত্রুটি: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            'success':        result['success'],
            'disease':        result['disease'],
            'disease_bn':     result['disease_bn'],
            'confidence':     f"{result['confidence'] * 100:.1f}%",
            'advice':         result['advice'],
            'all_detections': result['all_detections'],
        })


# ---------------------------------------------------------------------------
# GET /api/v1/history/   DELETE /api/v1/history/
# ---------------------------------------------------------------------------
class ChatHistoryAPIView(APIView):
    """
    GET  — Return paginated chat history for the authenticated user's session.
    DELETE — Clear the authenticated user's chat history.

    GET query params:
        ?limit=50    (default 50, max 200)
        ?offset=0    (default 0)

    GET Response (200):
        {
          "count":    12,
          "messages": [
            {"id": 1, "sender": "user",  "text": "...", "intent": "", "created_at": "..."},
            {"id": 2, "sender": "bot",   "text": "...", "intent": "crop_season", "created_at": "..."},
            ...
          ]
        }

    DELETE Response (204): no body.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = _session_key(request)
        try:
            limit  = min(int(request.query_params.get('limit',  50)), 200)
            offset = max(int(request.query_params.get('offset',  0)),   0)
        except (TypeError, ValueError):
            limit, offset = 50, 0

        from .models import ChatMessage  # noqa: PLC0415
        qs    = ChatMessage.objects.filter(session_key=session)
        total = qs.count()
        msgs  = qs[offset: offset + limit]

        return Response({
            'count': total,
            'messages': [
                {
                    'id':         m.pk,
                    'sender':     m.sender,
                    'text':       m.text,
                    'intent':     m.intent,
                    'confidence': m.confidence,
                    'created_at': m.created_at.isoformat(),
                }
                for m in msgs
            ],
        })

    def delete(self, request):
        session = _session_key(request)
        from .models import ChatMessage  # noqa: PLC0415
        deleted, _ = ChatMessage.objects.filter(session_key=session).delete()
        logger.info('[History] Cleared %d messages for session %s', deleted, session)
        return Response(status=status.HTTP_204_NO_CONTENT)
