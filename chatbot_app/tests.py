"""
chatbot_app/tests.py — Django API test suite  (M8: TEST-1)

Run:
    pytest chatbot_app/tests.py -v
    pytest chatbot_app/tests.py --cov=chatbot_app --cov-report=term-missing

Test plan (10 mandatory + 5 extras = 15 total):
    1.  test_chat_empty_input            → HTTP 400
    2.  test_chat_no_body                → HTTP 400
    3.  test_chat_known_farming_intent   → "ধানে পোকা" → 200 + response
    4.  test_chat_unknown_input          → low-confidence → 200 + fallback
    5.  test_weather_valid_coords        → Dhaka → 200 + Bangla keys  (mocked)
    6.  test_weather_invalid_coords      → lat=999 → 400
    7.  test_weather_missing_params      → no body → 400
    8.  test_disease_no_image            → no file field → 400
    9.  test_disease_wrong_type          → text file → 400
    10. test_disease_valid_jpeg          → 200 or 503 (weights optional)
    11. test_jwt_auth_required           → unauthenticated → 401
    12. test_jwt_obtain_token            → valid creds → 200 + access/refresh
    13. test_jwt_invalid_creds           → bad creds → 401
    14. test_chat_history_empty          → GET /history/ → 200 + count=0
    15. test_throttle_classes_registered → throttle classes on all views
"""

import io
import json
from unittest.mock import patch, MagicMock

import pytest
from django.contrib.auth import get_user_model
from PIL import Image as PILImage
from rest_framework.test import APIClient

User = get_user_model()

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    return APIClient(SERVER_NAME="127.0.0.1")


@pytest.fixture
def auth_client(db, api_client):
    """APIClient pre-authenticated with a JWT access token."""
    user, _ = User.objects.get_or_create(
        username="testuser_m8",
        defaults={"email": "m8@test.bd"},
    )
    user.set_password("testpass_m8")
    user.save()

    resp = api_client.post(
        "/api/v1/auth/token/",
        {"username": "testuser_m8", "password": "testpass_m8"},
        format="json",
    )
    assert resp.status_code == 200, f"Token obtain failed: {resp.data}"
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return api_client


