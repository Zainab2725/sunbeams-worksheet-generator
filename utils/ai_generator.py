"""
ai_generator.py

Builds the system + user prompt for the worksheet generator and calls
the Groq API (free tier, generous rate limits, OpenAI-compatible
chat-completions style) to produce a structured JSON worksheet:

{
  "worksheet_title": str,
  "instructions_urdu": str,
  "instructions_english": str,
  "questions": [str, ...],
  "answer_key": [str, ...]
}

Why Groq: it has a free API tier with a large daily request allowance
and fast inference, so it fits this project's "lightweight, free"
constraint better than a paid-only API. Get a free key at
https://console.groq.com/keys -- no credit card required at signup.

The prompt teaches the model the "scaffold" pattern seen in the
Sunbeams syllabus PDFs: the same topic is broken into 4 increasing
levels of difficulty (e.g. the Urdu word scaffold: single letter+vowel
-> two letters joined -> letters with i'raab/diacritics -> full word).
"""

import os
import json
import re
from groq import Groq

# openai/gpt-oss-20b is Groq's strongest general-purpose free-tier
# model as of writing and handles bilingual Urdu/English text well.
# If it's ever deprecated, swap in whatever Groq lists as current at
# https://console.groq.com/docs/models
MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are a bilingual (Urdu/English) worksheet writer for Sunbeams,
a network of non-formal primary schools in Pakistan. Your worksheets are used by
teachers running multi-grade, multi-level classrooms, so clarity and an accurate
difficulty level matter more than anything else.

You follow a 4-level scaffolding pattern seen throughout the Sunbeams syllabus
materials. For example, for the Urdu word "کھانا" the syllabus breaks it into:
  Level 1: a single letter with a short vowel sound (e.g. کھ)
  Level 2: two letters joined together (e.g. کھا)
  Level 3: letters with i'raab / diacritics shown (e.g. کھاں)
  Level 4: the full word written normally, without diacritics (e.g. کھانا)

Apply this same "simple building block -> full, real-world complexity" logic to
ANY subject or topic you are given (Math, Science, English, Islamiyat, Social
Studies), not just Urdu letters. Level 1 should isolate the smallest sub-skill;
Level 4 should be the full, real-world version of the skill/question.

You must ground your questions in the syllabus context provided to you -- use
its vocabulary, scope, and topic boundaries. Do not introduce concepts outside
that scope.

Always respond with STRICT JSON ONLY. No markdown, no code fences, no preamble,
no explanation outside the JSON object. The JSON must have exactly these keys:
"worksheet_title", "instructions_urdu", "instructions_english", "questions",
"answer_key". "questions" and "answer_key" must be arrays of strings of equal
length, in matching order.
"""

USER_PROMPT_TEMPLATE = """Grade band: {grade}
Term: {term}
Subject: {subject}
Topic requested by teacher: {topic}
Difficulty level (1-4, per the scaffold pattern described above): {difficulty}

Syllabus context extracted from the official Sunbeams {subject} syllabus PDF for
this grade/term (use this to ground vocabulary and scope -- it may be partial or
messy OCR text, use your judgement):

---
{syllabus_context}
---

Generate a worksheet with 8-10 questions at the requested difficulty level, for
the requested topic, following the 4-level scaffold logic. Include a short
bilingual instruction line for the student. Respond with the strict JSON object
only, as specified in your system instructions.
"""


def _get_client(api_key: str = None) -> Groq:
    key = api_key or os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError(
            "No Groq API key found. Get a free key at "
            "https://console.groq.com/keys, then set it as the GROQ_API_KEY "
            "env var or pass api_key explicitly."
        )
    return Groq(api_key=key)


def _clean_json_response(raw_text: str) -> dict:
    """Strip stray markdown fences etc, then parse JSON."""
    cleaned = re.sub(r"^```(json)?|```$", "", raw_text.strip(), flags=re.MULTILINE).strip()
    return json.loads(cleaned)


def generate_worksheet(
    grade: str,
    term: str,
    subject: str,
    topic: str,
    difficulty: int,
    syllabus_context: str,
    api_key: str = None,
) -> dict:
    """
    Calls Groq to generate a worksheet. Returns a dict matching the
    schema described in SYSTEM_PROMPT. Raises on API or JSON-parse
    failure -- callers (e.g. the Streamlit app) should catch and show
    a friendly error.
    """
    client = _get_client(api_key)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        grade=grade,
        term=term,
        subject=subject,
        topic=topic,
        difficulty=difficulty,
        syllabus_context=syllabus_context or "(no syllabus text extracted -- use general grade-appropriate scope)",
    )

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=2000,
        temperature=0.7,
        response_format={"type": "json_object"},  # Groq enforces valid JSON output
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw_text = response.choices[0].message.content

    try:
        worksheet = _clean_json_response(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI response was not valid JSON: {e}\nRaw response:\n{raw_text}")

    # Basic schema sanity check
    required_keys = {"worksheet_title", "instructions_urdu", "instructions_english", "questions", "answer_key"}
    missing = required_keys - worksheet.keys()
    if missing:
        raise ValueError(f"AI response missing keys: {missing}")

    return worksheet


if __name__ == "__main__":
    # Quick manual test (requires GROQ_API_KEY set in env)
    result = generate_worksheet(
        grade="PA",
        term="Endline",
        subject="Urdu",
        topic="کھانا",
        difficulty=2,
        syllabus_context="Sample syllabus text about basic Urdu letter joining...",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
