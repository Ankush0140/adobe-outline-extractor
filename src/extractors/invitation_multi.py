# src/extractors/invitation_multi.py
from .utils import clean

# --- Multi-language keywords for headings ---
HOPE_KEYWORDS = [
    "hope",          # English
    "आशा",          # Hindi
    "భావిస్తున్నాము"   # Telugu
]

def extract_title(doc):
    """
    Same logic as invitation.py but kept separate for multi-language version.
    """
    first_page = doc.load_page(0)
    blocks = first_page.get_text("dict")["blocks"]
    page_height = first_page.rect.height
    page_width = first_page.rect.width

    candidate_lines = []

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            spans = line.get("spans", [])
            if not spans:
                continue

            line_text = " ".join(span.get("text", "") for span in spans).strip()
            if not line_text:
                continue

            font_size = spans[0].get("size", 0)
            x0, x1 = line["bbox"][0], line["bbox"][2]
            y0 = line["bbox"][1]

            # Only consider lines in top 35% of page
            if y0 > page_height * 0.35:
                continue

            center_offset = abs((x0 + x1) / 2 - page_width / 2)
            is_centered = center_offset < page_width * 0.2

            candidate_lines.append({
                "text": line_text,
                "font_size": font_size,
                "y_pos": y0,
                "is_centered": is_centered
            })

    sorted_lines = sorted(candidate_lines, key=lambda l: l["y_pos"])
    title_lines = []
    for line in sorted_lines:
        if line["is_centered"] and line["font_size"] >= 10:
            title_lines.append(line["text"])
        if len(title_lines) == 2:
            break

    return " | ".join(title_lines) if title_lines else "Untitled Invitation"


def extract_outline(doc):
    """
    Multi-language outline extractor.
    Searches for lines containing 'hope' or its Hindi/Telugu equivalents.
    """
    outline = []

    for page_num in range(len(doc)):
        text = doc.load_page(page_num).get_text()
        lines = [clean(line) for line in text.split("\n") if line.strip()]

        for line in lines:
            l = line.lower()
            if any(k.lower() in l for k in HOPE_KEYWORDS):
                outline.append({
                    "level": "H1",
                    "text": line,
                    "page": page_num
                })
                # Uncomment this if you want to stop at the first match
                # return outline

    return outline
