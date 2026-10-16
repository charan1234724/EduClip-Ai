
import re
from urllib.parse import quote

import requests


ARCHIVE_SEARCH_URL = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA_URL = "https://archive.org/metadata/"
USER_AGENT = "EduClipAI/1.0 (educational media discovery)"

VIDEO_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".ogv",
    ".mov",
    ".m4v",
}

MAX_RESULTS = 10
MAX_METADATA_CHECKS = 10


def _clean_text(value):
    """Convert metadata values into clean strings."""
    if isinstance(value, list):
        value = ", ".join(str(item) for item in value)

    if value is None:
        return ""

    return re.sub(r"<[^>]*>", "", str(value)).strip()


def _license_is_reusable(license_url):
    """
    Recognize common Creative Commons and public-domain license URLs.

    This is a preliminary filter only. Item-specific terms must
    still be reviewed before a file is reused.
    """
    url = (license_url or "").strip().lower().rstrip("/")

    if not url.startswith("https://"):
        return False

    allowed_patterns = (
        r"creativecommons\.org/publicdomain/zero/",
        r"creativecommons\.org/licenses/by/",
        r"creativecommons\.org/licenses/by-sa/",
        r"creativecommons\.org/publicdomain/mark/",
    )

    return any(
        re.search(pattern, url)
        for pattern in allowed_patterns
    )


def search_internet_archive_videos(query, limit=10):
    """
    Search Internet Archive movie items and return video files
    whose item metadata includes a recognized reuse license.

    Does not download media.
    """
    query = (query or "").strip()

    if not query:
        raise ValueError("Enter a topic to search.")

    if len(query) > 150:
        raise ValueError("Search topic must be 150 characters or fewer.")

    limit = max(1, min(int(limit), MAX_RESULTS))

    headers = {"User-Agent": USER_AGENT}

    # Escape special characters used by the search query syntax.
    # Keep the user's input safe for an Internet Archive search query.
    safe_query = re.sub(r'[^A-Za-z0-9 ]', ' ', query)
    safe_query = " ".join(safe_query.split())

    if not safe_query:
        raise ValueError(
            "Enter a topic containing letters or numbers."
        )

    search_expression = (
    f'mediatype:movies AND '
    f'(title:({safe_query}) OR '
    f'subject:({safe_query}) OR '
    f'description:({safe_query}))'
)   

    try:
        response = requests.get(
            ARCHIVE_SEARCH_URL,
            params={
                "q": search_expression,
                "fl[]": [
                    "identifier",
                    "title",
                    "creator",
                    "description",
                ],
                "rows": min(limit * 3, MAX_METADATA_CHECKS),
                "page": 1,
                "output": "json",
            },
            headers=headers,
            timeout=25,
        )
        response.raise_for_status()
        payload = response.json()

    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(
            "Could not search Internet Archive. Please try again later."
        ) from exc

    documents = (
        payload.get("response", {}).get("docs", [])
    )
    print(
    "Internet Archive raw search results:",
    len(documents)
)

    results = []

    for document in documents[:MAX_METADATA_CHECKS]:
        identifier = _clean_text(document.get("identifier"))

        if not identifier:
            continue

        # Validate the identifier before using it in a URL.
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", identifier):
            continue

        try:
            metadata_response = requests.get(
                f"{ARCHIVE_METADATA_URL}{quote(identifier, safe='')}",
                headers=headers,
                timeout=20,
            )
            metadata_response.raise_for_status()
            item_data = metadata_response.json()

        except (requests.RequestException, ValueError):
            continue

        metadata = item_data.get("metadata") or {}
        license_url = _clean_text(
            metadata.get("licenseurl")
            or metadata.get("license_url")
        )

        rights = _clean_text(metadata.get("rights"))
        license_name = _clean_text(metadata.get("license"))

        print("Archive item:", identifier)
        print("Title:", metadata.get("title", ""))
        print("License URL:", license_url)
        print("License name:", license_name)
        print("Rights:", rights)
        print(
    "Other rights-related fields:",
    {
        key: value
        for key, value in metadata.items()
        if any(
            word in key.lower()
            for word in ("license", "rights", "usage")
        )
    },
)
        print("Archive item:", identifier)
        print("Title:", metadata.get("title", ""))
        print("License URL:", license_url)
        print("License accepted:", _license_is_reusable(license_url))
        print("Files listed:", len(item_data.get("files") or []))

        if not _license_is_reusable(license_url):
            continue

        files = item_data.get("files") or []

        video_files = []

        for archive_file in files:
            filename = _clean_text(archive_file.get("name"))
            extension = ""

            if "." in filename:
                extension = "." + filename.rsplit(".", 1)[-1].lower()

            if (
                extension in VIDEO_EXTENSIONS
                and not archive_file.get("private")
                and not archive_file.get("source") == "derivative"
            ):
                video_files.append({
                    "filename": filename,
                    "size": archive_file.get("size"),
                    "format": _clean_text(archive_file.get("format")),
                    "download_url": (
                        "https://archive.org/download/"
                        f"{quote(identifier, safe='')}/"
                        f"{quote(filename, safe='')}"
                    ),
                })

        if not video_files:
            continue

        title = _clean_text(metadata.get("title")) or identifier
        creator = _clean_text(metadata.get("creator"))
        description = _clean_text(metadata.get("description"))

        results.append({
            "provider": "internet_archive",
            "source_id": identifier,
            "title": title,
            "creator": creator,
            "description": description[:1000],
            "source_page": f"https://archive.org/details/{identifier}",
            "license": license_url,
            "license_url": license_url,
            "license_needs_review": True,
            "video_files": video_files,
        })

        if len(results) >= limit:
            break

    return results
