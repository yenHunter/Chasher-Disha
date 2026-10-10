import logging
import os

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class ChatbotAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "chatbot_app"

    def ready(self) -> None:
        """
        Load the NLP engine exactly once at Django startup.  (M1: PERF-1)

        Why AppConfig.ready():
          - The app registry is fully initialised before this runs, so
            accessing settings and models here is safe.
          - Gunicorn pre-fork: the master process loads the model once;
            workers inherit it — no per-worker reload of ~125 MB.
          - Dev auto-reloader: Django spawns a parent watcher process and a
            child worker. RUN_MAIN='true' is set only in the child, so we
            skip loading in the parent to avoid double-loading.
        """
        if self._is_reloader_parent():
            return

        try:
            from chatbot_app.nlp_model import _load_nlp_engine  # noqa: PLC0415
            _load_nlp_engine()
        except Exception as exc:  # noqa: BLE001
            # Non-fatal at startup: chat endpoint returns a graceful error
            # until the engine becomes available.
            logger.error("[NLP] Engine failed to load: %s", exc, exc_info=True)

    @staticmethod
    def _is_reloader_parent() -> bool:
        """
        Return True when running as Django's dev-server reloader parent
        process (RUN_MAIN is unset or not 'true').

        In production (Gunicorn / uWSGI) RUN_MAIN is never set, so this
        always returns False and the engine loads normally.
        """
        run_main = os.environ.get("RUN_MAIN")
        # Production: RUN_MAIN is absent → always load
        if run_main is None:
            return False
        # Dev child worker: RUN_MAIN='true' → load
        # Dev reloader parent: RUN_MAIN='false' (or anything else) → skip
        return run_main != "true"
