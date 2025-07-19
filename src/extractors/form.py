# src/extractors/form.py
from utils import clean
from collections import defaultdict

def extract_title(doc):
    page = doc.load_page(0)
    text_lines = page.get_text().split("\n")

    for line in text_lines:
        line = clean(line)

        # Skip empty or metadata lines
        if not line or "microsoft word" in line.lower() or ".doc" in line.lower():
            continue

        # Title heuristic: meaningful length, no digits, not a label
        if len(line) > 10 and not any(char.isdigit() for char in line):
            if not any(ext in line.lower() for ext in ["form no", "s.no", "date", "name", "age", "designation"]):
                return line

    return "Untitled Form"

def extract_outline(doc):
    # Extract all text from the document
    field_keywords = {"s.no", "name", "age", "designation", "relationship", "date", "signature", "address"}

    all_lines = []
    for page_num in range(len(doc)):
        lines = doc.load_page(page_num).get_text().split("\n")
        for line in lines:
            cleaned = clean(line)
            if not cleaned or len(cleaned) < 3:
                continue
            all_lines.append(cleaned.lower())

    # Filter out title
    title = extract_title(doc).lower()
    non_title_lines = [line for line in all_lines if line != title]

    heading_candidates = []
    for line in non_title_lines:
        if len(line) > 20 and not any(line.startswith(f"{i}.") for i in range(1, 20)):
            if not any(keyword in line for keyword in field_keywords):
                heading_candidates.append(line)

    if heading_candidates:
        return [
        #     {
        #     "level": "H1",
        #     "text": extract_title(doc),
        #     "page": 0
        # }
        ]
    else:
        return []  # No meaningful sections → empty outline
