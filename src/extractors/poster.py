# File: src/extractors/poster.py

import fitz  # PyMuPDF
from collections import defaultdict
from .utils import clean

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


# def extract_outline(doc):
#     title = extract_title(doc)
#     headings = []
#     seen = set()
#     font_sizes = defaultdict(int)
#     span_data = []

#     # Step 1: Collect all text spans
#     for page_num in range(len(doc)):
#         page = doc.load_page(page_num)
#         blocks = page.get_text("dict")["blocks"]

#         for block in blocks:
#             if "lines" not in block:
#                 continue
#             for line in block["lines"]:
#                 for span in line["spans"]:
#                     text = clean(span["text"])
#                     if not text or len(text.split()) > 8 or len(text) < 4:
#                         continue
#                     font_size = round(span["size"], 1)
#                     bbox = fitz.Rect(span["bbox"])
#                     font_sizes[font_size] += 1
#                     span_data.append({
#                         "text": text,
#                         "size": font_size,
#                         "page": page_num,
#                         "bbox": bbox
#                     })

#     # Step 2: Heading font sizes (top 3 largest fonts)
#     sorted_sizes = sorted(font_sizes.items(), key=lambda x: (-x[0], -x[1]))
#     heading_sizes = [size for size, _ in sorted_sizes[:3]]

#     # Step 3: For each span, check if it's a heading
#     for span in span_data:
#         text = span["text"]
#         size = span["size"]
#         page = span["page"]
#         bbox = span["bbox"]

#         if text == title or text in seen:
#             continue
#         seen.add(text)

#         if size not in heading_sizes:
#             continue

#         # Step 4: Determine if inside a box
#         inside_box = False
#         for drawing in doc.load_page(page).get_drawings():
#             if drawing["type"] == "rect":
#                 rect = fitz.Rect(drawing["rect"])
#                 # if rect.contains(bbox):
#                 if rect.intersects(bbox):
#                     inside_box = True
#                     break

#         level = "H2" if inside_box else "H1"

#         headings.append({
#             "level": level,
#             "text": text,
#             "page": page
#         })

#     return headings
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
                    if not text or len(text.split()) > 8 or len(text) < 4:
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

        # Use geometry-based H2 condition
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

