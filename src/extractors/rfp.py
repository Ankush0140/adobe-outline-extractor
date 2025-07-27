# src/extractors/rfp.py
import re
from collections import Counter
from .utils import clean, is_heading_like,  is_date_line


# ---- Noise detection ----
def is_noisy_line(text: str) -> bool:
    if not text or len(text.strip()) < 5:
        return True
    tokens = text.split()
    if len(tokens) < 2:
        return True
    # Too many short tokens (OCR noise like "r Pr", "quest f")
    short_tokens = sum(len(t) <= 2 for t in tokens)
    if short_tokens / len(tokens) > 0.4:
        return True
    # Repeated characters (like "Reeeequest")
    if re.search(r"(.)\1{2,}", text):
        return True
    return False

# ---- Extract Title ----
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
            if y_top > height * 0.4:  # Focus on top 40% of page
                continue
            spans = line.get("spans", [])
            if not spans:
                continue
            text = clean(" ".join(span.get("text", "") for span in spans)).strip()
            if not text or is_noisy_line(text):
                continue
            size = max(span.get("size", 0) for span in spans)
            candidates.append((y_top, size, text))

    if not candidates:
        return "Untitled RFP"

    # Sort by vertical position and keep large font lines
    candidates.sort(key=lambda x: x[0])
    max_size = max(s for _, s, _ in candidates)
    title_lines = [t for _, s, t in candidates if s >= max_size - 1]

    return " ".join(title_lines) if title_lines else "Untitled RFP"

# src/extractors/rfp.py
import re
from collections import Counter
from .utils import clean, is_heading_like  # keep your existing utils

DATE_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"(?:\s+\d{1,2})?(?:,?\s+\d{4})?\b",
    re.IGNORECASE
)

def _is_date(text: str) -> bool:
    # Match any month name with optional day and year (e.g., "March 2003" or "April 21, 2003")
    if DATE_PATTERN.search(text):
        return True
    # Match simple numeric dates like "21/03/2003" or "03-21-03"
    if re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text):
        return True
    # "Timeline: March 2003 – September 2003" → treat as date-like
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
    if re.match(r'^[^a-zA-Z]+$', text):
        return True
    if len(words) > 20:
        return True
    return False


def _find_title_anchor(doc, title: str):
    """
    Find the y-coordinate right after the title. We’ll ignore anything above this on that page.
    Fallback: 40% of the first page.
    """
    norm_title = re.sub(r'\s+', ' ', title or '').strip().lower()
    if not norm_title:
        return 0, doc.load_page(0).rect.height * 0.4

    for p in range(min(3, len(doc))):  # usually in the first pages
        page = doc.load_page(p)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                line_text = clean(" ".join(span.get("text", "") for span in spans))
                if norm_title in line_text.lower():
                    # return the bottom (bbox[3]) of the title line
                    return p, line["bbox"][3]

    return 0, doc.load_page(0).rect.height * 0.4

def _merge_adjacent_headings(lines, max_gap=30, max_size_diff=1.2):
    """
    Merge consecutive lines that belong to the same visual heading (same page, near vertically,
    and similar font size).
    """
    if not lines:
        return []

    # sort by (page, y)
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
                # skip anything before the title on the start page
                if page_num == start_page and line["bbox"][1] <= start_y:
                    continue

                spans = line.get("spans", [])
                if not spans:
                    continue

                text = clean(" ".join(span.get("text", "") for span in spans)).strip()
                if not text:
                    continue

                # kill title repeats, dates, noise
                if (title and title.lower() in text.lower()) or _is_noise(text):
                    continue

                size = max(span.get("size", 0.0) for span in spans)
                font = " ".join(span.get("font", "") for span in spans).lower()

                if is_heading_like(text, font, size):
                    raw.append({
                        "text": text,
                        "size": round(size, 1),
                        "y": line["bbox"][1],
                        "page": page_num
                    })

    if not raw:
        return []

    # merge broken headings split across lines
    merged = _merge_adjacent_headings(raw)

    # dedupe (keep first occurrence per page)
    seen = set()
    uniq = []
    for c in merged:
        key = (c["text"].lower(), c["page"])
        if key not in seen:
            seen.add(key)
            uniq.append(c)

    # sizes -> H1..H4 (largest font = H1)
    unique_sizes = sorted({c["size"] for c in uniq}, reverse=True)
    levels = ["H1", "H2", "H3", "H4"]
    size_to_level = {sz: levels[min(i, len(levels) - 1)] for i, sz in enumerate(unique_sizes)}

    outline = [
        {"level": size_to_level.get(c["size"], "H4"), "text": c["text"], "page": c["page"]}
        for c in uniq
    ]

    return outline
