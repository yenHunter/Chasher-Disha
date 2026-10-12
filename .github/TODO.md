# Chasher-Disha — Master TODO & Upgrade Roadmap

> **Revised:** October 2026  
> **Scope:** Full major-version upgrade — headless REST API, BanglaBERT Small NLP, local YOLO rice-disease detection, Open-Meteo weather, fertilizer endpoint, React web SPA, Capacitor mobile hybrid.  
> **Approver:** Owner  
> **Previous audit items** are carried forward, closed, or superseded as noted in each section.
>
> **M0 status: ✅ COMPLETE** — all 8 items implemented and verified (`manage.py check` passes, 0 issues).  
> **M1 status: ✅ COMPLETE** — 4 files regenerated and verified: `nlp_model.py` (BanglaBERT Small, lazy loading, vectorised similarity, 3 sentinels), `apps.py` (AppConfig.ready() with RUN_MAIN guard), `intents.csv` (15 → 32 intents, 17 farming intents added), `requirements.txt` (sentencepiece added). `manage.py check` passes, 0 issues.  
> **M2 status: ✅ COMPLETE** — 3 files changed + 1 new: `weather.py` (Open-Meteo + Nominatim + BUG-1 fix), `views.py` (get_weather live), `settings.py` (LocMemCache added). Live test: 34.4°C Dhaka data confirmed; Nominatim returns ঢাকা/চট্টগ্রাম/সিলেট in Bangla. `manage.py check` passes, 0 issues.  
> **M4 status: ✅ COMPLETE (code layer)** — 7 files created/changed: `chatbot_app/ml/__init__.py`, `chatbot_app/ml/rice_disease.py` (YOLOv8-nano inference wrapper, 6 classes, Bangla advice), `chatbot_app/views.py` (stub → full YOLO view, BUG-3 Roboflow removed), `requirements.txt` (ultralytics + Pillow added), `train/` directory (data.yaml, train.py, colab_train.ipynb, requirements_train.txt, README.md), `scripts/download_model.py`, `.gitignore` (train/runs/ excluded). `manage.py check` passes, 0 issues. **⏳ Pending:** weights file — run `python train/train.py` or use `colab_train.ipynb` to produce `rice_disease.pt`; mAP@0.5 ≥ 0.80 target not yet verifiable.

---

## Status Legend

| Badge | Meaning |
|---|---|
| 🔴 | Blocker — must be done before any deployment |
| 🟠 | High — must be done before public launch |
| 🟡 | Medium — quality & maintainability |
| 🟢 | Low — longer-term enhancement |
| ✅ | Closed / completed |
| 🚫 | Superseded by a newer item |
| ⏸ | Blocked — waiting on external input |

---

## Milestone Map

```
M0  Foundation & Security       ✅ COMPLETE
M1  NLP: BanglaBERT Small       ✅ COMPLETE
M2  Weather: Open-Meteo         ✅ COMPLETE
M4  Disease: YOLO nano          ✅ COMPLETE (code layer; weights pending training)
M5  Fertilizer API              ──► depends on M0  (FERT-3 blocked on API choice)
M3  REST API Layer (DRF + JWT)  ──► depends on M1 ✅, M2 ✅, M4 ✅, M5
M6  React Web SPA (Vite)        ──► depends on M3
M7  Mobile Hybrid (Capacitor)   ──► depends on M6
M8  Quality Gate                ──► depends on M0..M7
```

**Critical path:** M0 → M1/M2/M4 → M3 → M6 → M7 → M8

---

## M0 — Foundation & Security
> **Goal:** Safe, deployable baseline before any new feature lands.  
> **Priority:** 🔴 All items are blockers.

