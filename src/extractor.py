from src.extractors.utils import detect_pdf_type
from extractors.form import extract_form_outline
from extractors.flyer import extract_flyer_outline
from extractors.document import extract_document_outline

def extract_outline(doc):
    pdf_type = detect_pdf_type(doc)

if pdf_type == "form":
    title = extract_title_form(doc)
    outline = []  # no outline for forms

elif pdf_type == "structured_document":
    title = extract_title_generic(doc)
    outline = extract_outline_structured(doc)

elif pdf_type == "rfp":
    title = extract_title_generic(doc)
    outline = extract_outline_rfp(doc)

elif pdf_type == "poster":
    title = extract_title_generic(doc)
    outline = extract_outline_poster(doc)

elif pdf_type == "invitation":
    title = extract_title_invitation(doc)
    outline = extract_outline_invitation(doc)

else:
    title = extract_title_generic(doc)
    outline = extract_outline_structured(doc)

