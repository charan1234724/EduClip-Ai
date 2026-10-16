"""Pixabay video search/download service with short-video filtering."""
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.conf import settings

PIXABAY_API_URL = "https://pixabay.com/api/videos/"
PIXABAY_CDN_HOSTS = {"cdn.pixabay.com"}
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
REQUEST_TIMEOUT = (10, 45)
MIN_VIDEO_DURATION_SECONDS = 15


class PixabayServiceError(Exception):
    pass


def _api_key():
    key = os.getenv("PIXABAY_API_KEY") or getattr(settings, "PIXABAY_API_KEY", "")
    if not key:
        raise PixabayServiceError(
            "PIXABAY_API_KEY is missing. Add it to the root .env file and restart Django."
        )
    return key


def search_pixabay_videos(query: str, per_page: int = 9, min_duration: int = MIN_VIDEO_DURATION_SECONDS):
    query = (query or "").strip()
    if not query:
        raise PixabayServiceError("A search keyword is required.")

    per_page = max(3, min(int(per_page), 20))
    min_duration = max(0, min(int(min_duration), 600))

    try:
        response = requests.get(
            PIXABAY_API_URL,
            params={
                "key": _api_key(),
                "q": query,
                "per_page": min(50, max(per_page * 3, 20)),
                "safesearch": "true",
                "video_type": "all",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 401:
            raise PixabayServiceError("Pixabay rejected the API key. Check PIXABAY_API_KEY.")
        response.raise_for_status()
        payload = response.json()
    except PixabayServiceError:
        raise
    except requests.RequestException as exc:
        raise PixabayServiceError(f"Pixabay search request failed: {exc}") from exc
    except ValueError as exc:
        raise PixabayServiceError("Pixabay returned an invalid response.") from exc

    videos = []
    for hit in payload.get("hits", []):
        duration = int(hit.get("duration") or 0)
        if duration < min_duration:
            continue

        variants = hit.get("videos") or {}
        chosen = next(
            (
                variants.get(size)
                for size in ("large", "medium", "small", "tiny")
                if (variants.get(size) or {}).get("url")
            ),
            {},
        )
        if not chosen.get("url"):
            continue

        videos.append({
            "id": hit.get("id"),
            "title": hit.get("tags") or f"Pixabay video {hit.get('id', '')}",
            "tags": hit.get("tags", ""),
            "user": hit.get("user", ""),
            "duration": duration,
            "views": hit.get("views", 0),
            "pageURL": hit.get("pageURL", ""),
            "thumbnail": chosen.get("thumbnail", ""),
            "download_url": chosen["url"],
            "videos": variants,
        })
        if len(videos) >= per_page:
            break

    return {
        "status": "success",
        "total": payload.get("total", 0),
        "min_duration_seconds": min_duration,
        "videos": videos,
        "message": (
            f"Showing videos at least {min_duration} seconds long."
            if videos else
            f"No videos at least {min_duration} seconds long were found. Try another keyword."
        ),
    }


def _safe_pixabay_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme == "https"
            and parsed.hostname in PIXABAY_CDN_HOSTS
            and not parsed.username
            and not parsed.password
        )
    except (TypeError, ValueError):
        return False


def download_pixabay_video(download_url: str, title: str = "pixabay-video"):
    if not _safe_pixabay_url(download_url):
        raise PixabayServiceError(
            "Rejected media URL. Only direct HTTPS URLs from cdn.pixabay.com are accepted."
        )

    parsed = urlparse(download_url)
    if "download=1" not in parsed.query.split("&"):
        download_url += "&download=1" if parsed.query else "?download=1"

    folder = Path(settings.MEDIA_ROOT) / "pixabay_downloads"
    folder.mkdir(parents=True, exist_ok=True)
    safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", (title or "pixabay-video")).strip("._")
    safe_title = (safe_title or "pixabay-video")[:70]
    import uuid

    output_path = folder / f"{safe_title}_{uuid.uuid4().hex[:8]}.mp4"

    try:
        with requests.get(
            download_url,
            stream=True,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
            headers={"User-Agent": "EduClipAI/1.0"},
        ) as response:
            if response.is_redirect:
                raise PixabayServiceError(
                    "Pixabay's media URL redirected. Search again and retry with a fresh result."
                )
            response.raise_for_status()
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    content_length = int(content_length)
                except ValueError as exc:
                    raise PixabayServiceError(
                        "The server returned an invalid Content-Length header."
                    ) from exc

            if content_length < 0:
                raise PixabayServiceError(
                    "The server returned an invalid Content-Length header."
                )

            if content_length > MAX_DOWNLOAD_BYTES:
                raise PixabayServiceError(
                    "This file is larger than the 100 MB demo limit."
                )

            total_bytes = 0
            temp_path = output_path.with_suffix(".part")
            try:
                with temp_path.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=256 * 1024):
                        if not chunk:
                            continue
                        total_bytes += len(chunk)
                        if total_bytes > MAX_DOWNLOAD_BYTES:
                            raise PixabayServiceError("Download exceeded the 100 MB demo limit.")
                        output.write(chunk)
                if total_bytes == 0:
                    raise PixabayServiceError("Pixabay returned an empty video file.")
                temp_path.replace(output_path)
            except Exception:
                temp_path.unlink(missing_ok=True)
                raise
    except PixabayServiceError:
        raise
    except requests.RequestException as exc:
        raise PixabayServiceError(f"Pixabay download failed: {exc}") from exc
    except OSError as exc:
        raise PixabayServiceError(f"Could not save the downloaded file: {exc}") from exc

    return {
        "file_path": str(output_path),
        "relative_path": str(output_path.relative_to(Path(settings.MEDIA_ROOT))),
        "size_bytes": output_path.stat().st_size,
    }
