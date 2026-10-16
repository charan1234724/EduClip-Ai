
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from django.conf import settings


COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "EduClipAI/1.0 (licensed educational media processing)"
MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024  # 500 MB

ALLOWED_LICENSE_PREFIXES = (
    "cc0",
    "cc by",
    "cc by-sa",
    "public domain",
)

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".ogv",
    ".ogg",
    ".mov",
    ".m4v",
}


def _metadata_text(metadata, key):
    value = metadata.get(key, "")

    if isinstance(value, dict):
        value = value.get("value", "")

    return re.sub(r"<[^>]*>", "", str(value)).strip()


def _license_is_allowed(name, license_url):
    name = (name or "").strip().lower()
    url = (license_url or "").strip().lower()

    if not name or not url:
        return False

    if not url.startswith("https://"):
        return False

    return any(
        name == prefix
        or name.startswith(prefix + " ")
        or name.startswith(prefix + "-")
        for prefix in ALLOWED_LICENSE_PREFIXES
    )


def _raise_for_rate_limit(response):
    if response.status_code != 429:
        response.raise_for_status()
        return

    retry_after = response.headers.get("Retry-After")

    if retry_after and retry_after.isdigit():
        wait_message = (
            f" Wait at least {retry_after} seconds before retrying."
        )
    else:
        wait_message = (
            " Wait at least 5 minutes before trying again."
        )

    raise RuntimeError(
        "Wikimedia is temporarily rate-limiting downloads."
        + wait_message
    )


def download_licensed_video(source_id):
    """
    Verify a Wikimedia Commons video and its license, then save it
    under MEDIA_ROOT/licensed_media/.

    Returns source metadata and the relative local file path.
    Does not automatically retry rate-limited requests.
    """
    source_id = (source_id or "").strip()

    if not source_id.startswith("File:") or len(source_id) > 255:
        raise ValueError("Select a valid Wikimedia Commons file.")

    headers = {"User-Agent": USER_AGENT}

    # Step 1: Retrieve the exact source metadata.
    try:
        response = requests.get(
            COMMONS_API_URL,
            params={
                "action": "query",
                "format": "json",
                "formatversion": 2,
                "redirects": 1,
                "titles": source_id,
                "prop": "imageinfo",
                "iiprop": "url|mime|extmetadata",
            },
            headers=headers,
            timeout=20,
        )

        _raise_for_rate_limit(response)
        payload = response.json()

    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(
            "Could not verify the Wikimedia source metadata."
        ) from exc

    pages = payload.get("query", {}).get("pages", [])
    page = pages[0] if pages else {}
    infos = page.get("imageinfo") or []

    if page.get("missing") or not infos:
        raise ValueError(
            "Wikimedia could not find this source file. "
            "Return to Licensed Media and select the source again."
        )

    info = infos[0]
    mime = (info.get("mime") or "").lower()

    if not mime.startswith("video/"):
        raise ValueError("The selected source is not a video file.")

    # Step 2: Check license information and attribution.
    metadata = info.get("extmetadata") or {}

    license_name = _metadata_text(metadata, "LicenseShortName")
    license_url = _metadata_text(metadata, "LicenseUrl")
    creator = _metadata_text(metadata, "Artist")
    credit = _metadata_text(metadata, "Credit")

    if not _license_is_allowed(license_name, license_url):
        raise ValueError(
            "This file does not have a recognized reusable license. "
            "Choose another source and review its license."
        )

    # Step 3: Validate the download URL.
    download_url = info.get("url", "")
    parsed = urlparse(download_url)

    if (
        parsed.scheme != "https"
        or parsed.hostname != "upload.wikimedia.org"
    ):
        raise ValueError(
            "The source download URL is not permitted."
        )

    extension = Path(parsed.path).suffix.lower()

    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError(
            "The source has an unsupported video extension."
        )

    # Step 4: Prepare a local destination.
    media_root = Path(settings.MEDIA_ROOT).resolve()
    media_dir = media_root / "licensed_media"
    media_dir.mkdir(parents=True, exist_ok=True)

    safe_stem = re.sub(r"[^A-Za-z0-9_-]", "_", source_id)
    destination = media_dir / f"{safe_stem[:100]}{extension}"
    temporary_path = destination.with_suffix(
        destination.suffix + ".part"
    )

    # Step 5: Download once, respecting rate limits.
    try:
        with requests.get(
            download_url,
            headers=headers,
            stream=True,
            timeout=(20, 90),
        ) as download:

            _raise_for_rate_limit(download)

            content_type = download.headers.get(
                "Content-Type", ""
            ).lower()

            if content_type and not (
                content_type.startswith("video/")
                or content_type == "application/octet-stream"
            ):
                raise ValueError(
                    "The source did not return video content."
                )

            total = 0

            with temporary_path.open("wb") as output:
                for chunk in download.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if not chunk:
                        continue

                    total += len(chunk)

                    if total > MAX_DOWNLOAD_BYTES:
                        raise ValueError(
                            "The video exceeds the 500 MB limit."
                        )

                    output.write(chunk)

        if (
            not temporary_path.exists()
            or temporary_path.stat().st_size == 0
        ):
            raise RuntimeError(
                "The downloaded file is empty."
            )

        # Replace the destination only after a complete download.
        temporary_path.replace(destination)

    except requests.RequestException as exc:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(
            "The video download failed because of a network or "
            "server error. Wait before retrying."
        ) from exc

    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    # Step 6: Return source and attribution information.
    return {
        "source_id": source_id,
        "source_page": info.get("descriptionurl", ""),
        "local_path": str(destination),
        "relative_path": destination.relative_to(
            media_root
        ).as_posix(),
        "mime_type": mime,
        "license": license_name,
        "license_url": license_url,
        "creator": creator,
        "credit": credit,
    }
