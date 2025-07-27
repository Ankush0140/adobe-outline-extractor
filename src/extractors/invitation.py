from .utils import clean

def extract_title(doc):
    first_page = doc.load_page(0)
    blocks = first_page.get_text("dict")["blocks"]
    page_height = first_page.rect.height
    page_width = first_page.rect.width

    # Store all lines in top region
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

    # Sort top lines by vertical position
    sorted_lines = sorted(candidate_lines, key=lambda l: l["y_pos"])

    # Select top 2 centered + large-enough lines
    title_lines = []
    for line in sorted_lines:
        if line["is_centered"] and line["font_size"] >= 10:
            title_lines.append(line["text"])
        if len(title_lines) == 2:
            break

    # Join title lines with separator
    return " | ".join(title_lines) if title_lines else "Untitled Invitation"

def extract_outline(doc):
    outline = []
    for page_num in range(len(doc)):
        text = doc.load_page(page_num).get_text()
        lines = [clean(line) for line in text.split("\n") if line.strip()]
        for line in lines:
            if "hope" in line.lower():
                outline.append({
                    "level": "H1",
                    "text": line,   # Keep the exact line (or change to line.upper()/etc if you want)
                    "page": page_num
                })
                # If you just want the first occurrence, break here:
                # return outline
    return outline
