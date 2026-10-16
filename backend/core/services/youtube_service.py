
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=True)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_BASE_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(Exception):
    """Raised when the YouTube Data API request fails."""


def search_youtube_videos(query, max_results=10):
    """
    Search YouTube for videos and return basic video metadata.
    This function searches for videos; it does not download them.
    """
    if not YOUTUBE_API_KEY:
        raise YouTubeAPIError(
            "YouTube API key is missing. Check the root .env file."
        )

    query = query.strip() if isinstance(query, str) else ""

    if not query:
        raise ValueError("Search query cannot be empty.")

    max_results = max(1, min(int(max_results), 50))

    search_response = requests.get(
        f"{YOUTUBE_API_BASE_URL}/search",
        params={
            "key": YOUTUBE_API_KEY,
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "safeSearch": "moderate",
        },
        timeout=20,
    )

    if not search_response.ok:
        try:
            error_data = search_response.json()
            message = error_data.get("error", {}).get(
                "message", "YouTube API request failed."
            )
        except ValueError:
            message = "YouTube API request failed."

        raise YouTubeAPIError(message)

    search_data = search_response.json()
    items = search_data.get("items", [])

    video_ids = [
        item.get("id", {}).get("videoId")
        for item in items
        if item.get("id", {}).get("videoId")
    ]

    if not video_ids:
        return []

    details_response = requests.get(
        f"{YOUTUBE_API_BASE_URL}/videos",
        params={
            "key": YOUTUBE_API_KEY,
            "part": "snippet,statistics,contentDetails",
            "id": ",".join(video_ids),
        },
        timeout=20,
    )

    if not details_response.ok:
        try:
            error_data = details_response.json()
            message = error_data.get("error", {}).get(
                "message", "Could not retrieve video details."
            )
        except ValueError:
            message = "Could not retrieve video details."

        raise YouTubeAPIError(message)

    details_data = details_response.json()
    details_by_id = {
        item["id"]: item
        for item in details_data.get("items", [])
    }

    results = []

    # Preserve the original search order.
    for video_id in video_ids:
        item = details_by_id.get(video_id)

        if not item:
            continue

        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        thumbnails = snippet.get("thumbnails", {})
        thumbnail = (
            thumbnails.get("high")
            or thumbnails.get("medium")
            or thumbnails.get("default")
            or {}
        )

        results.append({
            "youtube_id": video_id,
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": thumbnail.get("url", ""),
            "view_count": int(statistics.get("viewCount", 0)),
            "duration": item.get("contentDetails", {}).get(
                "duration", ""
            ),
            "published_at": snippet.get("publishedAt", ""),
        })

    return results
