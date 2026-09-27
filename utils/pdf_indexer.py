"""
pdf_indexer.py

Walks the dataset-sunbeams folder structure:

    dataset-sunbeams/
        PA/
            Endline/*.pdf
            Mid Line/*.pdf
        PB/
            Endline/*.pdf
            Mid Line/*.pdf
        PC/
            First term/*.pdf
            Second Term/*.pdf
            Third Term/*.pdf

...and builds a clean, normalized index:

    {
        "PA": {
            "Endline": {"Urdu": "path/to/file.pdf", "English": "...", ...},
            "Mid Term": {...}
        },
        "PC": {
            "First Term": {...},
            "Second Term": {...},
            "Third Term": {...}
        }
    }

Filenames in the real dataset are messy ("PA nazra endline.pdf",
"PC social.studeis end term syllabas.pdf", "P. B. islamiat midterm
syllabus..pdf"), so both TERM folder names and SUBJECT names inside
filenames are normalized using fuzzy matching (rapidfuzz) rather than
exact string matching.
"""

import os
import json
from rapidfuzz import process, fuzz

# Canonical labels we want to standardize everything to
CANONICAL_TERMS = ["First Term", "Mid Term", "Second Term", "Third Term", "Endline"]

CANONICAL_SUBJECTS = [
    "Urdu",
    "English",
    "Math",
    "Science",
    "Islamiyat",
    "Social Studies",
    "Nazra",
]

# Extra keyword hints to help fuzzy matching land on the right subject
# (helps with things like "S.st", "islamiat", "social.studeis")
SUBJECT_ALIASES = {
    "Urdu": ["urdu"],
    "English": ["english", "eng"],
    "Math": ["math", "maths"],
    "Science": ["science", "sci"],
    "Islamiyat": ["islamiat", "islamiyat", "islamyat"],
    "Social Studies": ["s.st", "sst", "social", "studeis", "studies"],
    "Nazra": ["nazra", "nazara"],
}

TERM_ALIASES = {
    "First Term": ["first term", "1st term"],
    "Mid Term": ["mid term", "midterm", "mid line", "midline"],
    "Second Term": ["second term", "2nd term"],
    "Third Term": ["third term", "3rd term"],
    "Endline": ["endline", "end term", "end line"],
}


def _best_alias_match(text: str, alias_map: dict, score_cutoff: int = 60):
    """Return the canonical key from alias_map whose alias list best
    matches `text`, or None if nothing scores above score_cutoff."""
    text_low = text.lower()
    best_key, best_score = None, 0
    for canonical, aliases in alias_map.items():
        for alias in aliases:
            score = fuzz.partial_ratio(alias, text_low)
            if score > best_score:
                best_score = score
                best_key = canonical
    if best_score >= score_cutoff:
        return best_key
    return None


def normalize_term(folder_name: str) -> str:
    """Map a messy term folder name to a canonical term label."""
    match = _best_alias_match(folder_name, TERM_ALIASES)
    return match or folder_name.strip()


def normalize_subject(file_name: str) -> str:
    """Map a messy filename to a canonical subject label."""
    match = _best_alias_match(file_name, SUBJECT_ALIASES)
    return match or os.path.splitext(file_name)[0].strip()


def build_index(dataset_root: str) -> dict:
    """
    Walk dataset_root (the dataset-sunbeams folder) and build the
    grade -> term -> subject -> filepath index.
    """
    index = {}

    if not os.path.isdir(dataset_root):
        raise FileNotFoundError(f"Dataset root not found: {dataset_root}")

    for grade in sorted(os.listdir(dataset_root)):
        grade_path = os.path.join(dataset_root, grade)
        if not os.path.isdir(grade_path):
            continue

        index.setdefault(grade, {})

        for term_folder in sorted(os.listdir(grade_path)):
            term_path = os.path.join(grade_path, term_folder)
            if not os.path.isdir(term_path):
                continue

            canonical_term = normalize_term(term_folder)
            index[grade].setdefault(canonical_term, {})

            for fname in sorted(os.listdir(term_path)):
                if not fname.lower().endswith(".pdf"):
                    continue
                subject = normalize_subject(fname)
                full_path = os.path.join(term_path, fname)
                index[grade][canonical_term][subject] = full_path

    return index


def save_index(index: dict, out_path: str = "index_cache.json"):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def load_index(in_path: str = "index_cache.json") -> dict:
    with open(in_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_index(dataset_root: str, cache_path: str = "index_cache.json", force_rebuild: bool = False) -> dict:
    """Convenience wrapper: load from cache if present, else build + cache it."""
    if not force_rebuild and os.path.exists(cache_path):
        try:
            return load_index(cache_path)
        except Exception:
            pass  # fall through to rebuild if cache is corrupt

    index = build_index(dataset_root)
    save_index(index, cache_path)
    return index


if __name__ == "__main__":
    # Quick manual test: point this at your dataset-sunbeams folder
    root = os.environ.get("DATASET_ROOT", "dataset-sunbeams")
    idx = get_index(root, force_rebuild=True)
    print(json.dumps(idx, ensure_ascii=False, indent=2))
