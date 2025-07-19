import re

def clean(text):
    return " ".join(text.replace("\u00a0", " ").strip().split())

def clean_text(text):
    return " ".join(text.strip().split())

def is_meaningful(text):
    """
    Determines if a line is meaningful:
    - Should contain mostly alphabetic content
    - Should not be a version/page/copyright line
    - Should not be decorative (e.g., dots or dashes)
    - Should have minimum length
    """
    text = text.strip()
    if len(text) < 4:
        return False
    if re.fullmatch(r"[. \-•·_]{3,}", text):
        return False  # decorative line
    if any(x in text.lower() for x in ["version", "copyright", "page"]):
        return False
    alpha_ratio = sum(c.isalpha() for c in text) / max(len(text), 1)
    return alpha_ratio > 0.5  # mostly letters

def is_probably_toc_line(text):
    return (
        re.match(r"^\d+(\.\d+)*\s", text) or
        re.search(r"\s\d{1,3}$", text) or
        ("." in text and len(set(text.strip())) <= 3) or
        len(text.split()) <= 4
    )

def is_metadata(text):
    return any(k in text.lower() for k in ["version", "copyright", "page", "may", "june", "july", "2014"])
