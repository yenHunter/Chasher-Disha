# চাষের দিশা — Chasher-Disha

> **বাংলা কৃষি সহায়তা অ্যাপ্লিকেশন** · Bangla Agricultural Assistant

An offline-capable, mobile-first agricultural assistant for Bangladeshi farmers — Bangla NLP chatbot, AI-powered rice disease detection, hyperlocal weather, and fertilizer recommendations.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                │
│  ┌──────────────────────┐       ┌──────────────────────────────┐   │
│  │  React 18 + Vite SPA │       │  Capacitor 8 Android App     │   │
│  │  (web/src/)           │       │  (offline-first WebView)     │   │
│  │  Tailwind · Zustand   │       │  ONNX disease on-device      │   │
│  └──────────┬───────────┘       └──────────────┬───────────────┘   │
└─────────────┼─────────────────────────────────┼───────────────────┘
              │  JWT Bearer  /api/v1/             │
┌─────────────┼─────────────────────────────────┼───────────────────┐
│             │         Django 5.2 + DRF          │                   │
│  ┌──────────▼──────────────────────────────────▼──────────────┐   │
│  │           REST API  (/api/v1/)                              │   │
│  │  POST /auth/token/    POST /chat/                           │   │
│  │  POST /weather/       POST /disease/                        │   │
│  │  GET  /history/       POST /auth/token/refresh/             │   │
│  └──────┬──────────────┬──────────────┬──────────────┬────────┘   │
│         │              │              │              │              │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌────▼────┐ ┌──────▼──────┐      │
│  │ BanglaBERT  │ │ Open-Meteo │ │  YOLO   │ │  Fertilizer │      │
│  │ Small (NLP) │ │ + Nominatim│ │ nano v8 │ │  API (stub) │      │
│  │  M1         │ │    M2      │ │   M4    │ │     M5      │      │
│  └─────────────┘ └────────────┘ └─────────┘ └─────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start (< 15 minutes)

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.12+ |
| Node.js | 22+ |
| Git | any |
| Android Studio | Ladybug+ (for mobile only) |

### 1 — Clone and create virtual environment

```bash
git clone https://github.com/yenHunter/Chasher-Disha.git
cd Chasher-Disha
python -m venv env
# Windows
.\env\Scripts\activate
# macOS/Linux
source env/bin/activate
```

### 2 — Install Python dependencies

```bash
pip install -r requirements/dev.txt
```

> **Note:** `torch` is large (~2 GB). For CI / lightweight installs use the CPU wheel:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> pip install -r requirements/dev.txt
> ```

### 3 — Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set DJANGO_SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4 — Run migrations and start Django

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for admin panel
python manage.py runserver
# → http://127.0.0.1:8000
```

### 5 — Install and run the React frontend

```bash
npm --prefix web install
npm --prefix web run dev
# → http://localhost:5173  (proxies /api → Django:8000)
```

---

## API Reference

All endpoints require a JWT Bearer token except the auth endpoints.

### Obtain token

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_pass"}'
# → {"access": "eyJ...", "refresh": "eyJ..."}
```

### POST `/api/v1/chat/`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "ধানে পোকা লেগেছে"}'
# → {"response": "ধানের প্রধান ক্ষতিকর পোকা...", "intent": "pest_query", "confidence": 0.82}
```

### POST `/api/v1/weather/`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/weather/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"lat": 23.8103, "lon": 90.4125}'
# → {"place": "ঢাকা", "condition": "맑은 하늘", "temp_c": 32.1, "rain_prob_pct": 5, ...}
```

### POST `/api/v1/disease/`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/disease/ \
  -H "Authorization: Bearer <access_token>" \
  -F "image=@/path/to/rice_leaf.jpg"
# → {"success": true, "disease": "Blast", "disease_bn": "ব্লাস্ট রোগ",
#    "confidence": "87.3%", "advice": "ট্রাইসাইক্লাজল..."}
# If weights not trained yet → HTTP 503
```

### GET `/api/v1/history/`

```bash
curl http://127.0.0.1:8000/api/v1/history/ \
  -H "Authorization: Bearer <access_token>"
# → {"count": 12, "next": null, "results": [...]}
```

---

## Model Training (Rice Disease Detection)

The disease detection endpoint requires `chatbot_app/ml/models/rice_disease.pt`.

**Quickest path — Google Colab (free T4 GPU):**

