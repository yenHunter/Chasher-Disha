"""
scripts/smoke_test_api.py — M3 API smoke test using Django test client.
Run: python scripts/smoke_test_api.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatbot_project.settings")
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()
user, _ = User.objects.get_or_create(username="smoketest", defaults={"email": "s@test.com"})
user.set_password("pass")
user.save()

# Use SERVER_NAME that matches ALLOWED_HOSTS
client = APIClient(SERVER_NAME="127.0.0.1")

# 1. Unauthenticated -> 401
r = client.post("/api/v1/chat/", {"message": "test"}, format="json")
print(f"[1] UNAUTH chat        → {r.status_code}  (expected 401)  {'OK' if r.status_code == 401 else 'FAIL'}")

# 2. Obtain JWT
r = client.post("/api/v1/auth/token/", {"username": "smoketest", "password": "pass"}, format="json")
print(f"[2] Token obtain       → {r.status_code}  (expected 200)  {'OK' if r.status_code == 200 else 'FAIL'}")
data = r.json()
access  = data.get("access",  "")
refresh = data.get("refresh", "")
print(f"    access token  present: {bool(access)}")
print(f"    refresh token present: {bool(refresh)}")

client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

# 3. Weather
r = client.post("/api/v1/weather/", {"latitude": 23.8103, "longitude": 90.4125}, format="json")
print(f"[3] Weather            → {r.status_code}  (200 ok / 503 offline)  {'OK' if r.status_code in (200, 503) else 'FAIL'}")
if r.status_code == 200:
    d = r.json()
    print(f"    place={d.get('place')}  temp={d.get('temperature')}")

# 4. Token refresh
r = client.post("/api/v1/auth/token/refresh/", {"refresh": refresh}, format="json")
print(f"[4] Token refresh      → {r.status_code}  (expected 200)  {'OK' if r.status_code == 200 else 'FAIL'}")
print(f"    new access present: {bool(r.json().get('access'))}")

# 5. History GET
r = client.get("/api/v1/history/")
print(f"[5] History GET        → {r.status_code}  (expected 200)  {'OK' if r.status_code == 200 else 'FAIL'}")
print(f"    count={r.json().get('count')}")

# 6. Disease — no file -> 400
r = client.post("/api/v1/disease/")
print(f"[6] Disease no-image   → {r.status_code}  (expected 400)  {'OK' if r.status_code == 400 else 'FAIL'}")

# 7. Weather bad coords -> 400
r = client.post("/api/v1/weather/", {"latitude": 999, "longitude": 0}, format="json")
print(f"[7] Weather bad coords → {r.status_code}  (expected 400)  {'OK' if r.status_code == 400 else 'FAIL'}")

# 8. Weather missing body -> 400
r = client.post("/api/v1/weather/", {}, format="json")
print(f"[8] Weather no body    → {r.status_code}  (expected 400)  {'OK' if r.status_code == 400 else 'FAIL'}")

print("\nDone.")
