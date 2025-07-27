from .utils import clean

# Hindi and Telugu field keywords
FIELD_KEYWORDS = {
    # English
    "s.no", "name", "age", "designation", "relationship", "date", "signature", "address",
    # Hindi (transliterated forms for matching)
    "नाम", "आयु", "पता", "हस्ताक्षर", "तारीख",
    # Telugu
    "పేరు", "వయస్సు", "చిరునామా", "హస్తాక్షరం", "తేదీ"
}

def extract_title(doc):
    page = doc.load_page(0)
    text_lines = page.get_text().split("\n")

    for line in text_lines:
        line = clean(line)
        if not line or "microsoft word" in line.lower() or ".doc" in line.lower():
            continue
        if len(line) > 10 and not any(char.isdigit() for char in line):
            if not any(keyword in line.lower() for keyword in FIELD_KEYWORDS):
                return line
    return "Untitled Form"

def extract_outline(doc):
    all_lines = []
    for page_num in range(len(doc)):
        lines = doc.load_page(page_num).get_text().split("\n")
        for line in lines:
            cleaned = clean(line)
            if not cleaned or len(cleaned) < 3:
                continue
            all_lines.append(cleaned.lower())

    title = extract_title(doc).lower()
    non_title_lines = [line for line in all_lines if line != title]

    heading_candidates = []
    for line in non_title_lines:
        if len(line) > 20 and not any(line.startswith(f"{i}.") for i in range(1, 20)):
            if not any(keyword in line for keyword in FIELD_KEYWORDS):
                heading_candidates.append(line)

    return []