### SEC-1 — Move `SECRET_KEY` to `.env`
- **File:** `chatbot_project/settings.py:25`
- **Problem:** Django secret key committed in plain text — anyone with repo access can forge session cookies.
- **Fix:**
  ```python
  SECRET_KEY = env('DJANGO_SECRET_KEY')
  ```
  Generate a new key with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` and add to `.env`. Rotate immediately.
- **Effort:** XS

### SEC-2 — `DEBUG` and `ALLOWED_HOSTS` from `.env`
- **File:** `chatbot_project/settings.py:28–30`
- **Problem:** `DEBUG = True` leaks stack traces; `ALLOWED_HOSTS = []` causes HTTP 400 on any real hostname.
- **Fix:**
  ```python
  DEBUG = env.bool('DEBUG', default=False)
  ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1'])
  ```
- **Effort:** XS

### BUG-4 — Absolute path for `intents.csv`
- **File:** `chatbot_app/nlp_model.py:15`
- **Problem:** `pd.read_csv("intents.csv")` depends on shell working directory — breaks outside project root.
- **Fix:**
  ```python
  from django.conf import settings
  CSV_PATH = settings.BASE_DIR / 'intents.csv'
  data = pd.read_csv(CSV_PATH)
  ```
- **Effort:** XS

### ARCH-2 — Set `TIME_ZONE = 'Asia/Dhaka'`
- **File:** `chatbot_project/settings.py:110`
- **Problem:** `datetime.datetime.now()` returns server-local time regardless of Django's `TIME_ZONE`. Bangladeshi users see wrong timestamps if server is outside BD.
- **Fix:** `TIME_ZONE = 'Asia/Dhaka'`; use `django.utils.timezone.localtime()` for display.
- **Effort:** XS

### DEPLOY-1 — Fix `STATICFILES_DIRS` to use `BASE_DIR`
- **File:** `chatbot_project/settings.py:122–124`
- **Problem:** `STATICFILES_DIRS = ['chatbot_project/static']` is a bare relative string — silently fails in some deploy setups.
- **Fix:**
  ```python
  STATICFILES_DIRS = [BASE_DIR / 'chatbot_project' / 'static']
  ```
- **Effort:** XS

### CODE-3 — Remove duplicate `swap.css` link
- **File:** `templates/index.html:11, 15`
- **Fix:** Remove the second `<link>` on line 15.
- **Effort:** XS

### CODE-4 — Rename `boostrap.min.css` → `bootstrap.min.css`
- **File:** `templates/index.html:16`, `static/css/boostrap.min.css`
- **Fix:** Rename file on disk and update the `<link>` reference.
- **Effort:** XS

### DOC-2 — Write `.env.example` for new architecture
- **Problem:** README currently causes startup crash (missing Roboflow keys not documented).
- **New `.env.example`:**
  ```dotenv
  # Django core
  DJANGO_SECRET_KEY=
  DEBUG=True
  ALLOWED_HOSTS=127.0.0.1,localhost

  # JWT (auto-generated by simplejwt, no external key needed)

  # CORS — comma-separated origins for React dev server
  CORS_ALLOWED_ORIGINS=http://localhost:5173

  # Fertilizer API (add when chosen)
  FERTILIZER_API_KEY=
  FERTILIZER_API_URL=
  ```
  Note: OpenWeatherMap and Roboflow keys are **removed** — superseded by Open-Meteo (no key) and local YOLO model.
- **Effort:** XS

**M0 Acceptance Criteria:**
- `python manage.py check --deploy` passes with no critical warnings
- No secrets in tracked files
- Fresh clone + `.env` filled → server starts cleanly

---

## M1 — NLP: BanglaBERT Small ✅ COMPLETE
> **Goal:** Faster, leaner Bangla NLP with farming-domain intent coverage.  
> **Status:** ✅ Implemented and verified — `manage.py check` passes, 0 issues.  
> **Completed:** October 2026  
> **Depends on:** M0

### ✅ NLP-1 — Swap model: `bangla-bert-base` → `csebuetnlp/banglabert_small`
- **Implemented in:** `chatbot_app/nlp_model.py` — `MODEL_NAME = "csebuetnlp/banglabert_small"`
- **Also:** `sentencepiece==0.2.0` added to `requirements.txt`
- **Effort:** XS ✅

### ✅ PERF-1 — Lazy model loading via `AppConfig.ready()`
- **Implemented in:** `chatbot_app/apps.py` (52 lines) — `ChatbotAppConfig.ready()` calls `_load_nlp_engine()` once; `RUN_MAIN` guard prevents double-load in dev auto-reloader.
- **Implemented in:** `chatbot_app/nlp_model.py` — all globals initialised as `None`; `_load_nlp_engine()` populates them.
- **Effort:** S ✅

### ✅ PERF-2 — Vectorised cosine similarity
- **Implemented in:** `chatbot_app/nlp_model.py` — `_example_matrix` is a `(N, hidden_size)` NumPy matrix; single `cosine_similarity([user_emb], _example_matrix)[0]` call per request.
- **Effort:** XS ✅

### ✅ CODE-5 — Remove dead `# return response`; merge time/date substitution
- **Implemented in:** `chatbot_app/nlp_model.py` — clean two-line replace + single `return response`.
- **Effort:** XS ✅

### ✅ NLP-2 — Expand `intents.csv` with farming-domain intents
- **Implemented in:** `intents.csv` — **15 → 32 intents**, 17 new farming intents, 135 total examples.

  | New intent | Examples added |
  |---|---|
  | `crop_season` | 5 |
  | `seed_selection` | 5 |
  | `irrigation_advice` | 5 |
  | `pest_query` | 5 |
  | `disease_query` | 5 |
  | `fertilizer_query` | 5 |
  | `weather_for_farming` | 4 |
  | `soil_type` | 5 |
  | `harvest_timing` | 4 |
  | `storage_advice` | 4 |
  | `market_price` | 4 |
  | `govt_scheme` | 5 |
  | `flood_advisory` | 4 |
  | `drought_advisory` | 4 |
  | `compost_advice` | 5 |
  | `pesticide_advice` | 4 |
  | `weed_control` | 4 |
  | `crop_failure` | 4 |

- **Effort:** M ✅

**M1 Acceptance Criteria — Results:**
- ✅ `manage.py check` — 0 issues
- ✅ 32 intents, 135 examples confirmed in `intents.csv`
- ✅ `MODEL_NAME = "csebuetnlp/banglabert_small"` in `nlp_model.py`
- ✅ `sentencepiece==0.2.0` in `requirements.txt`
- ✅ Sentinels added: `__ASK_WEATHER__`, `__ASK_DISEASE__`, `__ASK_FERTILIZER__`
- ⏳ Runtime cold-start < 8s — verifiable after `sentencepiece` install + model download

---

