

import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Locate the EduClip-Ai project root.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

# Load the root .env file.
load_dotenv(dotenv_path=ENV_FILE, override=True)


OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_ai_response(prompt, system_prompt=None):
    """
    Send a prompt to OpenRouter and return the AI-generated text.

    Raises RuntimeError with a useful message if the request fails.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "openrouter/free")

    if not api_key:
        raise RuntimeError(
            "OpenRouter API key is missing. Check the project root .env file."
        )

    if not prompt or not prompt.strip():
        raise ValueError("The prompt cannot be empty.")

    messages = []

    if system_prompt:
        messages.append(
            {
                "role": "system",
                "content": system_prompt,
            }
        )

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    payload = {
        "model": model,
        "messages": messages,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "EduClip AI",
    }

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=90,
        )
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not connect to OpenRouter: {exc}"
        ) from exc

    if not response.ok:
        # Do not include the API key in error messages.
        raise RuntimeError(
            f"OpenRouter returned HTTP {response.status_code}: "
            f"{response.text[:1000]}"
        )

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "OpenRouter returned an unexpected response format."
        ) from exc

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("OpenRouter returned an empty AI response.")

    return content.strip()


import json


def generate_trending_topics():
    """
    Generate exactly 100 structured educational topic suggestions.
    Trend scores are estimates, not verified live measurements.
    """
    system_prompt = """
You are an educational content researcher for YouTube Shorts
and TikTok. Return only valid JSON, with no Markdown fences.
Never invent live view counts, search volumes, or trend data.
Trend scores are estimates, not verified measurements.
"""

    prompt = """
Generate exactly 100 unique educational video topics with
strong potential to attract interest on YouTube Shorts and TikTok.

Prioritize specific, curiosity-driven topics related to:
- Artificial intelligence and useful AI tools
- Programming and software development
- Cybersecurity and online safety
- Gadgets and emerging technology
- Space and astronomy
- Science and experiments
- Practical digital skills
- Psychology and learning
- Robotics and engineering
- Technology developments and recent discoveries

Requirements:
1. Every topic must be suitable for a 30-90 second educational video.
2. Avoid duplicates, generic filler, misinformation, and clickbait.
3. Use a mix of Beginner, Intermediate, and Advanced difficulty.
4. Provide 3-6 useful search keywords for each topic.
5. Assign a relative estimated trend_score from 1 to 100.
6. Set trend_status to "unverified" because live trend evidence
   has not been checked by this generation request.
7. Do not claim that a topic is currently trending as a verified fact.

Return one JSON array containing exactly 100 objects.
Each object must contain these fields:
{
  "title": "Specific topic title",
  "category": "Subject category",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "difficulty": "Beginner",
  "trend_score": 75,
  "trend_status": "unverified"
}
"""

    response_text = generate_ai_response(
        prompt=prompt,
        system_prompt=system_prompt,
    )

    # Remove Markdown code fences if the model adds them.
    cleaned_text = response_text.strip()

    if cleaned_text.startswith("```"):
        lines = cleaned_text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned_text = "\n".join(lines).strip()

    try:
        topics = json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
        f"OpenRouter returned invalid JSON at line {exc.lineno}, "
        f"column {exc.colno}: {exc.msg}. "
        f"Response preview: {cleaned_text[:500]}"
    ) from exc

    if not isinstance(topics, list) or len(topics) != 100:
        raise RuntimeError(
            "The AI response must contain exactly 100 topics. "
            "Please try again."
        )

    required_fields = {
        "title",
        "category",
        "keywords",
        "difficulty",
        "trend_score",
        "trend_status",
    }
    allowed_difficulties = {
        "Beginner",
        "Intermediate",
        "Advanced",
    }
    seen_titles = set()

    for index, topic in enumerate(topics, start=1):
        if not isinstance(topic, dict):
            raise RuntimeError(f"Topic {index} is not a JSON object.")

        if not required_fields.issubset(topic.keys()):
            raise RuntimeError(f"Topic {index} is missing required fields.")

        title = topic["title"]
        keywords = topic["keywords"]
        score = topic["trend_score"]

        if not isinstance(title, str) or not title.strip():
            raise RuntimeError(f"Topic {index} has an invalid title.")

        normalized_title = title.strip().casefold()
        if normalized_title in seen_titles:
            raise RuntimeError(f"Duplicate topic title found: {title}")
        seen_titles.add(normalized_title)

        if not isinstance(topic["category"], str) or not topic["category"].strip():
            raise RuntimeError(f"Topic {index} has an invalid category.")

        if not isinstance(keywords, list) or not 3 <= len(keywords) <= 6:
            raise RuntimeError(
                f"Topic {index} must contain 3-6 keywords."
            )

        if topic["difficulty"] not in allowed_difficulties:
            raise RuntimeError(f"Topic {index} has an invalid difficulty.")

        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not 1 <= score <= 100
        ):
            raise RuntimeError(f"Topic {index} has an invalid trend score.")

        if topic["trend_status"] != "unverified":
            raise RuntimeError(
                f"Topic {index} must use trend_status='unverified'."
            )

    return topics