def _make_jpeg_bytes(color: tuple = (34, 139, 34)) -> bytes:
    """Create a minimal valid 64×64 JPEG in memory."""
    img = PILImage.new("RGB", (64, 64), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# Mock payload — keys must exactly match what WeatherAPIView reads from fetch_weather()
_MOCK_WEATHER = {
    "message":          "আজ আবহাওয়া পরিষ্কার।",
    "agri_advice":      "সেচ দেওয়া যাবে।",
    "place":            "ঢাকা",
    "condition":        "맑은 하늘",
    "temperature":      32.1,
    "humidity":         70,
    "rain_probability": 5,
    "wind_speed":       12.0,
    "uv_index":         7,
    "rain_3day":        2.5,
    "et0_3day":         14.5,
}


# ── TEST-11/12/13: JWT auth gate ──────────────────────────────────────────────

@pytest.mark.django_db
class TestJwtAuth:
    """M8 TEST-11, TEST-12, TEST-13 — JWT obtain and auth gate."""

    def test_jwt_auth_required(self, api_client):
        """Unauthenticated request → 401."""
        resp = api_client.post(
            "/api/v1/chat/", {"message": "হ্যালো"}, format="json"
        )
        assert resp.status_code == 401

    def test_jwt_obtain_token(self, db, api_client):
        """Valid credentials → 200 with access and refresh tokens."""
        user, _ = User.objects.get_or_create(
            username="jwt_test_user", defaults={"email": "j@t.bd"}
        )
        user.set_password("securepass123")
        user.save()

        resp = api_client.post(
            "/api/v1/auth/token/",
            {"username": "jwt_test_user", "password": "securepass123"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_jwt_invalid_creds(self, db, api_client):
        """Wrong password → 401."""
        resp = api_client.post(
            "/api/v1/auth/token/",
            {"username": "nobody", "password": "wrong"},
            format="json",
        )
        assert resp.status_code == 401


# ── TEST-1/2: Chat input validation ──────────────────────────────────────────

@pytest.mark.django_db
class TestChatValidation:
    """M8 TEST-1, TEST-2 — Chat endpoint input validation."""

    def test_chat_empty_input(self, auth_client):
        """Empty message string → 400."""
        resp = auth_client.post(
            "/api/v1/chat/", {"message": ""}, format="json"
        )
        assert resp.status_code == 400

    def test_chat_no_body(self, auth_client):
        """Missing message key → 400."""
        resp = auth_client.post("/api/v1/chat/", {}, format="json")
        assert resp.status_code == 400


# ── TEST-3/4: Chat NLP responses ─────────────────────────────────────────────

@pytest.mark.django_db
class TestChatNlp:
    """M8 TEST-3, TEST-4 — BanglaBERT intent matching."""

    def test_chat_known_farming_intent(self, auth_client):
        """'ধানে পোকা লেগেছে' matches pest_query → 200 + response."""
        resp = auth_client.post(
            "/api/v1/chat/", {"message": "ধানে পোকা লেগেছে"}, format="json"
        )
        assert resp.status_code == 200
        assert "response" in resp.data
        assert len(resp.data["response"]) > 5

    def test_chat_unknown_input(self, auth_client):
        """Unrelated gibberish → cosine < 0.60 → fallback, still 200."""
        resp = auth_client.post(
            "/api/v1/chat/",
            {"message": "xyzzy foo bar baz 12345"},
            format="json",
        )
        assert resp.status_code == 200
        assert "response" in resp.data
        assert len(resp.data["response"]) > 0


# ── TEST-5/6/7: Weather endpoint ─────────────────────────────────────────────

@pytest.mark.django_db
class TestWeather:
    """M8 TEST-5, TEST-6, TEST-7 — Weather endpoint."""

    def test_weather_valid_coords(self, auth_client):
        """Dhaka coords → 200 with expected keys (Open-Meteo mocked)."""
        import chatbot_app.weather  # ensure module is loaded before patch targets it
        with patch.object(
            __import__("chatbot_app.weather", fromlist=["fetch_weather"]),
            "fetch_weather",
            return_value=_MOCK_WEATHER,
        ):
            resp = auth_client.post(
                "/api/v1/weather/",
                {"latitude": 23.8103, "longitude": 90.4125},
                format="json",
            )
        assert resp.status_code == 200
        for key in ("place", "condition", "weather", "rain_probability"):
            assert key in resp.data, f"Missing key: {key}"

    def test_weather_invalid_coords(self, auth_client):
        """Out-of-range latitude → 400 (no network call made)."""
        resp = auth_client.post(
            "/api/v1/weather/", {"latitude": 999, "longitude": 0}, format="json"
        )
        assert resp.status_code == 400

    def test_weather_missing_params(self, auth_client):
        """Empty body → 400."""
        resp = auth_client.post("/api/v1/weather/", {}, format="json")
        assert resp.status_code == 400


# ── TEST-8/9/10: Disease endpoint ────────────────────────────────────────────

@pytest.mark.django_db
class TestDisease:
    """M8 TEST-8, TEST-9, TEST-10 — Disease detection endpoint."""

    def test_disease_no_image(self, auth_client):
        """POST with no file → 400."""
        resp = auth_client.post("/api/v1/disease/", {}, format="multipart")
        assert resp.status_code == 400

    def test_disease_wrong_file_type(self, auth_client):
        """Plain-text file → 400 (type guard)."""
        txt = io.BytesIO(b"this is not an image")
        txt.name = "test.txt"
        resp = auth_client.post(
            "/api/v1/disease/", {"image": txt}, format="multipart"
        )
        assert resp.status_code == 400

    def test_disease_valid_jpeg_returns_503_or_200(self, auth_client):
        """
        Valid JPEG → 200 with schema (weights present) OR 503 (weights missing).
        Both outcomes are valid in CI.
        """
        jpeg_bytes = _make_jpeg_bytes()
        img_file = io.BytesIO(jpeg_bytes)
        img_file.name = "leaf.jpg"
        resp = auth_client.post(
            "/api/v1/disease/", {"image": img_file}, format="multipart"
        )
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            for key in ("disease", "confidence", "advice"):
                assert key in resp.data


# ── TEST-14: Chat history ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestChatHistory:
    """M8 TEST-14 — GET /history/ returns paginated results."""

    def test_chat_history_empty(self, auth_client):
        """Fresh user → history count is 0."""
        resp = auth_client.get("/api/v1/history/")
        assert resp.status_code == 200
        assert "count" in resp.data
        assert resp.data["count"] == 0


# ── TEST-15: Rate-limit structure ─────────────────────────────────────────────

class TestRateLimitConfig:
    """M8 TEST-15 — Verify throttle classes are registered (no DB needed)."""

    def test_throttle_classes_registered(self):
        from chatbot_app.api_views import ChatAPIView, WeatherAPIView, DiseaseAPIView

        for view_cls in (ChatAPIView, WeatherAPIView, DiseaseAPIView):
            assert hasattr(view_cls, "throttle_classes"), (
                f"{view_cls.__name__} is missing throttle_classes"
            )
            assert len(view_cls.throttle_classes) > 0, (
                f"{view_cls.__name__}.throttle_classes is empty"
            )



import io
import json

import pytest
from django.contrib.auth import get_user_model
from PIL import Image as PILImage
from rest_framework.test import APIClient

User = get_user_model()

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def django_db_setup():
    """Session-scoped DB — avoids re-creating tables per test."""
    pass


@pytest.fixture
def api_client():
    return APIClient(SERVER_NAME="127.0.0.1")


@pytest.fixture
def auth_client(db, api_client):
    """APIClient pre-authenticated with a JWT access token."""
    user, _ = User.objects.get_or_create(
        username="testuser_m8",
        defaults={"email": "m8@test.bd"},
    )
    user.set_password("testpass_m8")
    user.save()

    resp = api_client.post(
        "/api/v1/auth/token/",
        {"username": "testuser_m8", "password": "testpass_m8"},
        format="json",
    )
    assert resp.status_code == 200, f"Token obtain failed: {resp.data}"
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
    return api_client


def _make_jpeg_bytes(color: tuple = (34, 139, 34)) -> bytes:
    """Create a minimal valid 64×64 JPEG in memory."""
    img = PILImage.new("RGB", (64, 64), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ── TEST-9: JWT auth gate (runs without DB to keep it fast) ──────────────────

@pytest.mark.django_db
class TestJwtAuth:
    """M8 TEST-9, TEST-11, TEST-12 — JWT obtain and auth gate."""

    def test_jwt_auth_required(self, api_client):
        """Unauthenticated request → 401."""
        resp = api_client.post(
            "/api/v1/chat/", {"message": "হ্যালো"}, format="json"
        )
        assert resp.status_code == 401

    def test_jwt_obtain_token(self, db, api_client):
        """Valid credentials → 200 with access and refresh tokens."""
        user, _ = User.objects.get_or_create(
            username="jwt_test_user", defaults={"email": "j@t.bd"}
        )
        user.set_password("securepass123")
        user.save()

        resp = api_client.post(
            "/api/v1/auth/token/",
            {"username": "jwt_test_user", "password": "securepass123"},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_jwt_invalid_creds(self, db, api_client):
        """Wrong password → 401."""
        resp = api_client.post(
            "/api/v1/auth/token/",
            {"username": "nobody", "password": "wrong"},
            format="json",
        )
        assert resp.status_code == 401


# ── TEST-1/2: Chat input validation ──────────────────────────────────────────

@pytest.mark.django_db
class TestChatValidation:
    """M8 TEST-1, TEST-2 — Chat endpoint input validation."""

    def test_chat_empty_input(self, auth_client):
        """Empty message string → 400."""
        resp = auth_client.post(
            "/api/v1/chat/", {"message": ""}, format="json"
        )
        assert resp.status_code == 400

    def test_chat_no_body(self, auth_client):
        """Missing message key → 400."""
        resp = auth_client.post("/api/v1/chat/", {}, format="json")
        assert resp.status_code == 400


# ── TEST-3/4: Chat NLP responses ─────────────────────────────────────────────

@pytest.mark.django_db
class TestChatNlp:
    """M8 TEST-3, TEST-4 — BanglaBERT intent matching."""

    def test_chat_known_farming_intent(self, auth_client):
        """
        'ধানে পোকা লেগেছে' matches pest_query intent.
        Expects 200 and a non-empty Bangla response.
        """
        resp = auth_client.post(
            "/api/v1/chat/", {"message": "ধানে পোকা লেগেছে"}, format="json"
        )
        assert resp.status_code == 200
        data = resp.data
        assert "response" in data
        assert len(data["response"]) > 5  # non-trivial response

    def test_chat_unknown_input(self, auth_client):
        """
        Completely unrelated input → cosine score < 0.60 → fallback.
        The fallback response must be non-empty and not raise.
        """
        resp = auth_client.post(
            "/api/v1/chat/",
            {"message": "xyzzy foo bar baz 12345"},
            format="json",
        )
        assert resp.status_code == 200
        assert "response" in resp.data
        assert len(resp.data["response"]) > 0


# ── TEST-5/6/7: Weather endpoint (stale block removed — see class above) ─────



# ── TEST-8/9: Disease endpoint ───────────────────────────────────────────────

@pytest.mark.django_db
class TestDisease:
    """M8 TEST-8, TEST-9 — Disease detection endpoint."""

    def test_disease_no_image(self, auth_client):
        """POST with no file → 400."""
        resp = auth_client.post("/api/v1/disease/", {}, format="multipart")
        assert resp.status_code == 400

    def test_disease_wrong_file_type(self, auth_client):
        """Plain-text file → 400 (type guard)."""
        txt = io.BytesIO(b"this is not an image")
        txt.name = "test.txt"
        resp = auth_client.post(
            "/api/v1/disease/", {"image": txt}, format="multipart"
        )
        assert resp.status_code == 400

    def test_disease_valid_jpeg_returns_503_or_200(self, auth_client):
        """
        Valid JPEG → either:
          200 with {disease, confidence, advice}  (weights present), or
          503 ModelNotReady                        (weights not yet trained).
        Both are valid in CI — we only assert the shape on 200.
        """
        jpeg_bytes = _make_jpeg_bytes()
        img_file = io.BytesIO(jpeg_bytes)
        img_file.name = "leaf.jpg"
        resp = auth_client.post(
            "/api/v1/disease/", {"image": img_file}, format="multipart"
        )
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            for key in ("disease", "confidence", "advice"):
                assert key in resp.data


# ── TEST-13: Chat history ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestChatHistory:
    """M8 TEST-13 — GET /history/ returns paginated results."""

    def test_chat_history_empty(self, auth_client):
        """Fresh user → history count is 0."""
        resp = auth_client.get("/api/v1/history/")
        assert resp.status_code == 200
        assert "count" in resp.data
        assert resp.data["count"] == 0


# ── TEST-14: Rate-limit structure ─────────────────────────────────────────────

class TestRateLimitConfig:
    """M8 TEST-14 — Verify throttle classes are registered (no DB needed)."""

    def test_throttle_classes_registered(self):
        from chatbot_app.api_views import ChatAPIView, WeatherAPIView, DiseaseAPIView

        for view_cls in (ChatAPIView, WeatherAPIView, DiseaseAPIView):
            assert hasattr(view_cls, "throttle_classes"), (
                f"{view_cls.__name__} is missing throttle_classes"
            )
            assert len(view_cls.throttle_classes) > 0, (
                f"{view_cls.__name__}.throttle_classes is empty"
            )
