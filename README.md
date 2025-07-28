# Adobe Outline Extractor 📝

This project is a multilingual PDF parser designed for the Adobe India Hackathon 2025. It extracts structured outlines and titles from diverse types of PDFs — including forms, invitations, posters, RFPs, and structured documents. It supports both English and regional languages like Hindi and Telugu.

---

## 📌 PDF Types Supported

The solution handles **5 PDF types**, each with **language-specific extractors**:

| PDF Type     | English Extractor       | Multilingual Extractor (Hindi/Telugu) |
|--------------|-------------------------|----------------------------------------|
| Form         | `extractors.form`       | `extractors.form_multilingual`        |
| Invitation   | `extractors.invitation` | `extractors.invitation_multilingual`  |
| Poster       | `extractors.poster`     | `extractors.poster_multilingual`      |
| RFP          | `extractors.rfp`        | `extractors.rfp_multilingual`         |
| Structured   | `extractors.structured` | `extractors.structured_multilingual`  |

---

## 🧠 Approach

### 1. **PDF Categorization**
- Each PDF is first classified into one of the five types (e.g., `form`, `poster`, etc.)
- A language detection mechanism (currently based on script heuristics) determines whether to use the English or multilingual version of the extractor.

### 2. **Title Extraction**
- The `extract_title()` function heuristically identifies the most likely title from the first page.
  - Skips metadata, form labels, and short/noisy lines.
  - Filters out common field labels (e.g., `Name`, `Age`, `पता`, etc.)

### 3. **Outline Extraction**
- The `extract_outline()` function scans each page and:
  - Skips repeated headers/footers, table of contents, dates, and paragraph-style lines.
  - Identifies only hierarchical, heading-style text elements using heuristics like font size, position, and keywords.

### 4. **Multilingual Support**
- Field labels and noise filters are extended for **Devanagari (Hindi)** and **Telugu** script characters.
- Matching is script-aware and avoids false positives in non-English documents.

---

## ⚙️ Libraries & Tools Used

| Library       | Purpose                                  |
|---------------|------------------------------------------|
| `PyMuPDF`     | PDF text extraction and layout analysis  |
| `re`          | Regex-based line filtering               |
| `unicodedata` | Unicode script normalization             |
| `Docker`      | Containerized environment setup          |
| `Python 3.9`  | Base runtime                             |

---

## 🚀 How to Build and Run

### ✅ Expected Execution
When executed, the app will:
- Load all PDFs from `/app/input`
- Write structured JSON output to `/app/output`

### 🔧 Build Docker Image

```bash
docker build -t pdf-processor .

### 🔧 Run Docker Image

```bash
docker run --rm -v "%cd%/input:/app/input:ro" -v "%cd%/output:/app/output" --network none pdf-processor


🗂️ Directory Structure
.
├── input/                 # Folder containing test PDFs
├── output/                # Output folder for JSON results
├── src/
│   ├── main.py            # Entry point
│   ├── utils.py           # Shared utilities
│   ├── detector.py        # PDF type and language detection logic
│   └── extractors/
│       ├── form.py
│       ├── form_multilingual.py
│       ├── invitation.py
│       ├── invitation_multilingual.py
│       ├── poster.py
│       ├── poster_multilingual.py
│       ├── rfp.py
│       ├── rfp_multilingual.py
│       ├── structured.py
│       └── structured_multilingual.py
├── requirements.txt
├── Dockerfile
└── README.md
