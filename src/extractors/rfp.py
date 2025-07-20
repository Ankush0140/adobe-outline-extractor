# Directory: src/extractors/rfp.py
from .utils import clean

def extract_title(doc):
    text = doc.load_page(0).get_text()
    lines = [clean(line) for line in text.split("\n") if line.strip()]
    for line in lines:
        if "proposal" in line.lower():
            return line
    return lines[0] if lines else "Untitled RFP"

def extract_outline(doc):
    spans_all = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict")['blocks']
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block['lines']:
                full_text = " ".join(span['text'] for span in line['spans']).strip()
                if not full_text or len(full_text) < 3:
                    continue
                size = max(span['size'] for span in line['spans'])
                spans_all.append({"text": clean(full_text), "size": round(size, 1), "page": page_num })

    sizes = sorted({s['size'] for s in spans_all}, reverse=True)
    size_to_level = {sz: f"H{min(i+1, 4)}" for i, sz in enumerate(sizes)}
    outline, seen = [], set()
    for s in spans_all:
        if s['text'] in seen or len(s['text']) < 4:
            continue
        seen.add(s['text'])
        outline.append({"level": size_to_level.get(s['size'], "H4"), "text": s['text'], "page": s['page']})
    return outline