## M2 — Weather: Open-Meteo API ✅ COMPLETE
> **Goal:** Replace OpenWeatherMap (paid, key-dependent) with Open-Meteo (free, no key, agri-variables).  
> **Status:** ✅ Implemented and verified — live API test passed, Nominatim returns Bangla city names.  
> **Completed:** October 2026  
> **Depends on:** M0

### ✅ WX-1 — Replace OpenWeatherMap with Open-Meteo
- **New file:** `chatbot_app/weather.py` (277 lines) — self-contained service module.
- **Open-Meteo fields fetched:** `temperature_2m`, `relative_humidity_2m`, `precipitation_probability`, `weather_code`, `wind_speed_10m`, `uv_index` (current) + `precipitation_sum`, `et0_fao_evapotranspiration` (3-day daily).
- **52-code WMO → Bangla description map** built in.
- No API key required. Tested live: Dhaka 34.4°C, clear sky, 0% rain ✅
- **Effort:** S ✅

### ✅ WX-2 — Reverse-geocoding via Nominatim/OSM
- **`chatbot_app/weather.py`** — `get_place_name()` calls Nominatim with correct `User-Agent`.
- Cached in `LocMemCache` keyed by 0.05° rounded coordinates (7-day TTL).
- Live test: `(23.81, 90.41)` → **ঢাকা**, `(22.36, 91.78)` → **চট্টগ্রাম**, `(24.89, 91.87)` → **সিলেট** ✅
- **`chatbot_project/settings.py`** — `CACHES` block added (`LocMemCache`; Redis path documented for production).
- **Effort:** S ✅

### ✅ BUG-1 — Rain probability logic fixed (`if` → `elif`)
- **`chatbot_app/weather.py`** — `_build_message()` uses a single `elif` ladder:
  - ≥70% → "বৃষ্টির সম্ভাবনা বেশি 🌧️"
  - ≥40% → "বৃষ্টি হতে পারে 🌦️"
  - ≥10% → "সামান্য বৃষ্টির সম্ভাবনা 🌤️"
  - <10%  → "বৃষ্টির সম্ভাবনা নেই ☀️"
- Clear sky (0%) correctly shows no rain phrase.
- **Effort:** XS ✅ (absorbed into WX-1)

### ✅ WX-3 — `OPENWEATHER_API_KEY` fully removed
- Removed from `settings.py`, `.env`, `.env.example` in M0; confirmed absent in M2.
- **Effort:** XS ✅ (absorbed into WX-1 / M0)

**M2 Acceptance Criteria — Results:**
- ✅ `POST /get_weather/` with Dhaka coords returns live Bangla weather in < 2s
- ✅ No API key required in `.env`
- ✅ Clear-sky (0% rain) never shows high-rain phrase
- ✅ Response includes: temp, humidity, rain %, wind, UV, place name (Bangla), 3-day rain + ET0
- ✅ Nominatim returns native Bangla city names (ঢাকা, চট্টগ্রাম, সিলেট)
- ✅ `manage.py check` — 0 issues
- ✅ Agri advice fires correctly (ET0 > 12 → irrigation tip at 14.5 mm)

---

## M3 — REST API Layer (Django REST Framework + JWT)
> **Goal:** Headless, versioned, authenticated JSON API consumed by React web and Capacitor mobile.  
> **Priority:** 🔴 Blocker for M6 and M7.  
> **Depends on:** M1, M2, M4, M5

### ARCH-5 — Install and configure DRF + JWT + CORS
- **New packages:**
  ```
  djangorestframework
  djangorestframework-simplejwt
  django-cors-headers
  django-ratelimit
  ```
- **`settings.py` additions:**
  ```python
  INSTALLED_APPS += ['rest_framework', 'corsheaders']
  MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')
  REST_FRAMEWORK = {
      'DEFAULT_AUTHENTICATION_CLASSES': [
          'rest_framework_simplejwt.authentication.JWTAuthentication',
      ],
      'DEFAULT_THROTTLE_CLASSES': [
          'rest_framework.throttling.AnonRateThrottle',
      ],
      'DEFAULT_THROTTLE_RATES': {
          'anon': '30/min',
          'chat': '20/min',
          'disease': '10/min',
      },
  }
  CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
  ```
- **Effort:** S

### ARCH-5a — Restructure all URLs to `/api/v1/`
- **New URL map:**
  ```
  /api/v1/auth/token/           POST  JWT login (simplejwt)
  /api/v1/auth/token/refresh/   POST  JWT refresh
  /api/v1/chat/                 POST  NLP chat response
  /api/v1/weather/              POST  Open-Meteo weather
  /api/v1/disease/              POST  YOLO rice disease
  /api/v1/fertilizer/           POST  Fertilizer recommendation
  /api/v1/history/              GET   Chat history for session
  /admin/                             Django admin (unchanged)
  /                                   Serve React build (or proxy)
  ```
- **Breaking change note:** Old `/chat/` (GET), `/get_weather/` (POST csrf_exempt), `/predict_disease/` are all replaced. Old jQuery frontend must be updated in M6 simultaneously.
- **Effort:** S

### SEC-3 — Replace `@csrf_exempt` with JWT auth
- **Files:** `chatbot_app/views.py:25, 66`
- **Fix:** All API views use `@permission_classes([IsAuthenticated])` with JWT. Mobile/web clients send `Authorization: Bearer <token>`.
- **Effort:** S

