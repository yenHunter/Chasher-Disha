"""
models.py — Django ORM models for Chasher-Disha.

M3: ARCH-1  — ChatMessage: persistent conversation history per session.
M3: ARCH-1a — MissedQuery: captures low-confidence NLP inputs for gap analysis.
"""

from django.db import models


# ---------------------------------------------------------------------------
# M3: ARCH-1 — Chat history
# ---------------------------------------------------------------------------
class ChatMessage(models.Model):
    """
    One turn in a chat conversation, keyed by session.

    session_key  — Django session key (40 chars) or a JWT sub claim (UUID).
                   Used to group messages into a conversation thread.
    sender       — 'user' | 'bot'
    text         — Raw message text (user input or bot response).
    intent       — NLP-detected intent label (blank for user messages or
                   when confidence is below threshold).
    confidence   — Cosine similarity score from BanglaBERT (null for user
                   messages and sentinel responses).
    created_at   — UTC timestamp; ordering is by this field.
    """

    SENDER_USER = 'user'
    SENDER_BOT  = 'bot'
    SENDER_CHOICES = [
        (SENDER_USER, 'User'),
        (SENDER_BOT,  'Bot'),
    ]

    session_key = models.CharField(max_length=64, db_index=True)
    sender      = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text        = models.TextField()
    intent      = models.CharField(max_length=60, blank=True, default='')
    confidence  = models.FloatField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering   = ['created_at']
        indexes    = [models.Index(fields=['session_key', 'created_at'])]
        verbose_name        = 'Chat Message'
        verbose_name_plural = 'Chat Messages'

    def __str__(self) -> str:
        preview = self.text[:50] + ('…' if len(self.text) > 50 else '')
        return f'[{self.sender}] {preview}'


# ---------------------------------------------------------------------------
# M3: ARCH-1a — Missed query log for continuous NLP improvement
# ---------------------------------------------------------------------------
class MissedQuery(models.Model):
    """
    Records user inputs that fell below the NLP confidence threshold (< 0.60).

    Collecting these enables intent gap analysis:
      - Which phrases are farmers actually using?
      - Which intents are under-represented in intents.csv?

    Used by: chatbot_app/nlp_model.py → _log_missed_query()
    """

    text       = models.TextField()
    best_score = models.FloatField(
        help_text='Highest cosine similarity score achieved (< 0.60)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering            = ['-created_at']
        verbose_name        = 'Missed Query'
        verbose_name_plural = 'Missed Queries'

    def __str__(self) -> str:
        preview = self.text[:60] + ('…' if len(self.text) > 60 else '')
        return f'{preview}  (score={self.best_score:.3f})'
