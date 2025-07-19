# Directory: src/main.py
import fitz
import json
from pathlib import Path
from detect_type import detect_pdf_type

from extractors import form, rfp, invitation, poster, structured

type_to_extractor = {
    "form": form,
    "rfp": rfp,
    "poster": poster,
    "invitation": invitation,
    "structured_document": structured
}

def process_pdfs():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in input_dir.glob("*.pdf"):
        try:
            doc = fitz.open(pdf_path)
            pdf_type = detect_pdf_type(doc)
            extractor = type_to_extractor.get(pdf_type, structured)
            title = extractor.extract_title(doc)
            outline = extractor.extract_outline(doc)
            output_data = {"title": title, "outline": outline}
            with open(output_dir / f"{pdf_path.stem}.json", "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2)
            print(f"Processed {pdf_path.name} as {pdf_type}")
        except Exception as e:
            print(f"Failed to process {pdf_path.name}: {e}")

if __name__ == "__main__":
    print("Starting PDF extraction...")
    process_pdfs()
    print("All PDFs processed.")