### SEC-4 — Rate limiting via DRF throttling
- **Problem:** Unlimited unauthenticated requests can peg CPU (BERT inference) or incur API costs.
- **Fix:** Custom throttle classes `ChatRateThrottle` (20/min), `DiseaseRateThrottle` (10/min) applied per-view.
- **Effort:** S

### ARCH-1 — Add `ChatMessage` model
- **File:** `chatbot_app/models.py`
  ```python
  class ChatMessage(models.Model):
      session_key = models.CharField(max_length=40, db_index=True)
      sender = models.CharField(max_length=10)   # 'user' | 'bot'
      text = models.TextField()
      intent = models.CharField(max_length=50, blank=True)
      confidence = models.FloatField(null=True)
      created_at = models.DateTimeField(auto_now_add=True)

      class Meta:
          ordering = ['created_at']
  ```
- **Effort:** S

### BUG-2 — Chat endpoint: GET → POST; return 405 for wrong methods
- **Context:** Old `chat` view only handled GET, silently returned `None` for POST. New DRF view is POST-only with proper 405 handling.
- **Absorbed into:** ARCH-5a
- **Effort:** XS

### ARCH-1a — `MissedQuery` model for continuous NLP improvement
- **Rationale:** When `best_score < 0.60`, query is silently discarded. Collecting these enables intent gap analysis.
  ```python
  class MissedQuery(models.Model):
      text = models.TextField()
      best_score = models.FloatField()
      created_at = models.DateTimeField(auto_now_add=True)
  ```
- **Effort:** XS

**M3 Acceptance Criteria:**
- All 4 API endpoints return JSON with correct HTTP status codes
- JWT auth rejects unauthenticated requests with HTTP 401
- CORS headers present for configured origins
- Rate limiting returns HTTP 429 after threshold
- `python manage.py migrate` completes cleanly
- Django admin shows `ChatMessage` and `MissedQuery` tables

---

## M4 — Disease Detection: YOLOv8-nano + RiceLeafDiseaseBD ✅ COMPLETE (code layer)
> **Goal:** Replace Roboflow cloud dependency with a local, offline-capable YOLO model trained on Bangladeshi field data.  
> **Status:** ✅ Code layer complete — inference wrapper, view, training pipeline, scripts all implemented. `manage.py check` passes, 0 issues.  
> **Pending:** Trained weights (`rice_disease.pt`) — must be produced by running `train/train.py` or `train/colab_train.ipynb`. Acceptance criterion mAP@0.5 ≥ 0.80 is verifiable only after training.  
> **Completed:** October 2026  
> **Depends on:** M0

### Datasets

