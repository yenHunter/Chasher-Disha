"""
admin.py — Django admin registrations for Chasher-Disha.

M3: ARCH-1  — ChatMessage visible in admin
M3: ARCH-1a — MissedQuery visible in admin (intent gap analysis)
"""

from django.contrib import admin

from .models import ChatMessage, MissedQuery


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display  = ('id', 'session_key', 'sender', 'short_text', 'intent', 'confidence', 'created_at')
    list_filter   = ('sender', 'intent')
    search_fields = ('session_key', 'text', 'intent')
    readonly_fields = ('created_at',)
    ordering      = ('-created_at',)

    @admin.display(description='Text (preview)')
    def short_text(self, obj):
        return obj.text[:80] + ('…' if len(obj.text) > 80 else '')


@admin.register(MissedQuery)
class MissedQueryAdmin(admin.ModelAdmin):
    list_display  = ('id', 'short_text', 'best_score', 'created_at')
    search_fields = ('text',)
    readonly_fields = ('created_at',)
    ordering      = ('-created_at',)

    @admin.display(description='Query (preview)')
    def short_text(self, obj):
        return obj.text[:100] + ('…' if len(obj.text) > 100 else '')
