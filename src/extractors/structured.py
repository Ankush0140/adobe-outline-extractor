# File: src/extractors/structured.py
from utils import clean, is_meaningful, is_metadata, is_probably_toc_line
import fitz
import re
from collections import defaultdict, Counter
from ml_fallback import is_heading  # optional fallback


def extract_title(doc):
    first_page = doc.load_page(0)
    blocks = first_page.get_text("dict")["blocks"]

    max_y_limit = first_page.rect.height * 0.75  # Top 75%
    skip_keywords = {"version", "copyright", "page", "www", "revision", "table of contents"}

    title_lines = []
    seen = set()

    last_font = None
    last_size = None

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            y = line["bbox"][1]
            if y > max_y_limit:
                continue

            spans = line["spans"]
            if not spans:
                continue

            line_text = clean(" ".join(span["text"] for span in spans))
            if not line_text or line_text in seen:
                continue
            seen.add(line_text)

            lowered = line_text.lower()
            if any(k in lowered for k in skip_keywords):
                # Stop if metadata appears after collecting title lines
                if title_lines:
                    return " ".join(title_lines)
                continue

            # Extract font name and size from first span
            font = spans[0].get("font", "")
            size = round(spans[0].get("size", 0), 1)

            # Stop collecting if font/size suddenly changes
            if last_font and last_size:
                if font != last_font or abs(size - last_size) > 1.0:
                    return " ".join(title_lines)

            if any(c.isalpha() for c in line_text) and len(line_text) > 5:
                title_lines.append(line_text)
                last_font = font
                last_size = size

    return " ".join(title_lines) if title_lines else "Untitled Document"

def extract_outline(doc):
    all_lines = []
    line_freq = Counter()

    for page_num in range(len(doc)):
        blocks = doc.load_page(page_num).get_text("dict")['blocks']
        line_map = defaultdict(list)
        for block in blocks:
            if 'lines' not in block:
                continue
            for line in block['lines']:
                y = round(line['bbox'][1], 1)
                for span in line['spans']:
                    if span['text'].strip():
                        line_map[y].append(span)

        for y in sorted(line_map):
            spans = line_map[y]
            spans.sort(key=lambda s: s['bbox'][0])
            merged_text = " ".join(clean(span['text']) for span in spans).strip()
            if not merged_text:
                continue
            line_freq[merged_text] += 1
            all_lines.append({
                "text": merged_text,
                "page": page_num,
                "y": y
            })

    # Detect title
    title = extract_title(doc)
    print(f"[DEBUG] Extracted title: {title}")

    outline = []
    seen = set()
    start_collecting = False

    for line in all_lines:
        text = line['text']
        page = line['page']

        # Start collecting after title appears
        if not start_collecting:
            title_words = set(title.lower().split())
            line_words = set(text.lower().split())
            common = title_words & line_words
            if len(common) >= max(1, int(0.5 * len(title_words))):  # At least 50% words in common
                start_collecting = True
                print(f"[DEBUG] Title match found (fuzzy): '{text}' — starting collection")
                continue

        if text in seen:
            print(f"[SKIP] Duplicate line: {text}")
            continue
        seen.add(text)

        if not is_meaningful(text):
            print(f"[SKIP] Not meaningful: {text}")
            continue

        if is_metadata(text):
            print(f"[SKIP] Metadata line: {text}")
            continue

        if is_probably_toc_line(text):
            print(f"[SKIP] TOC line: {text}")
            continue

        if line_freq[text] > 1:
            print(f"[SKIP] Repeated line (header/footer?): {text}")
            continue

        print(f"[ADD] Heading: {text}")
        outline.append({
            "level": "H2",
            "text": text,
            "page": page
        })

    print(f"[DEBUG] Final outline length: {len(outline)}")
    return outline