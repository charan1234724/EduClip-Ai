import requests
from html import unescape


COMMONS_API_URL = "https://commons.wikimedia.org/w/api.php"

# These licenses may permit reuse, subject to their conditions.
REUSE_LICENSES = {
    "cc0",
    "cc by",
    "cc by-sa",
    "public domain",
}


def _plain_text(value):
    """Convert Commons metadata HTML to readable text."""
    if not value:
        return ""

    if isinstance(value, dict):
        value = value.get("value", "")

    # Commons metadata can contain HTML.
    import re
    value = re.sub(r"<[^>]+>", " ", str(value))
    return " ".join(unescape(value).split())


def _license_may_be_reusable(license_name):
    """Identify common reusable license labels; not a legal guarantee."""
    normalized = (license_name or "").strip().lower()
    normalized = normalized.replace(
        "creative commons attribution-share alike",
        "cc by-sa",
    )
    normalized = normalized.replace(
        "creative commons attribution",
        "cc by",
    )

    return any(
        normalized == license_name
        or normalized.startswith(license_name + " ")
        or normalized.startswith(license_name + "-")
        for license_name in REUSE_LICENSES
    )


def search_licensed_videos(query, limit=10):
    query = (query or "").strip()

    if not query:
        raise ValueError("Enter an educational topic to search.")

    limit = max(1, min(int(limit), 20))

    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"filetype:video {query}",
        "gsrnamespace": 6,
        "gsrlimit": 20,
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": 480,
    }

    headers = {
        "User-Agent": "EduClipAI/1.0 (educational media search)"
    }

    try:
        response = requests.get(
            COMMONS_API_URL,
            params=params,
            headers=headers,
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(
            "Wikimedia Commons search failed. Try again later."
        ) from exc

    pages = payload.get("query", {}).get("pages", {})
    results = []

    for page in pages.values():
        image_info = page.get("imageinfo") or []
        if not image_info:
            continue

        info = image_info[0]
        mime = (info.get("mime") or "").lower()

        # Do not return still images or audio-only files.
        if not mime.startswith("video/"):
            continue

        metadata = info.get("extmetadata") or {}

        license_name = _plain_text(
            metadata.get("LicenseShortName")
        )
        license_url = _plain_text(
            metadata.get("LicenseUrl")
        )
        creator = _plain_text(metadata.get("Artist"))
        credit = _plain_text(metadata.get("Credit"))

        results.append({
            "provider": "wikimedia_commons",
            "source_id": page.get("title", ""),
            "title": page.get("title", "").removeprefix("File:"),
            "source_page": info.get("descriptionurl", ""),
            "download_url": info.get("url", ""),
            "thumbnail": info.get("thumburl", ""),
            "mime_type": mime,
            "license": license_name,
            "license_url": license_url,
            "creator": creator,
            "credit": credit,
            "license_needs_review": not (
                license_name and license_url
                and _license_may_be_reusable(license_name)
            ),
        })

    
    query_words = {
        word.lower()
        for word in query.split()
        if len(word) > 2
    }

    def relevance_score(video):
        title_words = set(
            video["title"].lower().replace("_", " ").split()
        )
        credit_words = set(
            video["credit"].lower().replace("_", " ").split()
        )

        title_matches = len(query_words & title_words)
        credit_matches = len(query_words & credit_words)

        return (title_matches * 3) + credit_matches

    results.sort(key=relevance_score, reverse=True)

    return results

