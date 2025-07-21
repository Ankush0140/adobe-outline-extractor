# src/extractors/rfp.py
from .utils import clean
from collections import Counter

def extract_title(doc):
    first_page = doc.load_page(0)
    blocks = first_page.get_text("dict")["blocks"]

    title_lines = []
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            line_text = " ".join(span["text"] for span in line["spans"]).strip()
            if "proposal" in line_text.lower() or "business plan" in line_text.lower():
                title_lines.append(line_text)

    # Combine multiple lines if needed
    full_title = " ".join(title_lines)
    return clean(full_title) if full_title else "Untitled RFP"

# def extract_outline(doc):
def extract_outline(doc, title):
    spans_all = []
    title = extract_title(doc)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                full_text = " ".join(span["text"] for span in line["spans"]).strip()
                if not full_text:
                    continue

                text = clean(full_text)  # ✅ Move this up here
                if (
                    len(text) < 8 or
                    len(text.split()) < 2 or
                    any(len(w) <= 2 for w in text.split()) or
                    len(text.split()) > 20 or
                    any(char in text for char in ['\u2019', 'f', ':']) and len(text) < 10 or
                    text == title or
                    text.lower().startswith("mailto:") or
                    text.lower().startswith("www.") or
                    text.strip().isdigit()
                ):
                    continue

                size = max(span["size"] for span in line["spans"])
                spans_all.append({
                    "text": text,
                    "size": round(size, 1),
                    "page": page_num
                })
                #  Filter
                if (
                    text == title or
                    text.lower().startswith("mailto:") or
                    text.lower().startswith("www.") or
                    text.strip().isdigit() or
                    len(text.split()) > 20  # paragraph text
                ):
                    continue

                spans_all.append({
                    "text": text,
                    "size": round(size, 1),
                    "page": page_num
                })

    # 🎯 Font-size → heading level
    size_counter = Counter(span["size"] for span in spans_all)
    sorted_sizes = [size for size, _ in size_counter.most_common()]
    size_to_level = {sz: f"H{min(i + 2, 4)}" for i, sz in enumerate(sorted_sizes)}  # H2 is largest

    outline, seen = [], set()
    for span in spans_all:
        if span["text"] in seen:
            continue
        seen.add(span["text"])
        level = size_to_level.get(span["size"], "H4")
        outline.append({
            "level": level,
            "text": span["text"],
            "page": span["page"]
        })

    return outline