1. Download **RiceLeafDiseaseBD v3** from [Mendeley](https://data.mendeley.com/datasets/86s4jzj2m4/3)
2. Open `train/colab_train.ipynb` in Colab and run all cells
3. Download `rice_disease.pt` + `rice_disease.onnx` from Colab output
4. Place both files in `chatbot_app/ml/models/`
5. Place `rice_disease.onnx` also in `web/src/assets/` for on-device inference

See [`train/README.md`](train/README.md) for local GPU training instructions.

**Dataset attribution:**

- Primary: RiceLeafDiseaseBD v3 — Md. Shoaib Ahmed Shibli, Mendeley Data, doi:[10.17632/86s4jzj2m4.3](https://data.mendeley.com/datasets/86s4jzj2m4/3)
- Supplementary: Harvard Dataverse XAOBYW — doi:[10.7910/DVN/XAOBYW](https://doi.org/10.7910/DVN/XAOBYW)

---

## Mobile (Android)

```bash
# Build web assets first
npm --prefix web run build

# Add Android platform (first time only — requires Android Studio)
cd web && npx cap add android

# Sync web assets + Capacitor plugins into Android project
npx cap sync android

# Open in Android Studio → Build → Generate Signed APK
npx cap open android
```

See [`web/android-res/README.md`](web/android-res/README.md) for icons, splash screen, and live-reload setup.

---

## Running Tests

```bash
# Django API tests (14 test cases)
pytest chatbot_app/tests.py -v

# With coverage
pytest chatbot_app/tests.py --cov=chatbot_app --cov-report=term-missing

# React component tests (20 test cases across 4 files)
npm --prefix web run test

# All tests
make test
```

---

## Project Structure

```
Chasher-Disha/
├── chatbot_app/          # Django app
│   ├── api_views.py      # DRF REST views (M3)
│   ├── api_urls.py       # /api/v1/ URL patterns
│   ├── ml/
│   │   ├── rice_disease.py  # YOLOv8 inference wrapper (M4)
│   │   └── models/          # *.pt / *.onnx weights (git-ignored)
│   ├── nlp_model.py      # BanglaBERT Small NLP (M1)
│   ├── weather.py        # Open-Meteo + Nominatim (M2)
│   ├── views.py          # Legacy Django-template views
│   └── tests.py          # pytest test suite (M8)
├── chatbot_project/      # Django project settings + URLs
├── web/                  # Vite + React SPA (M6) + Capacitor (M7)
│   ├── src/
│   │   ├── api/          # Axios client + typed endpoints
│   │   ├── components/   # ChatBubble, WeatherCard, DiseaseResult, …
│   │   ├── hooks/        # useChat, useWeather, useNetworkWatcher
│   │   ├── lib/          # capacitorBridge, offlineNlp, onnxDisease, weatherCache
│   │   ├── pages/        # Login, Chat, Weather, Disease, Fertilizer
│   │   └── store/        # Zustand: auth, chat, network
│   ├── capacitor.config.ts
│   └── android-res/      # Icon / splash source + setup guide
├── train/                # YOLOv8 training pipeline (M4)
│   ├── train.py
│   ├── colab_train.ipynb
│   └── README.md
├── scripts/              # download_model.py, smoke_test_api.py
├── requirements/
│   ├── base.txt          # production
│   ├── dev.txt           # + pytest, ruff, black
│   └── prod.txt          # + gunicorn, whitenoise
├── .github/
│   ├── workflows/ci.yml  # GitHub Actions CI (M8)
│   └── TODO.md           # Master roadmap
├── intents.csv           # 32 Bangla farming intents
├── Makefile              # Developer shortcuts
├── pyproject.toml        # ruff + black + pytest config
└── .pre-commit-config.yaml
```

---

## Milestone Status

| Milestone | Status |
|---|---|
| M0 Foundation & Security | ✅ Complete |
| M1 BanglaBERT Small NLP | ✅ Complete |
| M2 Open-Meteo Weather | ✅ Complete |
| M3 REST API (DRF + JWT) | ✅ Complete |
| M4 YOLO Rice Disease | ✅ Complete (weights pending training) |
| M6 Vite + React SPA | ✅ Complete |
| M7 Capacitor Android + Offline | ✅ Complete (Android Studio sync pending) |
| M8 Quality Gate | ✅ Complete |
| M5 Fertilizer API | 🔲 Pending (API choice required) |

---

## Contributing

1. Fork → feature branch → PR against `main`
2. `pre-commit install` before first commit
3. `make test` must pass locally
4. Follow the branch naming: `feat/m*-description`, `fix/description`
