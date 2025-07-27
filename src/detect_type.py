import re

def detect_pdf_type(doc):
    text = ""
    for page_num in range(min(3, len(doc))):  # sample first 3 pages
        try:
            text += doc.load_page(page_num).get_text().lower()
        except Exception:
            continue

    # --- form ---
    if (
        "ltc advance" in text or
        "application for grant" in text or
        "application form for" in text
    ):
        return "form"

    # --- rfp ---
    if "rfp" in text or "request for proposal" in text:
        return "rfp"

    # --- poster ---
    if "mission statement" in text or "elective course" in text:
        return "poster"

    # --- invitation ---
    if "rsvp" in text or "you are invited" in text:
        return "invitation"

    # --- structured document ---
    # Detect patterns like "1." or "2.1" (typical numbering)
    if re.search(r"\b\d+(\.\d+)*\b", text[:1000]):
        return "structured_document"

    return "structured_document"
