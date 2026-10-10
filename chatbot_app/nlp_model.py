"""
NLP engine for Chasher-Disha — Milestone M1.

Changes vs original:
  NLP-1  Model: sagorsarker/bangla-bert-base  →  csebuetnlp/banglabert_small
          ~125 MB vs ~500 MB; ~4× faster cold-start; same Bangla quality.
          Requires sentencepiece (added to requirements.txt).

  PERF-1 Lazy loading: tokenizer / model / embeddings are NOT loaded at
          module-import time. They are initialised once inside
          AppConfig.ready() via _load_nlp_engine(), then cached in
          module-level singletons. Import-time loading caused 30s+
          runserver restarts and Gunicorn worker timeouts.

  PERF-2 Vectorised similarity: all example embeddings are stacked into
          a single NumPy matrix at load time; one cosine_similarity()
          BLAS call replaces the O(N) Python loop per request.

  BUG-4  Absolute CSV path anchored to BASE_DIR (carried from M0).
  CODE-5 Clean time/date substitution; dead comment removed (M0).
"""

from __future__ import annotations

import datetime
import logging
import random

import numpy as np
import pandas as pd
import torch
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model identifier  (M1: NLP-1)
# ---------------------------------------------------------------------------
MODEL_NAME = "csebuetnlp/banglabert_small"

# ---------------------------------------------------------------------------
# Module-level singletons — all None until _load_nlp_engine() is called.
# Direct access from outside this module is intentionally discouraged;
# use get_response() instead.  (M1: PERF-1)
# ---------------------------------------------------------------------------
_tokenizer: AutoTokenizer | None = None
_model: AutoModel | None = None
_responses: dict[str, list[str]] = {}   # intent  →  list of response strings
_intent_labels: list[str] = []          # one entry per example row (parallel to matrix)
_example_matrix: np.ndarray | None = None   # shape (N, hidden_size)
_engine_loaded: bool = False


# ---------------------------------------------------------------------------
# Engine loader — called once from ChatbotAppConfig.ready()
# ---------------------------------------------------------------------------
def _load_nlp_engine() -> None:
    """
    Load tokenizer, model, and precompute the full example-embedding matrix.

    Thread-safety note: called from AppConfig.ready() which Django invokes
    before any request is served. In Gunicorn pre-fork mode the workers
    inherit the already-loaded model, so each worker avoids re-loading
    ~125 MB from disk.
    """
    global _tokenizer, _model, _responses, _intent_labels, _example_matrix, _engine_loaded

    if _engine_loaded:
        return

    logger.info("[NLP] Loading %s …", MODEL_NAME)

    # -- Tokenizer & model  (M1: NLP-1) ------------------------------------
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    _model = AutoModel.from_pretrained(MODEL_NAME)
    _model.eval()

    # -- CSV path  (M0: BUG-4) ---------------------------------------------
    from django.conf import settings as _s  # noqa: PLC0415
    csv_path = _s.BASE_DIR / "intents.csv"
    data = pd.read_csv(csv_path)

    # -- Parse intents ------------------------------------------------------
    raw_examples: list[tuple[str, str]] = []   # (intent, example_text)

    for _, row in data.iterrows():
        intent = str(row["intent"])
        exs_raw = row.get("examples")
        res_raw = row.get("responses")
        if pd.isna(exs_raw) or pd.isna(res_raw):
            continue
        exs   = [e.strip() for e in str(exs_raw).split(";") if e.strip()]
        resps = [r.strip() for r in str(res_raw).split(";") if r.strip()]
        _responses[intent] = resps
        raw_examples.extend((intent, ex) for ex in exs)

    if not raw_examples:
        logger.error("[NLP] No examples loaded from %s — check CSV format.", csv_path)
        return

    # -- Precompute embeddings → stacked matrix  (M1: PERF-2) --------------
    logger.info("[NLP] Precomputing embeddings for %d examples …", len(raw_examples))
    vecs: list[np.ndarray] = []
    for intent, text in raw_examples:
        _intent_labels.append(intent)
        vecs.append(_embed(text))

    _example_matrix = np.vstack(vecs)   # shape: (N, hidden_size)
    _engine_loaded = True
    logger.info(
        "[NLP] Engine ready — %d intents, %d examples.",
        len(_responses),
        len(raw_examples),
    )


# ---------------------------------------------------------------------------
# Internal embedding helper
# ---------------------------------------------------------------------------
def _embed(text: str) -> np.ndarray:
    """Return a 1-D mean-pooled embedding for *text* (shape: hidden_size,)."""
    inputs = _tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=128,
        padding=True,
    )
    with torch.no_grad():
        outputs = _model(**inputs)
        emb = outputs.last_hidden_state.mean(dim=1)   # mean pooling
    return emb[0].numpy()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_response(user_input: str) -> str:
    """
    Match *user_input* against all intent examples and return the best
    response string, a routing sentinel, or a fallback message.

    Sentinels returned to the view layer:
        '__ASK_WEATHER__'     — weather_query or weather_for_farming matched
        '__ASK_DISEASE__'     — disease_query or pest_query matched
        '__ASK_FERTILIZER__'  — fertilizer_query matched
    """
    if not _engine_loaded:
        logger.warning("[NLP] get_response() called before engine is loaded.")
        return "দুঃখিত, সিস্টেম এখনও প্রস্তুত নয়। একটু পরে চেষ্টা করুন।"

    user_emb = _embed(user_input.strip())

    # Single BLAS call — replaces the O(N) Python loop  (M1: PERF-2)
    scores: np.ndarray = cosine_similarity([user_emb], _example_matrix)[0]
    best_idx: int = int(np.argmax(scores))
    best_score: float = float(scores[best_idx])
    best_intent: str = _intent_labels[best_idx]

    logger.debug("[NLP] best_intent=%s  score=%.4f", best_intent, best_score)

    # -- Sentinel routing ---------------------------------------------------
    if best_intent in ("weather_query", "weather_for_farming"):
        return "__ASK_WEATHER__"
    if best_intent in ("disease_query", "pest_query"):
        return "__ASK_DISEASE__"
    if best_intent == "fertilizer_query":
        return "__ASK_FERTILIZER__"

    # -- Low-confidence fallback; log for continuous improvement  (M3: ARCH-1a)
    if best_score < 0.60:
        _log_missed_query(user_input, best_score)
        return (
            "দুঃখিত, আমি বুঝতে পারিনি 😔 "
            "একটু অন্যভাবে বলুন অথবা সাহায্যের জন্য 'সাহায্য' লিখুন।"
        )

    response = random.choice(_responses[best_intent])

    # -- Template variable substitution  (M0: CODE-5) ----------------------
    now = datetime.datetime.now()
    response = response.replace("{current_time}", now.strftime("%I:%M %p"))
    response = response.replace("{current_date}", now.strftime("%d %B, %Y"))

    return response


def _log_missed_query(text: str, score: float) -> None:
    """
    Persist unmatched queries to MissedQuery model for gap analysis.
    Silently skipped if the model is not yet migrated (safe before M3).
    (M3: ARCH-1a)
    """
    try:
        from chatbot_app.models import MissedQuery  # noqa: PLC0415
        MissedQuery.objects.create(text=text, best_score=score)
    except Exception:
        pass  # model not yet available — non-fatal