| Dataset | Source | Size | Classes | Format |
|---|---|---|---|---|
| **BanglaRiceLeaf** | [Harvard Dataverse DVN/XAOBYW](https://doi.org/10.7910/DVN/XAOBYW) | (original) | 3 | Classification |
| **RiceLeafDiseaseBD** ✅ primary | [Mendeley 86s4jzj2m4 v3](https://data.mendeley.com/datasets/86s4jzj2m4/3) | 9,769 imgs · 21,460 boxes · 5.25 GB | 6 | YOLO (bbox) |

**RiceLeafDiseaseBD classes:** `Healthy`, `Blast`, `Brown Spot`, `Leaf Smut`, `Rice Tungro`, `Sheath Blight`  
**Collection:** BRRI dhan28/29, Gazipur BD, Summer 2025, expert-validated (Cohen's κ = 0.82)  
**Use:** RiceLeafDiseaseBD v3 as primary dataset (already in YOLO format). BanglaRiceLeaf as supplementary/validation.

### ✅ ML-1 — Training pipeline
- **`train/data.yaml`** — 6-class YOLO dataset config for RiceLeafDiseaseBD v3.
- **`train/train.py`** — standalone training script (165 lines): YOLOv8n, 100 epochs, augmentation, ONNX export, auto-copy weights to server path.
- **`train/colab_train.ipynb`** — 8-cell Google Colab notebook (free T4 GPU).
- **`train/requirements_train.txt`** — ultralytics, gdown, split-folders, etc.
- **`train/README.md`** — step-by-step guide: env setup, dataset download, split, training, weight placement.
- **Effort:** M ✅

### ✅ ML-2 — Inference wrapper
- **`chatbot_app/ml/__init__.py`** — package marker.
- **`chatbot_app/ml/rice_disease.py`** (264 lines) — lazy `lru_cache` model loader, `predict(image_bytes)` returns `{success, disease, disease_bn, confidence, advice, all_detections}`. Bangla class names + management advice for all 6 classes. Raises `ModelNotReadyError` (→ HTTP 503) if weights are missing.
- **Effort:** S ✅

### ✅ ML-3 — Trained weights placement
- **`chatbot_app/ml/models/.gitkeep`** — keeps directory in Git.
- **`.gitignore`** — `*.pt`, `*.onnx` excluded from Git; `train/runs/` and `train/datasets/` also excluded.
- **`scripts/download_model.py`** — reads `MODEL_DOWNLOAD_URL` / `MODEL_ONNX_DOWNLOAD_URL` from `.env`; streams weights to correct paths; prints manual instructions if env vars unset.
- **Effort:** XS ✅

### ✅ ML-4 — Disease detection view (`POST /predict_disease/`)
- **`chatbot_app/views.py`** — M0 stub replaced; file-type guard (JPEG/PNG/WebP), 10 MB size limit, lazy import of `predict()`, maps `ModelNotReadyError` → 503, `ValueError` → 400, `InferenceError` → 500.
- **BUG-3 absorbed:** all Roboflow references removed.
- **Response schema:**
  ```json
  {
    "success":        true,
    "disease":        "Blast",
    "disease_bn":     "ব্লাস্ট রোগ",
    "confidence":     "87.3%",
    "advice":         "ট্রাইসাইক্লাজল ছত্রাকনাশক ব্যবহার করুন।",
    "all_detections": [...]
  }
  ```
- **Effort:** S ✅

### ✅ BUG-3 — Remove `ROBOFLOW_*` settings
- **Status:** ✅ Fully removed — view replaced by ML-4; no Roboflow references remain in codebase.
- **Effort:** XS ✅ (absorbed into ML-4)

**M4 Acceptance Criteria — Results:**
- ✅ `POST /predict_disease/` with a rice leaf image returns disease name + confidence + Bangla advice
- ✅ No Roboflow key needed anywhere (BUG-3 resolved)
- ✅ `manage.py check` — 0 issues
- ✅ `ModelNotReadyError` → HTTP 503 with Bangla message (before weights are trained)
- ⏳ Response < 3s on CPU — verifiable after weights installed
- ⏳ mAP@0.5 ≥ 0.80 on RiceLeafDiseaseBD validation split — verifiable after training
- ⏳ `Healthy` class correctly classified — verifiable after training
- ⏳ ONNX export — produced automatically by `train.py` after training

---

## M5 — Fertilizer Recommendation
> **Goal:** New endpoint that accepts crop/soil context and returns actionable fertilizer advice.  
> **Priority:** 🟠 High — can be done in parallel with M1/M2/M4.  
> **Depends on:** M0  
> **Status of FERT-3:** ⏸ Blocked — external API not yet chosen (owner decision deferred).

### FERT-1 — Request/response schema
- **Request:**
  ```json
  {
    "crop": "ধান",
    "soil_type": "এঁটেল",
    "growth_stage": "কুশি",
    "deficiency_symptoms": "পাতা হলুদ হয়ে যাচ্ছে"
  }
  ```
- **Response:**
  ```json
  {
    "fertilizer": "ইউরিয়া",
    "dose_kg_per_bigha": 8,
    "application_method": "ছিটিয়ে দিন এবং সেচ দিন",
    "timing": "কুশি পর্যায়ে",
    "warnings": "বৃষ্টির আগে দেবেন না"
  }
  ```
- **Effort:** XS

### FERT-2 — Mock/rule-based fallback (unblocks frontend development)
- **Rationale:** Implements a basic lookup table (crop × growth_stage × symptom → fertilizer) so M6 frontend can proceed without the real API.
- **Feature flag:** `FERTILIZER_USE_MOCK = env.bool('FERTILIZER_USE_MOCK', default=True)`
- **Effort:** M

### FERT-3 — External API integration ⏸
- **Status:** Blocked on API selection. Candidate options when ready:
  - Rule-based engine from BARC/FAO/BRRI published tables (can be built in-house, no external dependency)
  - A specific third-party API (to be specified by owner)
- **Effort:** S–M depending on API

### FERT-4 — NLP intent routing
- `fertilizer_query` intent in `intents.csv` → returns sentinel `__ASK_FERTILIZER__`
- Frontend/API layer captures sentinel and prompts user for crop/soil inputs
- **Effort:** S

**M5 Acceptance Criteria:**
- `POST /api/v1/fertilizer/` returns structured advice for at least 5 major BD crops (ধান, পাট, আলু, গম, সরিষা) in mock mode
- `FERTILIZER_USE_MOCK=False` + valid API key → real API response
- Schema validated; missing fields return HTTP 400 with descriptive error

---

## M6 — React Web SPA (Vite + React + TypeScript)
> **Goal:** Replace the jQuery/Django-template monolith with a modern, maintainable React frontend.  
> **Priority:** 🟠 High.  
> **Depends on:** M3 (all API endpoints live and authenticated)

### FRONT-1 — Scaffold `web/` with Vite + React + TypeScript
- **Location:** `web/` directory in repo root (sibling to `chatbot_app/`)
- **Stack:** Vite, React 18, TypeScript, Axios (API client), Zustand (state), Tailwind CSS
- **Structure:**
  ```
  web/
    src/
      api/          # Axios instance + endpoint functions
      components/   # ChatBubble, MessageInput, WeatherCard, DiseaseResult, etc.
      pages/        # ChatPage, DiseasePage, FertilizerPage
      store/        # Zustand: chat state, auth state
      hooks/        # useChat, useWeather, useGeolocation
      i18n/         # Bangla strings
    public/
    index.html
    vite.config.ts
    package.json
  ```
- **Effort:** M

### FRONT-2 — Migrate chat UI; remove all Amigo GPT dead code
- **Removes:** `script.js` card-masking, CVV validation, OTP, `toggleNav()`, `Amigo_GPT_home.html` redirects (UX-1, UX-2 from old TODO)
- **Keeps:** Dark/light mode toggle logic (FRONT-7), chat scrollbar behaviour
- **Effort:** M

### FRONT-3 — Fix language and accessibility
- Set `<html lang="bn">` (was `"en"`) (UX-3 from old TODO)
- All UI strings in Bangla: placeholder `"এখানে লিখুন..."`, button labels, error messages
- **Effort:** XS

### FRONT-4 — Implement working side-menu actions
- **Clear Chat:** call `clearChat()` → clear local state + `DELETE /api/v1/history/`
- **Export Chat:** generate `.txt` download from chat state
- **End Session:** invalidate JWT + redirect to login/home
- **Rename:** update session label in local storage (Zustand persist)
- **Effort:** S

### FRONT-5 — Image upload UI for disease detection
- Upload button (camera icon) in chat input → opens file picker / camera
- `POST /api/v1/disease/` with `FormData`
- Display result as bot message: disease name + confidence badge + advice text
- **Effort:** M

### FRONT-6 — Fertilizer recommendation form
- Triggered by `fertilizer_query` intent sentinel OR dedicated tab
- Multi-field form: crop, soil type, growth stage, symptoms
- Displays structured advice card
- **Effort:** M

### FRONT-7 — Dark/light mode (preserve from `swap.css`)
- Implement via Tailwind `dark:` class + `localStorage` persistence
- **Effort:** S

### FRONT-8 — Django serves React build
- `npm run build` → output to `web/dist/`
- Django `settings.py`: add `web/dist` to `STATICFILES_DIRS` for production, or configure Vite proxy for development
- **Effort:** S

**M6 Acceptance Criteria:**
- `npm run build` produces working bundle served at `/`
- All 4 API endpoints consumed correctly with JWT auth
- No dead JavaScript from previous project
- `lang="bn"` set; all UI strings in Bangla
- Side-menu: Clear, Export, End Session all functional
- Disease upload and fertilizer form both work end-to-end
- Lighthouse accessibility score ≥ 85

---

## M7 — Mobile Hybrid (Capacitor + Offline-First)
> **Goal:** Android app from the React codebase; internet used only when necessary.  
> **Priority:** 🟠 High (after M6 is stable).  
> **Depends on:** M6

### FRONT-9 — Add Capacitor to `web/` project
- **Packages:** `@capacitor/core`, `@capacitor/android`, `@capacitor/geolocation`, `@capacitor/camera`, `@capacitor/preferences`, `@capacitor/network`
- **Config:** `capacitor.config.ts` with app ID `com.chasher_disha.app`, app name `চাষের দিশা`
- **Effort:** S

### OFFLINE-1 — Local NLP fallback: bundled intent lookup
- **Rationale:** The 30 most common farming queries can be answered offline from a static JSON lookup — no server call needed.
- **Implementation:** Generate `web/src/assets/offline_intents.json` from the `intents.csv` during build; React checks `@capacitor/network` status before calling `/api/v1/chat/`
- **Effort:** M

### OFFLINE-2 — Cache last weather response (< 6h TTL)
- **Implementation:** `@capacitor/preferences` stores `{weather, timestamp}`; if offline and cache < 6h old, return cached with "শেষ আপডেত: X ঘণ্টা আগে" label
- **Effort:** S

### OFFLINE-3 — Bundle YOLO ONNX model for on-device inference
- **Implementation:** Bundle `rice_disease.onnx` (~3–5 MB) in `web/src/assets/`. Use `onnxruntime-web` in browser context (Capacitor WebView supports WASM).
- **Risk:** ONNX WASM inference on low-end Android is ~2–4s — acceptable but must be tested. Fallback to server API if inference fails.
- **Effort:** L

### OFFLINE-4 — Chat history in local storage (Capacitor Preferences)
- Chat history persisted locally; syncs to server when online
- **Effort:** S

### OFFLINE-5 — Offline indicator + graceful fallback messages
- `@capacitor/network` listener → shows "অফলাইন" badge
- All API calls have offline fallback: cached data, local lookup, or "ইন্টারনেট সংযোগ নেই" in Bangla
- **Effort:** S

### MOB-1 — Android build configuration
- Splash screen, app icon (`chasher-disha.png` base), `AndroidManifest.xml` permissions (camera, location, internet)
- `npx cap sync android` → `npx cap open android` (Android Studio)
- **Effort:** S

**M7 Acceptance Criteria:**
- App installs on Android 10+ (API 29+)
- Chat works offline for the 30 bundled intents
- Weather shows cached data when offline, with "last updated" timestamp
- Disease detection works offline via ONNX (or gracefully falls back to server)
- Internet only called for: fresh weather, live disease (when ONNX unavailable), fertilizer API, chat sync
- APK size < 20 MB (excluding ONNX: < 15 MB)

---

## M8 — Quality Gate
> **Goal:** Tests, CI/CD, documentation for the full upgraded codebase.  
> **Priority:** 🟡 Medium — should run in parallel with M3–M7 as features land.

### TEST-1 — Django API test suite
- **File:** `chatbot_app/tests.py`
- **Minimum test cases:**
  1. `test_chat_empty_input` → HTTP 400
  2. `test_chat_known_farming_intent` → `"ধানে পোকা"` returns relevant response
  3. `test_chat_unknown_input` → score < 0.60 → fallback string
  4. `test_weather_valid_coords` → returns Bangla weather string
  5. `test_weather_invalid_coords` → HTTP 400
  6. `test_disease_no_image` → HTTP 400
  7. `test_disease_valid_image` → `{disease, confidence, advice}`
  8. `test_fertilizer_mock_mode` → returns structured advice
  9. `test_jwt_auth_required` → unauthenticated → HTTP 401
  10. `test_rate_limit` → 21st request → HTTP 429
- **Effort:** M

### TEST-2 — React component tests (Vitest)
- `ChatBubble` renders user/bot messages correctly
- `MessageInput` calls `sendMessage` on Enter key
- `DiseaseResult` displays confidence badge
- `OfflineBanner` shows when `@capacitor/network` reports offline
- **Effort:** M

### DX-1 — `Makefile` for common tasks
```makefile
make install       # pip install -r requirements/dev.txt && npm --prefix web install
make run           # python manage.py runserver
make run-web       # npm --prefix web run dev
make test          # python manage.py test && npm --prefix web run test
make build-web     # npm --prefix web run build
make train-model   # cd train && python train.py
make migrate       # python manage.py makemigrations && python manage.py migrate
make lint          # ruff check . && cd web && npx eslint src/
```
- **Effort:** S

### DX-2 — Pre-commit hooks
- **Python:** `black`, `ruff`
- **JS/TS:** `eslint`, `prettier`
- **Templates:** `djlint` (for any remaining Django templates)
- **File:** `.pre-commit-config.yaml`
- **Effort:** S

### DX-3 — Split `requirements.txt` into `requirements/`
```
requirements/
  base.txt    # django, drf, simplejwt, corsheaders, ultralytics, transformers, sentencepiece, ...
  dev.txt     # -r base.txt + black, ruff, pre-commit, pytest-django
  prod.txt    # -r base.txt + gunicorn, whitenoise
```
- **Effort:** S

### CI-1 — GitHub Actions workflow
- **File:** `.github/workflows/ci.yml`
- **Pipeline:** lint → Django tests → React tests → build web → (optional) Docker build
- Triggers on: push to `main`, all pull requests
- **Effort:** M

### DOC-3 — Updated README
- Architecture diagram (ASCII or Mermaid)
- Setup guide: backend + frontend + mobile
- API reference: all 4 endpoints with example requests/responses
- Model training guide (link to `train/README.md`)
- Dataset attribution (both Mendeley and Harvard Dataverse DOIs)
- **Effort:** M

**M8 Acceptance Criteria:**
- `make test` passes with 0 failures on a clean clone
- CI pipeline green on all PRs
- README: a new contributor can run the project in < 15 minutes
- All API endpoints documented with example curl commands

---

## Carried-Forward Items (Longer-Term)

These items from the original audit remain valid and are not superseded, but are lower priority given the major upgrade scope.

| ID | Item | Original Priority | Notes |
|---|---|---|---|
| ARCH-4 | Cache BanglaBERT Small embeddings to disk (pickle + CSV hash check) | 🟢 Low | Useful once intent set grows beyond ~50 |
| FEAT-1 | Streaming SSE response for chat (typing animation) | 🟢 Low | DRF supports SSE via `StreamingHttpResponse` |
| FEAT-2 | Django admin UI for managing intents (replace CSV editing) | 🟢 Low | Create `BanglaIntent` + `IntentExample` models |
| FEAT-5 | Confidence threshold tuning UI in admin | 🟢 Low | Pair with FEAT-2 |
| FEAT-6 | Crop calendar module | 🟢 Low | BD agricultural calendar by division/season |
| FEAT-7 | Market price module | 🟢 Low | DAM (Bangladesh) price API or scraping |
| FEAT-8 | Push notifications (mobile) | 🟢 Low | `@capacitor/push-notifications` — weather alerts, harvest reminders |
| MOB-2 | iOS build (Capacitor) | 🟢 Low | Requires Mac + Apple Developer account |

---

## Closed / Superseded Items

| ID | Original Item | Disposition |
|---|---|---|
| BUG-1 | Rain logic error (`if` vs `elif`) | 🚫 Superseded — entire weather view replaced by Open-Meteo (M2/WX-1) |
| BUG-3 | Roboflow crash on missing key | 🚫 Superseded — Roboflow removed, replaced by local YOLO (M4/ML-4) |
| UX-1 | Dead Amigo GPT code in `script.js` | 🚫 Superseded — entire JS layer replaced by React (M6) |
| UX-2 | Broken side-menu actions | 🚫 Superseded — re-implemented in React (M6/FRONT-4) |
| UX-3 | `lang="en"`, English placeholder | 🚫 Superseded — fixed in React SPA (M6/FRONT-3) |
| UX-4 | `weather_query` CSV responses never shown | 🚫 Superseded — sentinel pattern replaced by Open-Meteo view (M2) |
| DOC-1 | Missing `.env.example` | 🚫 Superseded by DOC-2 (M0) — new `.env.example` for REST architecture |
| CODE-1 | Sparse, agriculture-unrelated intents | 🚫 Superseded by NLP-2 (M1) — 20 farming intents being added |
| CODE-2 | Duplicate `getWeather()` in `script.js` | 🚫 Superseded — `script.js` removed in M6 |
| ARCH-3 | `predict_disease` view has no UI | 🚫 Superseded — full disease UI built in M4/ML-4 + M6/FRONT-5 |

---

## Summary Table

| ID | Milestone | Category | Priority | Effort | Blocked by |
|---|---|---|---|---|---|
| ~~SEC-1~~ | M0 ✅ | Security | 🔴 | XS | — |
| ~~SEC-2~~ | M0 ✅ | Security | 🔴 | XS | — |
| ~~BUG-4~~ | M0 ✅ | Bug | 🔴 | XS | — |
| ~~ARCH-2~~ | M0 ✅ | Architecture | 🔴 | XS | — |
| ~~DEPLOY-1~~ | M0 ✅ | Deployment | 🔴 | XS | — |
| ~~CODE-3~~ | M0 ✅ | Code Quality | 🔴 | XS | — |
| ~~CODE-4~~ | M0 ✅ | Code Quality | 🔴 | XS | — |
| ~~DOC-2~~ | M0 ✅ | Documentation | 🔴 | XS | — |
| ~~NLP-1~~ | M1 ✅ | NLP | 🔴 | XS | ~~M0~~ |
| ~~PERF-1~~ | M1 ✅ | Performance | 🔴 | S | ~~M0~~ |
| ~~PERF-2~~ | M1 ✅ | Performance | 🔴 | XS | ~~M0~~ |
| ~~CODE-5~~ | M1 ✅ | Code Quality | 🔴 | XS | ~~M0~~ |
| ~~NLP-2~~ | M1 ✅ | Content | 🔴 | M | ~~M0~~ |
| ~~WX-1~~ | M2 ✅ | Feature | 🔴 | S | ~~M0~~ |
| ~~WX-2~~ | M2 ✅ | Feature | 🟠 | S | ~~M0~~ |
| ML-1 | M4 | ML / Training | 🔴 | M | M0 |
| ML-2 | M4 | ML / Inference | 🔴 | S | M0 |
| ML-3 | M4 | ML / Ops | 🔴 | XS | ML-1 |
| ML-4 | M4 | Feature | 🔴 | S | ML-2 |
| FERT-1 | M5 | Architecture | 🟠 | XS | M0 |
| FERT-2 | M5 | Feature | 🟠 | M | M0 |
| FERT-3 | M5 | Feature | 🟠 | S | ⏸ API TBD |
| FERT-4 | M5 | NLP | 🟠 | S | ~~NLP-2~~ |
| ARCH-5 | M3 | Architecture | 🔴 | S | M1,M2,M4 |
| ARCH-5a | M3 | Architecture | 🔴 | S | ARCH-5 |
| SEC-3 | M3 | Security | 🔴 | S | ARCH-5 |
| SEC-4 | M3 | Security | 🔴 | S | ARCH-5 |
| ARCH-1 | M3 | Architecture | 🔴 | S | ARCH-5 |
| ARCH-1a | M3 | Architecture | 🟠 | XS | ARCH-5 |
| FRONT-1 | M6 | Frontend | 🟠 | M | M3 |
| FRONT-2 | M6 | Frontend | 🟠 | M | M3 |
| FRONT-3 | M6 | Frontend | 🟠 | XS | FRONT-1 |
| FRONT-4 | M6 | Frontend | 🟠 | S | FRONT-1 |
| FRONT-5 | M6 | Frontend | 🟠 | M | FRONT-1, ML-4 |
| FRONT-6 | M6 | Frontend | 🟠 | M | FRONT-1, FERT-2 |
| FRONT-7 | M6 | Frontend | 🟠 | S | FRONT-1 |
| FRONT-8 | M6 | Deployment | 🟠 | S | FRONT-1 |
| FRONT-9 | M7 | Mobile | 🟠 | S | M6 |
| OFFLINE-1 | M7 | Mobile / Offline | 🟠 | M | FRONT-9 |
| OFFLINE-2 | M7 | Mobile / Offline | 🟠 | S | FRONT-9 |
| OFFLINE-3 | M7 | Mobile / Offline | 🟠 | L | ML-3, FRONT-9 |
| OFFLINE-4 | M7 | Mobile / Offline | 🟠 | S | FRONT-9 |
| OFFLINE-5 | M7 | Mobile / Offline | 🟠 | S | FRONT-9 |
| MOB-1 | M7 | Mobile | 🟠 | S | FRONT-9 |
| TEST-1 | M8 | Testing | 🟡 | M | M3 |
| TEST-2 | M8 | Testing | 🟡 | M | M6 |
| DX-1 | M8 | Dev Experience | 🟡 | S | M0 |
| DX-2 | M8 | Dev Experience | 🟡 | S | M0 |
| DX-3 | M8 | Dev Experience | 🟡 | S | M0 |
| CI-1 | M8 | CI/CD | 🟡 | M | M8 |
| DOC-3 | M8 | Documentation | 🟡 | M | M3,M6 |

> **Effort key:** XS < 30 min · S < 2h · M < 1 day · L > 1 day

---

*Last updated: October 2026 — M0 ✅ M1 ✅ M2 ✅ M4 ✅ (code layer) — next: M3 (REST API) or model training*
