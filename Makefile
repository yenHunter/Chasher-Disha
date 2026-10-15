# Makefile — Chasher-Disha developer shortcuts
# Usage: make <target>
# Requires: GNU Make (Windows: install via `winget install GnuWin32.Make`)

PYTHON   = .\env\Scripts\python.exe
PIP      = .\env\Scripts\pip.exe
MANAGE   = $(PYTHON) manage.py
NPM      = npm --prefix web

.PHONY: install run run-web test test-django test-web build-web \
        migrate lint lint-py lint-web format train-model \
        cap-sync cap-open clean

# ── Setup ────────────────────────────────────────────────────────────────────
install:
	$(PIP) install -r requirements/dev.txt
	$(NPM) install

# ── Run ──────────────────────────────────────────────────────────────────────
run:
	$(MANAGE) runserver

run-web:
	$(NPM) run dev

# ── Test ─────────────────────────────────────────────────────────────────────
test: test-django test-web

test-django:
	$(PYTHON) -m pytest chatbot_app/tests.py -v --tb=short

test-django-cov:
	$(PYTHON) -m pytest chatbot_app/tests.py -v --tb=short \
	    --cov=chatbot_app --cov-report=term-missing --cov-report=html

test-web:
	$(NPM) run test

# ── Build ────────────────────────────────────────────────────────────────────
build-web:
	$(NPM) run build

# ── Database ─────────────────────────────────────────────────────────────────
migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

# ── Lint / Format ────────────────────────────────────────────────────────────
lint: lint-py lint-web

lint-py:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m black --check .

lint-web:
	$(NPM) run lint

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m black .

# ── Model training ───────────────────────────────────────────────────────────
train-model:
	cd train && $(PYTHON) train.py

# ── Capacitor / Android ──────────────────────────────────────────────────────
cap-sync: build-web
	cd web && npx cap sync android

cap-open:
	cd web && npx cap open android

# ── Housekeeping ─────────────────────────────────────────────────────────────
clean:
	Get-ChildItem -Recurse -Include __pycache__,*.pyc | Remove-Item -Recurse -Force
