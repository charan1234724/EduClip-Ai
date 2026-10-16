from django.contrib import admin

from .models import (
    GeneratedClip,
    Topic,
    Transcript,
    TranscriptSegment,
    Video,
)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "difficulty",
        "trend_score",
        "created_at",
    )
    search_fields = ("title", "category")
    list_filter = ("category", "difficulty")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "youtube_id")
    fields = (
        "topic",
        "youtube_id",
        "title",
        "channel",
        "url",
        "thumbnail",
        "view_count",
        "duration",
        "source_file",
    )
    search_fields = ("title", "channel")
    list_filter = ("channel",)


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = (
        "video",
        "language",
        "created_at",
    )
    search_fields = ("video__title",)


@admin.register(TranscriptSegment)
class TranscriptSegmentAdmin(admin.ModelAdmin):
    list_display = (
        "transcript",
        "start_time",
        "end_time",
    )
    search_fields = ("text",)


@admin.register(GeneratedClip)
class GeneratedClipAdmin(admin.ModelAdmin):
    list_display = (
        "video",
        "start_time",
        "end_time",
        "created_at",
    )
    search_fields = ("video__title",)