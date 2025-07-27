# Directory: src/main.py
import time
import json
import fitz
import inspect
from pathlib import Path
from detect_type import detect_pdf_type
from extractors import (
    form, form_multilang,
    rfp, rfp_multi,
    invitation, invitation_multi,
    poster, poster_multi,
    structured, structured_multi
)

# ---- Constraints ----
MAX_PAGES = 50
MAX_SECONDS_PER_PDF = 10.0

# default extractors
type_to_extractor = {
    "form": form,
    "rfp": rfp,
    "poster": poster,
    "invitation": invitation,
    "structured_document": structured
}

# multilingual extractors
type_to_extractor_multi = {
    "form": form_multilang,
    "rfp": rfp_multi,
    "poster": poster_multi,
    "invitation": invitation_multi,
    "structured_document": structured_multi
}

def has_devanagari_or_telugu(text: str) -> bool:
    for ch in text:
        oc = ord(ch)
        if 0x0900 <= oc <= 0x097F or 0x0C00 <= oc <= 0x0C7F:  # Devanagari / Telugu
            return True
    return False

def process_pdfs():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in input_dir.glob("*.pdf"):
        start_t = time.perf_counter()
        try:
            doc = fitz.open(pdf_path)

            # Enforce page limit
            if len(doc) > MAX_PAGES:
                print(f"Skipping {pdf_path.name}: page count {len(doc)} exceeds limit ({MAX_PAGES}).")
                doc.close()
                continue

            pdf_type = detect_pdf_type(doc)

            # pick default extractor
            extractor = type_to_extractor.get(pdf_type, structured)

            # multilingual switch (cheap – only first page sampled)
            sample_text = ""
            if len(doc) > 0:
                try:
                    sample_text = doc.load_page(0).get_text()
                except Exception:
                    sample_text = ""

            if has_devanagari_or_telugu(sample_text):
                extractor = type_to_extractor_multi.get(pdf_type, structured_multi)

            # Title
            title = extractor.extract_title(doc)

            # Outline (with/without title arg)
            outline_func = extractor.extract_outline
            if len(inspect.signature(outline_func).parameters) == 2:
                outline = outline_func(doc, title)
            else:
                outline = outline_func(doc)

            elapsed = time.perf_counter() - start_t
            if elapsed > MAX_SECONDS_PER_PDF:
                print(f"Aborting {pdf_path.name}: exceeded time limit ({elapsed:.2f}s > {MAX_SECONDS_PER_PDF}s).")
                doc.close()
                continue

            output_data = {"title": title, "outline": outline}
            with open(output_dir / f"{pdf_path.stem}.json", "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            print(f"Processed {pdf_path.name} as {pdf_type} "
                  f"({'multi' if extractor in type_to_extractor_multi.values() else 'default'}) "
                  f"in {elapsed:.2f}s")

            doc.close()

        except Exception as e:
            print(f"Failed to process {pdf_path.name}: {e}")

if __name__ == "__main__":
    print("Starting PDF extraction...")
    process_pdfs()
    print("All PDFs processed.")
