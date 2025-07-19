# Directory: src/detect_type.py

def detect_pdf_type(doc):
    text = ""
    for page_num in range(min(3, len(doc))):
        text += doc.load_page(page_num).get_text().lower()

    if (
    "ltc advance" in text or
    "application for grant" in text or
    "application form for" in text
    ):
        return "form"
    if "rfp" in text or "request for proposal" in text:
        return "rfp"
    if "mission statement" in text or "elective course" in text:
        return "poster"
    if "rsvp" in text or "you are invited" in text:
        return "invitation"
    if any(char.isdigit() and char == "." for char in text[:1000]):
        return "structured_document"

    return "structured_document"
