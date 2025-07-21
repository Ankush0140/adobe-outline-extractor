# Refined version of structured.py (with bug fixes)
from .utils import clean, clean_text, is_toc_line, is_metadata_line, is_repeated_line, is_heading_like
import fitz  # PyMuPDF
import re
from collections import defaultdict, Counter

def extract_title(doc):
    first_page = doc.load_page(0)
    blocks = first_page.get_text("dict")["blocks"]

    max_y_limit = first_page.rect.height * 0.75
    skip_keywords = {"version", "copyright", "page", "www", "revision", "table of contents"}

    title_lines = []
    seen = set()

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
                if title_lines:
                    return " ".join(title_lines)
                continue

            size = round(spans[0].get("size", 0), 1)
            if last_size and abs(size - last_size) > 3.0:
                return " ".join(title_lines)

            if any(c.isalpha() for c in line_text) and len(line_text) > 5:
                title_lines.append(line_text)
                last_size = size

    return " ".join(title_lines) if title_lines else "Untitled Document"

def detect_page_role(page_lines):
    texts = [line["text"].strip().lower() for line in page_lines if line["text"].strip()]

    if len(texts) <= 5 and any(len(t.split()) >= 4 for t in texts):
        if all(not any(k in t for k in ["copyright", "version", "page"]) for t in texts):
            return "title_page"

    if any("table of contents" in t for t in texts):
        return "toc_page"
    if sum(bool(re.search(r"\.{2,}\s*\d+$", t)) for t in texts) >= 3:
        return "toc_page"
    if any("revision history" in t for t in texts) and any(re.search(r"remarks|version|date", t) for t in texts):
        return "revision_history_page"
    if any("acknowledgement" in t for t in texts):
        return "acknowledgements_page"
    for t in texts:
        normalized = re.sub(r"\s+", " ", t.strip().lower())
        if re.match(r"^\d+(\.\d+)*[\.\s]+references", normalized) or normalized == "references":
            return "references_page"
    if any(re.match(r"^\d+(\.\d+)*[\s.]+", t) for t in texts):
        return "heading_page"
    if any(re.match(r"^chapter \d+:", t) for t in texts):
        return "heading_page"

    return "unknown"

def should_skip_role(role):
    return role in {"unknown"}

# def extract_from_heading_page(lines, page_num):
#     result = []
#     seen = set()
#     size_counter = Counter(line["size"] for line in lines)
#     dominant_size = size_counter.most_common(1)[0][0] if size_counter else 0

#     skip_starts = ('professionals', 'junior', 'experienced', 'new', 'testers')

#     for line in lines:
#         text = line["text"]
#         if text in seen:
#             continue
#         seen.add(text)

#         if is_metadata_line(text) or is_repeated_line(text, line_freq) or is_toc_line(text):
#             continue
#         # Skip Chapter headings like "Chapter 1:"
#         if re.match(r"^Chapter \d+:", text, re.IGNORECASE):
#             continue
#         # Skip simple numbered bullets like "1. some text"
#         if re.match(r"^\d+\.\s+[a-z]", text):
#             continue

#         number_match = re.match(r"^(\d+(?:\.\d+)*)([\s.]+)(.*)", text)
#         if number_match:
#             trailing_text = number_match.group(3).strip()
#             if trailing_text:
#                 word_count = len(trailing_text.split())
#                 dot_count = number_match.group(1).count('.')
                
#                 # Skip if starting with known bullet content
#                 if trailing_text.lower().split()[0] in skip_starts:
#                     continue

#                 if word_count >= 2 and line["size"] >= dominant_size:
#                     level = f"H{dot_count + 1}"
#                     result.append({"level": level, "text": text.strip() + " ", "page": page_num})
#                     continue

#         if re.match(r"^Chapter \d+:", text, re.IGNORECASE):
#             result.append({"level": "H1", "text": text.strip() + " ", "page": page_num})
#             continue

#         if is_heading_like(text, font=line["font"], size=line["size"]):
#             if line["size"] >= dominant_size and len(text.split()) > 2:
#                 result.append({"level": "H1", "text": text.strip() + " ", "page": page_num})

