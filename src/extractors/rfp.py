import fitz  # PyMuPDF
import re
from collections import Counter, defaultdict
from .utils import is_heading_like, clean

DATE_PATTERN = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
    re.IGNORECASE
)

def extract_first_page_lines(doc):
    if len(doc) == 0:
        return []
    text = doc.load_page(0).get_text()
    return [clean(line) for line in text.split("\n") if line.strip()]

def extract_title(doc) -> str:
    """
    Extract a highly accurate, de-noised title block from the first page.
    This version avoids hardcoding and handles noisy/repeated span artifacts.
    """
    if len(doc) == 0:
        return "No Title Found"

    page = doc.load_page(0)
    height = page.rect.height
    blocks = page.get_text("dict")["blocks"]

    title_lines = []

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            y_coord = line["bbox"][1]
            if y_coord > height * 0.4:
                continue  # bottom content, probably body

            text = clean(" ".join(span.get("text", "") for span in line["spans"])).strip()
            if not text or len(text.split()) < 2:
                continue

            size = max(span["size"] for span in line["spans"])
            font = " ".join(span["font"] for span in line["spans"]).lower()

            if is_heading_like(text, font, size) or size >= 11.0:
                title_lines.append((y_coord, text, size))

    if not title_lines:
        return "No Title Found"

    # Group lines with similar font sizes (within 1pt) and top positions
    title_lines.sort(key=lambda x: x[0])  # sort by vertical position

    final_tokens = []
    seen_words = set()
    previous_size = None
    for _, line_text, size in title_lines:
        if previous_size and abs(previous_size - size) > 1:
            break  # font size dropped → likely end of title
        previous_size = size
        for word in line_text.strip().split():
            lw = word.lower()
            if len(lw) > 2 and lw not in seen_words:
                final_tokens.append(word)
                seen_words.add(lw)

    title = " ".join(final_tokens)
    return title[:200] if title else "No Title Found"

def extract_rfp_identifier(lines):
    pattern = re.compile(r"\b(RFP|RFQ|RFI)[\s:\-#]*[A-Z0-9_\-/]+", re.IGNORECASE)
    for line in lines:
        match = pattern.search(line)
        if match:
            return clean(match.group())
    return ''

def extract_date(lines):
    for line in lines:
        match = DATE_PATTERN.search(line)
        if match:
            return match.group()
    return ''

def extract_organization(lines):
    # No hardcoded organization names; use generic "organization-like" word triggers only if necessary
    for line in lines:
        if re.search(r"(library|institute|department|city|association)", line, re.IGNORECASE):
            return line
    return ''

def extract_purpose(lines):
    for line in lines:
        if line.lower().strip().startswith("the purpose"):
            return line.strip()
    return ''

def extract_features(doc):
    lines = extract_first_page_lines(doc)
    return {
        "title": extract_title(doc),
        "organization": extract_organization(lines),
        "rfp_identifier": extract_rfp_identifier(lines),
        "date": extract_date(lines),
        "purpose": extract_purpose(lines)
    }

def extract_outline(doc, title=None):
    spans_all = []
    line_freq = defaultdict(int)

    # Phase 1: Collect all candidate heading-like lines
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                text = clean(" ".join(span.get("text", "") for span in spans)).strip()
                if not text or len(text.split()) <= 1 or len(text.split()) > 25:
                    continue

                line_freq[text.lower()] += 1

                max_size = max(span["size"] for span in spans)
                font = " ".join(span["font"] for span in spans).lower()

                if is_heading_like(text, font, max_size):
                    spans_all.append({
                        "text": text,
                        "size": round(max_size, 1),
                        "page": page_num
                    })

    # Phase 2: Filter out repeated/junky lines by occurrence threshold (e.g., headers/footers)
    unique_spans = []
    seen = set()
    for span in spans_all:
        t = span["text"].lower()
        if span["text"] not in seen and line_freq[t] <= 2 and (not title or title.lower() not in t):
            seen.add(span["text"])
            unique_spans.append(span)
    if not unique_spans:
        return []

    font_counts = Counter(s['size'] for s in unique_spans)
    sorted_sizes = sorted(font_counts.items(), key=lambda item: -item[1])
    font_to_level = {}
    for i, (size, _) in enumerate(sorted_sizes):
        font_to_level[size] = "H1" if i == 0 else ("H2" if i == 1 else ("H3" if i == 2 else "H4"))

    outline = [
        {
            "level": font_to_level.get(span["size"], "H4"),
            "text": span["text"],
            "page": span["page"]
        }
        for span in unique_spans
    ]
    return outline
