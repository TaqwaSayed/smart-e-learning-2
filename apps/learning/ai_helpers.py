"""
Small, single-purpose Gemini helper for summarizing lesson content.
Kept separate from services.py (which owns the quiz-generation logic) so
each file has one clear job.

Design choice: never raises. If the API key is missing or the call fails
for any reason, returns None so the view can show a friendly message
instead of a broken page.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

CANDIDATE_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"]


def summarize_lesson_content(content: str, language: str = 'en'):
    """
    Returns a short bullet-point summary of `content`, or None if
    summarization isn't available (no API key) or the call fails.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key or not content or not content.strip():
        return None

    lang_instruction = "Write the summary in Arabic." if language == 'ar' else "Write the summary in English."
    prompt = (
        "Summarize the following lesson content for a student in 4 to 6 short "
        "bullet points, focusing only on the key concepts they need to remember. "
        f"{lang_instruction} Respond with just the bullet points, no preamble.\n\n"
        f"Lesson content:\n{content}"
    )

    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        for model_name in CANDIDATE_MODELS:
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                logger.warning("Lesson summarization failed on %s: %s", model_name, e)
                continue
    except Exception as e:
        logger.warning("Lesson summarization setup failed: %s", e)

    return None
