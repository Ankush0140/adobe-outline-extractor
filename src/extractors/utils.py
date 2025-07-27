# File: src/extractors/utils.py
import re
import unicodedata

# ---------------- TEXT CLEANING ---------------- #
def clean(text):
    return text.replace('\n', ' ').strip()

def clean_text(text):
    return text.replace("\n", " ").strip()

# ---------------- TOC / METADATA DETECTION ---------------- #
def is_toc_line(text):
    t = text.lower().strip()
    # Keep your original conditions
    return bool(
        t.startswith("table of contents") or
        "toc" in t or
        "....." in t or
        t.endswith(tuple(str(n) for n in range(1, 21))) or
        re.search(r"\.{2,}\s*\d+$", t)  # dotted leaders with page number
    )

def is_metadata_line(text):
    return any(keyword in text.lower() for keyword in [
        "version", "copyright", "page", "approved", "remarks", "date", "of 12"
    ])

def is_repeated_line(text, line_freq):
    return line_freq[text] > 1

# ---------------- MULTILINGUAL SCRIPT DETECTION ---------------- #
DEVANAGARI = re.compile(r"[\u0900-\u097F]")  # Hindi
TELUGU     = re.compile(r"[\u0C00-\u0C7F]")  # Telugu

def detect_script(text: str) -> str:
    if DEVANAGARI.search(text):
        return "devanagari"
    if TELUGU.search(text):
        return "telugu"
    return "latin"  # fallback

def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text or "").strip()

# ---------------- HEADING DETECTION ---------------- #
def is_heading_like(text, font="", size=0):
    text = text.strip()
    words = text.split()

    if not text or len(words) > 15:
        return False

    script = detect_script(text)

    if script == "latin":
        # Keep your original logic
        if re.match(r"^\d+(\.\d+)*\s+", text):
            return True
        if text.isupper():
            return True
        if text.istitle() and len(words) <= 8:
            return True
        if size >= 11 and any(w in font.lower() for w in ["bold", "black", "semibold"]):
            return True
        return False

    if script in ("devanagari", "telugu"):
        return len(words) <= 10 and not text.endswith(("।", ".", ":"))

    return False

# ---------------- DATE DETECTION ---------------- #
_MONTHS = r"January|February|March|April|May|June|July|August|September|October|November|December"
DATE_REGEXES = [
    re.compile(rf"\b(?:{_MONTHS})\s+\d{{1,2}},?\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(rf"\b(?:{_MONTHS})\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(rf"\b\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b"),
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    re.compile(r"\bFY\s*(19|20)\d{2}\b", re.IGNORECASE),
    re.compile(r"\bQ[1-4]\s*(19|20)\d{2}\b", re.IGNORECASE),
    re.compile(r"\b(19|20)\d{2}\s*[-/]\s*(19|20)\d{2}\b"),
]
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")

def is_date_line(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    for rx in DATE_REGEXES:
        if rx.search(t):
            return True
    if _YEAR_RE.search(t) and (re.search(_MONTHS, t, re.IGNORECASE) or "timeline" in t.lower()):
        return True
    return False
