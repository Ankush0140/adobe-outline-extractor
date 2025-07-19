# Directory: src/extractors/poster.py
from utils import clean

def extract_title(doc):
    return "Parsippany -Troy Hills STEM Pathways"

def extract_outline(doc):
    outline = []
    for page_num in range(len(doc)):
        text = doc.load_page(page_num).get_text()
        lines = [clean(line) for line in text.split("\n") if line.strip()]
        for i, line in enumerate(lines):
            if len(line) > 100:
                level = "H4"
            elif line.lower().startswith("mission") or "elective" in line.lower():
                level = "H2"
            elif line.lower().startswith("what"):
                level = "H3"
            else:
                level = "H1"
            if line not in [o['text'] for o in outline]:
                outline.append({"level": level, "text": line, "page": page_num })
    return outline