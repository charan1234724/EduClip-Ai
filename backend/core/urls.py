
from django.urls import path

from . import views

from .views import (
    health_check,
    topic_list,
    video_list,
    transcript_list,
    transcript_segment_list,
    generated_clip_list,
    search_youtube,
    TranscribeAudioView,
    ImportCaptionsView,
    enhance_clip_text,
    generate_clip,
    test_ai,
    generate_topics,
    search_licensed_media,
    download_licensed_media,
    search_internet_archive_media,
    pixabay_video_search,
    pixabay_video_download,
    narrated_clip_files,
    TranscribeYouTubeView,
)

urlpatterns = [
    path(
        "health/",
        health_check,
        name="health-check",
    ),

    path(
        "topics/",
        topic_list,
        name="topic-list",
    ),

    path(
        "videos/",
        video_list,
        name="video-list",
    ),

    path(
        "transcripts/",
        transcript_list,
        name="transcript-list",
    ),

    path(
        "transcript-segments/",
        transcript_segment_list,
        name="transcript-segment-list",
    ),

    path(
        "clips/",
        generated_clip_list,
        name="generated-clip-list",
    ),

    path("ai/test/", test_ai, name="test-ai"),
    path("clips/generate/", generate_clip, name="generate_clip"),

    path("topics/generate/", generate_topics, name="generate-topics"),
    path("youtube/search/", search_youtube, name="youtube-search"),
    path("transcribe/", TranscribeAudioView.as_view(), name="transcribe-audio"),
    path(
    "ai/enhance-clip/",
    enhance_clip_text,
    name="enhance_clip_text",
),
    path(
    "transcripts/import-captions/",
    ImportCaptionsView.as_view(),
    name="import-captions",
),
    path(
    "licensed-media/search/",
    search_licensed_media,
    name="licensed-media-search",
),
    path(
    "licensed-media/download/",
    download_licensed_media,
    name="licensed-media-download"
),
    path(
    "licensed-media/internet-archive/search/",
    search_internet_archive_media,
    name="internet-archive-search",
),
    path(
    "licensed-media/pixabay/search/",
    pixabay_video_search,
    name="pixabay-video-search",
),
    path(
    "licensed-media/pixabay/download/",
    pixabay_video_download,
    name="pixabay-video-download",
),
    path(
    "narrated-clips/generate/",
    views.generate_narrated_video,
    name="generate-narrated-video",
),
    path(
    "narrated-clips/",
    narrated_clip_files,
    name="narrated-clip-files",
),
    path(
    "transcribe-youtube/",
    TranscribeYouTubeView.as_view(),
    name="transcribe-youtube",
),
]
