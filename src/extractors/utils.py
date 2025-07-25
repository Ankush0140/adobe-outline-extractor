# import re

# def clean(text):
#     return text.replace('\n', ' ').strip()

# def clean_text(text):
#     return text.replace("\n", " ").strip()

# def is_toc_line(text):
#     return bool(text.lower().strip().startswith("table of contents") or
#                 any(p in text.lower() for p in [".....", " 1.", " 2.", "toc", "page "]) or
#                 text.lower().strip().endswith(tuple(str(n) for n in range(1, 21))))

# def is_metadata_line(text):
#     return any(keyword in text.lower() for keyword in [
#         "version", "copyright", "page", "approved", "remarks", "date", "of 12"
#     ])

# def is_repeated_line(text, line_freq):
#     return line_freq[text] > 1

# def is_heading_like(text, font="", size=0):
#     text = text.strip()
#     words = text.split()

#     # Reject empty or super long lines
#     if not text or len(words) > 15:
#         return False

#     # Rule 1: Numbered heading
#     if re.match(r"^\d+(\.\d+)*\s+", text):
#         return True

#     # Rule 2: ALL CAPS and short
#     if text.isupper():
#         return True

#     # Rule 3: Title Case and short
#     if text.istitle() and len(words) <= 8:
#         return True

#     # Rule 4: Visual signal (font and size)
#     font_lower = font.lower()
#     if size >= 11 and any(w in font_lower for w in ["bold", "black", "semibold"]):
#         return True

#     return False
# src/utils/utils.py

import re

def clean(text):
    return text.replace('\n', ' ').strip()

def clean_text(text):
    return text.replace("\n", " ").strip()

def is_toc_line(text):
    return bool(text.lower().strip().startswith("table of contents") or
                any(p in text.lower() for p in [".....", " 1.", " 2.", "toc", "page "]) or
                text.lower().strip().endswith(tuple(str(n) for n in range(1, 21))))

def is_metadata_line(text):
    return any(keyword in text.lower() for keyword in [
        "version", "copyright", "page", "approved", "remarks", "date", "of 12"
    ])

def is_repeated_line(text, line_freq):
    return line_freq[text] > 1

def is_heading_like(text, font="", size=0):
    text = text.strip()
    words = text.split()

    if not text or len(words) > 15:
        return False

    if re.match(r"^\d+(\.\d+)*\s+", text):
        return True
    if text.isupper():
        return True
    if text.istitle() and len(words) <= 8:
        return True
    if size >= 11 and any(w in font.lower() for w in ["bold", "black", "semibold"]):
        return True

    return False
