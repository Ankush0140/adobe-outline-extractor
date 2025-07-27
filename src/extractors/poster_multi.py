# File: src/extractors/poster_multi.py
import fitz  # PyMuPDF
from collections import defaultdict
from .utils import clean

# Lightweight script detector (no utils change required)
def detect_script(text: str) -> str:
    for ch in text:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F:  # Devanagari (Hindi, etc.)
            return "devanagari"
        if 0x0C00 <= cp <= 0x0C7F:  # Telugu
            return "telugu"
    return "latin"

def _within_word_limit(text: str) -> bool:
    words = text.split()
    script = detect_script(text)
    # Keep original <=8 for Latin; allow a bit more for Indic scripts
    if script == "latin":
        return len(words) <= 8
    return len(words) <= 12

def extract_title(doc):
    first_page = doc.load_page(0)
    blocks = first_page.get_text("dict")["blocks"]
    title = ""
    largest_size = 0

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = clean(span["text"])
                if not text or len(text) < 5:
                    continue
                if span["size"] > largest_size:
                    largest_size = span["size"]
                    title = text
    return title

def extract_outline(doc):
    title = extract_title(doc)
    headings = []
    seen = set()
    font_sizes = defaultdict(int)
    span_data = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = clean(span["text"])
                    if not text or len(text) < 4:
                        continue
                    if not _within_word_limit(text):
                        continue

                    font_size = round(span["size"], 1)
                    bbox = fitz.Rect(span["bbox"])
                    font_sizes[font_size] += 1
                    span_data.append({
                        "text": text,
                        "size": font_size,
                        "page": page_num,
                        "bbox": bbox
                    })

    # same heuristic: pick top 3 biggest/most frequent sizes as headings
    sorted_sizes = sorted(font_sizes.items(), key=lambda x: (-x[0], -x[1]))
    heading_sizes = [size for size, _ in sorted_sizes[:3]]

    for span in span_data:
        text = span["text"]
        size = span["size"]
        page = span["page"]
        bbox = span["bbox"]

        if text == title or text in seen:
            continue
        seen.add(text)

        if size not in heading_sizes:
            continue

        # Same geometry-based level rule
        if bbox.y0 > 460 and bbox.x0 > 100:
            level = "H2"
        else:
            level = "H1"

        headings.append({
            "level": level,
            "text": text,
            "page": page
        })

    return headings

