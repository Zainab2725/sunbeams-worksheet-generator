"""
pdf_extractor.py

Extracts text content from a syllabus PDF (using pdfplumber) so it can
be handed to the AI as grounding context ("here is what this grade/
term/subject actually covers, and here is an example of how content
is scaffolded across difficulty levels").

Results are cached to a local JSON file keyed by file path + modified
time, so the same PDF is never re-parsed unnecessarily.
"""

import os
import json
import hashlib
import pdfplumber

CACHE_FILE = "extract_cache.json"


def _cache_key(pdf_path: str) -> str:
    """Key on path + mtime so an edited PDF gets re-extracted automatically."""
    mtime = os.path.getmtime(pdf_path)
    raw = f"{pdf_path}:{mtime}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _load_cache(cache_file: str = CACHE_FILE) -> dict:
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict, cache_file: str = CACHE_FILE):
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def extract_text(pdf_path: str, max_pages: int = 15) -> str:
    """
    Extract text from a PDF, using a local cache to avoid re-parsing.
    max_pages caps how much of a large syllabus PDF we pull (keeps AI
    prompt context small and cheap).
    """
    cache = _load_cache()
    key = _cache_key(pdf_path)

    if key in cache:
        return cache[key]

    text_chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            if i >= max_pages:
                break
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_chunks.append(page_text)

    full_text = "\n\n".join(text_chunks)

    cache[key] = full_text
    _save_cache(cache)

    return full_text


def extract_summary(pdf_path: str, max_chars: int = 4000) -> str:
    """
    Return a trimmed version of the extracted text, safe to drop
    straight into an AI prompt without blowing up context/cost.
    """
    full_text = extract_text(pdf_path)
    if len(full_text) <= max_chars:
        return full_text
    return full_text[:max_chars] + "\n...[truncated]"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(extract_summary(sys.argv[1]))
    else:
        print("Usage: python pdf_extractor.py <path-to-pdf>")
