import re

def clean(text):
    return text.replace('\n', ' ').strip()

def clean_text(text):
    return text.replace("\n", " ").strip()

def is_toc_line(text):
    return bool(text.lower().strip().startswith("table of contents") or
                any(p in text.lower() for p in [".....", " 1.", " 2.", "toc", "page "]) or
                text.lower().strip().endswith(tuple(str(n) for n in range(1, 21))))

def is_metadata_line(text):
    return any(keyword in text.lower() for keyword in [
        "version", "copyright", "page", "approved", "remarks", "date", "of 12"
    ])

def is_repeated_line(text, line_freq):
    return line_freq[text] > 1

def is_heading_like(text, font="", size=0):
    text = text.strip()
    words = text.split()

    if not text or len(words) > 15:
        return False

    if re.match(r"^\d+(\.\d+)*\s+", text):
        return True
    if text.isupper():
        return True
    if text.istitle() and len(words) <= 8:
        return True
    if size >= 11 and any(w in font.lower() for w in ["bold", "black", "semibold"]):
        return True

    return False

# ---------------- NEW: detect any kind of date line ---------------- #

_MONTHS = r"January|February|March|April|May|June|July|August|September|October|November|December"
DATE_REGEXES = [
    # March 21, 2003 / March 2003
    re.compile(rf"\b(?:{_MONTHS})\s+\d{{1,2}},?\s+\d{{4}}\b", re.IGNORECASE),
    re.compile(rf"\b(?:{_MONTHS})\s+\d{{4}}\b", re.IGNORECASE),
    # 21 March 2003
    re.compile(rf"\b\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}\b", re.IGNORECASE),
    # 2003-03-21
    re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b"),
    # 21/03/2003 or 03/21/2003
    re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
    # FY 2023, Q1 2022, 2022/23, 2022-23
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
    # fall-back: if it contains a year and also “timeline” or a month name, treat as date-ish
    if _YEAR_RE.search(t) and (re.search(_MONTHS, t, re.IGNORECASE) or "timeline" in t.lower()):
        return True
    return False