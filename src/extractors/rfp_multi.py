# src/extractors/rfp_multi.py
import re
from collections import Counter
from .utils import clean, is_heading_like  # keep using your utils' Latin logic where it works

# -----------------------
# Script detection
# -----------------------
def detect_script(text: str) -> str:
    for ch in text:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F:  # Devanagari (Hindi, etc.)
            return "devanagari"
        if 0x0C00 <= cp <= 0x0C7F:  # Telugu
            return "telugu"
    return "latin"

# A tolerant heading checker for non-Latin scripts
def is_heading_like_ml(text: str, font: str, size: float) -> bool:
    script = detect_script(text)
    if script == "latin":
        return is_heading_like(text, font, size)
    # For Hindi/Telugu: allow short-ish, non-paragraph lines and numbered headings
    if re.match(r"^\d+(\.\d+)*\s+", text.strip()):
        return True
    # Heuristic: short line (<= 15 words) that isn't obviously a body sentence
    return len(text.split()) <= 15 and not text.endswith(("।", ".", ":"))

# -----------------------
# Noise / date detection
# -----------------------
DATE_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"(?:\s+\d{1,2})?(?:,?\s+\d{4})?\b",
    re.IGNORECASE
)

def _is_date(text: str) -> bool:
    if DATE_PATTERN.search(text):
        return True
    if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text):
        return True
    if "timeline" in text.lower() and any(month in text.lower() for month in [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]):
        return True
    return False

def _is_noise(text: str) -> bool:
    text = text.strip()
    if not text:
        return True
    if _is_date(text):
        return True
    if len(text) < 3:
        return True
    words = text.split()
    if sum(1 for w in words if len(w) <= 2) > 2:
        return True
    if re.search(r'(.)\1{2,}', text.lower()):
        return True
    if re.match(r'^[^a-zA-Z\u0900-\u097F\u0C00-\u0C7F]+$', text):  # allow Devanagari/Telugu chars
        return True
    if len(words) > 20:
        return True
    return False

# -----------------------
# Title
# -----------------------
def extract_title(doc):
    if len(doc) == 0:
        return "Untitled RFP"

    page = doc.load_page(0)
    height = page.rect.height
    blocks = page.get_text("dict")["blocks"]

    candidates = []
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            y_top = line["bbox"][1]
            if y_top > height * 0.4:
                continue
            spans = line.get("spans", [])
            if not spans:
                continue
            text = clean(" ".join(span.get("text", "") for span in spans)).strip()
            if not text or _is_noise(text):  # keep same noise logic
                continue
            size = max(span.get("size", 0) for span in spans)
            candidates.append((y_top, size, text))

    if not candidates:
        return "Untitled RFP"

    candidates.sort(key=lambda x: x[0])
    max_size = max(s for _, s, _ in candidates)
    title_lines = [t for _, s, t in candidates if s >= max_size - 1]

    return " ".join(title_lines) if title_lines else "Untitled RFP"

# -----------------------
# Anchor & merge helpers
# -----------------------
def _find_title_anchor(doc, title: str):
    norm_title = re.sub(r'\s+', ' ', title or '').strip().lower()
    if not norm_title:
        return 0, doc.load_page(0).rect.height * 0.4

    for p in range(min(3, len(doc))):
        page = doc.load_page(p)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                line_text = clean(" ".join(span.get("text", "") for span in spans))
                if norm_title in line_text.lower():
                    return p, line["bbox"][3]
    return 0, doc.load_page(0).rect.height * 0.4

def _merge_adjacent_headings(lines, max_gap=30, max_size_diff=1.2):
    if not lines:
        return []
    lines.sort(key=lambda x: (x["page"], x["y"]))
    merged = []
    buf = [lines[0]]

    for cur in lines[1:]:
        prev = buf[-1]
        same_page = cur["page"] == prev["page"]
        close_y = abs(cur["y"] - prev["y"]) <= max_gap
        size_ratio = (max(cur["size"], prev["size"]) / max(min(cur["size"], prev["size"]), 0.1))
        close_size = size_ratio <= max_size_diff

        if same_page and close_y and close_size:
            buf.append(cur)
        else:
            merged.append({
                "text": " ".join(x["text"] for x in buf).strip(),
                "size": buf[0]["size"],
                "page": buf[0]["page"]
            })
            buf = [cur]

    merged.append({
        "text": " ".join(x["text"] for x in buf).strip(),
        "size": buf[0]["size"],
        "page": buf[0]["page"]
    })
    return merged

# -----------------------
# Outline
# -----------------------
def extract_outline(doc, title: str):
    start_page, start_y = _find_title_anchor(doc, title)
    raw = []

    for page_num in range(start_page, len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                if page_num == start_page and line["bbox"][1] <= start_y:
                    continue

                spans = line.get("spans", [])
                if not spans:
                    continue

                text = clean(" ".join(span.get("text", "") for span in spans)).strip()
                if not text:
                    continue

                if (title and title.lower() in text.lower()) or _is_noise(text):
                    continue

                size = max(span.get("size", 0.0) for span in spans)
                font = " ".join(span.get("font", "") for span in spans).lower()

                # Use multilingual-safe checker
                if is_heading_like_ml(text, font, size):
                    raw.append({
                        "text": text,
                        "size": round(size, 1),
                        "y": line["bbox"][1],
                        "page": page_num
                    })

    if not raw:
        return []

    merged = _merge_adjacent_headings(raw)

    seen = set()
    uniq = []
    for c in merged:
        key = (c["text"].lower(), c["page"])
        if key not in seen:
            seen.add(key)
            uniq.append(c)

    unique_sizes = sorted({c["size"] for c in uniq}, reverse=True)
    levels = ["H1", "H2", "H3", "H4"]
    size_to_level = {sz: levels[min(i, len(levels) - 1)] for i, sz in enumerate(unique_sizes)}

    outline = [
        {"level": size_to_level.get(c["size"], "H4"), "text": c["text"], "page": c["page"]}
        for c in uniq
    ]

    return outline
