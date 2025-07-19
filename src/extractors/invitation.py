# Directory: src/extractors/invitation.py
from utils import clean

def extract_title(doc):
    return "RSVP: ----------------"

def extract_outline(doc):
    outline = []
    for page_num in range(len(doc)):
        text = doc.load_page(page_num).get_text()
        lines = [clean(line) for line in text.split("\n") if line.strip()]
        for line in lines:
            if "rsvp" in line.lower():
                level = "H1"
            elif "hope" in line.lower():
                level = "H2"
            elif "topjump" in line.lower() or line.lower().startswith("www"):
                level = "H3"
            else:
                level = "H4"
            outline.append({"level": level, "text": line, "page": page_num })
    return outline