#     return result
def extract_from_heading_page(lines, page_num):
    result = []
    seen = set()
    size_counter = Counter(line["size"] for line in lines)
    dominant_size = size_counter.most_common(1)[0][0] if size_counter else 0

    skip_starts = ('professionals', 'junior', 'experienced', 'new', 'testers')

    for line in lines:
        text = line["text"]
        if text in seen:
            continue
        seen.add(text)

        if is_metadata_line(text) or is_repeated_line(text, line_freq) or is_toc_line(text):
            continue

        if re.match(r"^Chapter \d+:", text, re.IGNORECASE):
            continue

        number_match = re.match(r"^(\d+(?:\.\d+)*)([\s.]+)(.*)", text)
        if number_match:
            trailing_text = number_match.group(3).strip()
            number_part = number_match.group(1)
            dot_count = number_part.count('.')

            if trailing_text:
                word_count = len(trailing_text.split())
                first_word = trailing_text.lower().split()[0]

                # Skip if it's a single number followed by a dot (e.g., 1.) and the first word is in skip_starts
                if re.match(r'^\d+\.[\s]', text) and first_word in skip_starts:
                    continue

                if word_count >= 1 and line["size"] >= dominant_size:
                    level = f"H{dot_count + 1}"
                    result.append({"level": level, "text": text.strip(), "page": page_num})
                    continue

        if is_heading_like(text, font=line["font"], size=line["size"]):
            if line["size"] >= dominant_size and len(text.split()) > 2:
                result.append({"level": "H1", "text": text.strip(), "page": page_num})

    return result

def extract_from_revision_page(lines, page_num):
    for line in lines:
        if re.search(r"revision history", line["text"], re.IGNORECASE):
            return [{"level": "H1", "text": line["text"], "page": page_num}]
    return []

def extract_from_acknowledgements_page(lines, page_num):
    for line in lines:
        if "acknowledgement" in line["text"].lower():
            return [{"level": "H1", "text": line["text"], "page": page_num}]
    return []

def extract_from_toc_page(lines, page_num):
    for line in lines:
        if "table of contents" in line["text"].lower():
            return [{"level": "H1", "text": line["text"], "page": page_num}]
    return []

def extract_from_references_page(lines, page_num):
    result = []
    for line in lines:
        text = line["text"]
        normalized = re.sub(r"\s+", " ", text.strip().lower())

        if re.match(r"^\d+(\.\d+)*[\.\s]+references", normalized) or normalized == "references":
            result.append({"level": "H1", "text": line["text"], "page": page_num})
        elif re.match(r"^\d+(\.\d+)+\s+", normalized):
            result.append({"level": "H2", "text": line["text"], "page": page_num})
    return result

def extract_outline(doc):
    global line_freq
    title = extract_title(doc)
    line_freq = Counter()
    all_lines = []
    page_lines_map = defaultdict(list)
    page_roles = {}
    global_font_counter = Counter()

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")["blocks"]
        line_map = defaultdict(list)

        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                y = round(line["bbox"][1], 1)
                for span in line["spans"]:
                    if span["text"].strip():
                        line_map[y].append(span)

        for y in sorted(line_map):
            spans = line_map[y]
            spans.sort(key=lambda s: s["bbox"][0])
            merged_text = " ".join(clean_text(s["text"]) for s in spans).strip()
            if not merged_text:
                continue
            line_data = {
                "text": merged_text,
                "page": page_num,
                "y": y,
                "font": spans[0].get("font", ""),
                "size": spans[0].get("size", 0),
            }
            global_font_counter[line_data["size"]] += 1
            line_freq[merged_text] += 1
            all_lines.append(line_data)
            page_lines_map[page_num].append(line_data)

        page_roles[page_num] = detect_page_role(page_lines_map[page_num])

    outline = []
    collecting = False

    for line in all_lines:
        if not collecting and title.lower() in line["text"].lower():
            collecting = True
            break

    for page_num, lines in page_lines_map.items():
        role = page_roles[page_num]
        if should_skip_role(role):
            continue

        if role == "heading_page":
            outline += extract_from_heading_page(lines, page_num)
        elif role == "revision_history_page":
            outline += extract_from_revision_page(lines, page_num)
        elif role == "acknowledgements_page":
            outline += extract_from_acknowledgements_page(lines, page_num)
        elif role == "toc_page":
            outline += extract_from_toc_page(lines, page_num)
        elif role == "references_page":
            outline += extract_from_references_page(lines, page_num)

    return outline
