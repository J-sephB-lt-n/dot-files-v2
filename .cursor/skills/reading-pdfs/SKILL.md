---
name: reading-pdfs
description: Extract text, Table of Contents, page images and metadata from a PDF, and search over the PDF's text content using Full-Text Search. Use when the user asks you to read or answer questions using a PDF document.
---

# Reading PDFs

Follow the steps described in [Steps for a Single PDF](#steps-for-a-single-pdf) separately for each PDF you are working with.

## Steps for a Single PDF

Suggested Approach:

1. Make a temporary folder called `temp-<your-pdf-name>/` (hereafter referred to as _your temp pdf folder_) to locally store all extracted content and metadata from the PDF you are working with.
2. Read the [Embedded Table of Contents](#embedded-table-of-contents) in the PDF (if there is one) to understand the structure of the PDF.
3. [Extract PDF Metadata](#extract-pdf-metadata) for the PDF.
4. Based on the extracted PDF metadata, decide if the PDF is primarily a text PDF (copyable text), primarily an image PDF or truly a mixture of both. If you are still uncertain, compare a handful of random [extracted page images](#extract-page-images) (spanning the PDF) to the extracted text of those pages (you can use `pymupdf` for quick and dirty text extraction at this stage).
5. The method you use to explore/navigate the PDF content depends on the type of PDF:
   - If the PDF is primarily a text PDF, navigate the PDF using the approach described in [Text Extraction and FTS-indexing](#text-extraction-and-fts-indexing). You _may_ also use [Extract Page Images](#extract-page-images) if the PDF has complex layout, tables or important visual elements, although you should try to avoid this if possible because the page-image-based approach is highly inefficient compared to the text-based approach (page images cannot be searched, images take up a LOT of memory and space, and viewing page images will quickly exhaust your context window).
   - If the PDF content is primarily image-based, then navigate the PDF using the approach described in [Extract Page Images](#extract-page-images). Be careful because page images use a lot of memory and space and viewing page images will quickly exhaust your context window.
   - If the PDF is mixed, use the text-based approach as your primary method, but fall back to page images for specific pages that have low text content but high image content.
6. If the PDF has no [Embedded Table of Contents](#embedded-table-of-contents), then try to find one within the PDF text content itself. If you have access to FTS search, use this to look for the Table of Contents (or an index section) in the PDF text. Otherwise, you will have to explore the early pages in the PDF directly.
7. Use an [iterative search strategy](#iterative-search-strategy) to find the answer we are looking for in the PDF.
8. After we are finished with the PDF, then please delete the temporary files in \_your temp pdf folder (definitely don't delete the original PDF file, though). If you are not clear whether we are finished investigating the PDF yet or not, ask me.

### Iterative Search Strategy

1. Identify candidate relevant pages using the Table of Contents and (if available) FTS search.
2. Read the candidate pages
3. Repeat until confident or no new results. If FTS search is available, try reformulating the search query.

### Extract PDF Metadata

Run the following python code to extract metadata about the PDF:

```python
import json
import pymupdf

with pymupdf.open("path/to/your/file.pdf") as pdf:
  page_metrics: list[dict] = []
  for page in pdf:
    page_text: str = page.get_text().strip()
    page_metrics.append(
      {
        "n_chars": len(page_text),
        "n_words": len(page_text.split()),
        "n_images": len(page.get_image_info()),
      }
    )

  n_pages: int = len(page_metrics)
  n_pages_with_no_text: int = sum(page["n_chars"]==0 for page in page_metrics)
  n_words: int = sum(page["n_words"] for page in page_metrics)
  n_chars: int = sum(page["n_chars"] for page in page_metrics)
  n_images: int = sum(page["n_images"] for page in page_metrics)
  print("<pdf-metadata-summary>")
  print(f"- PDF contains an embedded table of contents: {bool(pdf.get_toc())}")
  print(f"- Total number of pages: {n_pages:,}")
  print(f"- Total number of words (whole document): {n_words:,}")
  print(f"- Total number characters (whole document): {n_chars:,}")
  print(f"- Total number of images (whole document): {n_images:,}")
  print(f"- Average (mean) number of words per page: {n_words/n_pages:,.2f}")
  print(f"- Average (mean) number of images per page: {n_images/n_pages:,.2f}")
  if n_images > 0:
    print(f"- Average (mean) number of words per image: {n_words/n_images:,.2f}")
  print(f"- Pages with no text: {n_pages_with_no_text}/{n_pages} ({100*n_pages_with_no_text/n_pages:.2f}%)")
  print(f"PDF metadata extracted by pymupdf: {json.dumps(pdf.metadata, default=str, indent=4)}")
  print("</pdf-metadata-summary>")
```

### Text Extraction and FTS-indexing

Run the following python code to extract the text from each page of your PDF file, write this extracted text to a local sqlite database, and index these text pages for Full-Text Search (FTS).

```python
import sqlite3
import subprocess
from contextlib import contextmanager
from pathlib import Path

result = subprocess.run(
    ["pdftotext", "-enc", "UTF-8", "-eol", "unix", "-layout", "path/to/your/input.pdf", "-"],
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

pages: list[str] = result.stdout.split("\f")
if pages and pages[-1].strip() == "":
    pages.pop()

@contextmanager
def open_db(path: Path):
    conn = sqlite3.connect(path)
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        conn.close()


with open_db(Path("{{your_temp_pdf_folder}}/pages.sqlite")) as conn:
    conn.execute("""
    CREATE VIRTUAL TABLE pages USING fts5(
        page_num  UNINDEXED
      , page_text
      , tokenize = 'porter unicode61' -- use tokenize = 'unicode61' if not english PDF
    )
    """)
    conn.executemany(
        "INSERT INTO pages(page_num, page_text) VALUES (?, ?)",
        enumerate(pages, start=1),
    )
```

If your system does not have poppler `pdftotext` installed, then you can use `pymupdf` as a replacement (although visual layout of extracted text is objectively inferior using `pymupdf` compared to poppler `pdftotext`) like this:

```python
import pymupdf

with pymupdf.open("path/to/your/file.pdf") as pdf:
  pages: list[str] = [page.get_text(sort=True) for page in pdf]
```

After running the text extraction and FTS indexing, you can read a specific full page of text like this:

```bash
sqlite3 -noheader -batch {{your_temp_pdf_folder}}/pages.sqlite \
  "SELECT page_text FROM pages WHERE page_num = 69;"
```

You can use Full-Text Search (sqlite fts5) to find relevant parts of the document like this:

```bash
sqlite3 -noheader {{your_temp_pdf_folder}}/pages.sqlite <<EOF
.mode list
.separator ''

SELECT    '<page-' || page_num || '>' || char(10) ||
          snippet(pages, 1, '[', ']', '…', 12) || char(10) ||
          '</page-' || page_num || '>' || char(10)
FROM      pages
WHERE     pages MATCH '(report OR summary) AND budget* AND "cash flow" NOT draft'
ORDER BY  rank   -- this is BM25 rank
LIMIT 20
;
EOF
```

**IMPORTANT**: The sqlite fts5 **snippet()** function shows you only the _first_ match on the page, so you should still read the full page text of the matching page (the first match might be irrelevant to the question you are trying to answer, but this does not mean that the answer to your question isn't somewhere else on the same page - outside of the **snippet()** you are seeing).

Because FTS is keyword-based (not semantic), you should include a lot of synonyms, abbreviations, and multiple forms of the same word in your search queries e.g. "anonymisation OR anonymization OR anonymise OR anonymize OR anonymising OR anonymizing OR anonymised OR anonymized OR identification OR de-identification OR identify OR identified OR identifiable OR pseudonymisation OR pseudonymization OR pseudonymise OR pseudonymize OR mask OR masking OR obfuscate OR obfuscation".

### Embedded Table of Contents

If there is an embedded Table of Contents ("bookmarks") within the PDF (in my experience very few PDFs actually have one), you can extract it using `pymupdf`:

```python
import pymupdf

with pymupdf.open("path/to/your/input.pdf") as pdf:
  toc: list[tuple[int, str, int]] = pdf.get_toc() # list[heading_level, title, page_num]

if toc:
  print("[HEADING_LEVEL, TITLE, PAGE_NUMBER]")
  for toc_item in toc:
    print(toc_item)
else:
  print("No Table of Contents found")
```

`get_toc()` returns an empty list if the PDF has no bookmarks.

## Extract Page Images

You can use [pymupdf](https://pymupdf.readthedocs.io/en/latest/) to extract each PDF page as a page image. Save these images to `{{your-temp-pdf-folder}}/images/*.png` using the following python code:

**IMPORTANT**: only export the page images you intend to read. Exporting images is slow and takes up a lot of space.

```python
from collections.abc import Sequence
from pathlib import Path

import pymupdf
from PIL import Image, ImageFilter, ImageOps

MAX_IMAGE_SIDE: int = 1024  # scaled so neither image height nor width exceeds this
PAGE_IMAGES_DIR: Path = Path("{{your-temp-pdf-folder}}/page_images")
PAGE_NUMS_TO_EXPORT: Sequence[int] | None = None
PAGE_IMAGES_DIR.mkdir(exist_ok=True)

with pymupdf.open("/path/to/your/input.pdf") as pdf:
    if PAGE_NUMS_TO_EXPORT is None:
        PAGE_NUMS_TO_EXPORT = range(1, len(pdf)+1)
    for page_num in PAGE_NUMS_TO_EXPORT:
        page: pymupdf.Page = pdf[page_num - 1]
        page_pixmap: pymupdf.Pixmap = page.get_pixmap(
            dpi=96,
            colorspace=pymupdf.csGRAY,  # use pymupdf.csRGB if colour is useful (e.g. graphs)
            alpha=False,
        )
        match page_pixmap.n:
            case 1:
                img_mode = "L"
            case 2:
                img_mode = "LA"
            case 3:
                img_mode = "RGB"
            case 4:
                img_mode = "RGBA"
            case _:
                raise ValueError(f"Unsupported pixmap channel count: {page_pixmap.n}")
        page_img: Image.Image = Image.frombytes(
            mode=img_mode,
            size=(page_pixmap.width, page_pixmap.height),
            data=page_pixmap.samples,
        )
        max_side_len: int = max(page_img.width, page_img.height)
        if max_side_len > MAX_IMAGE_SIDE:
            scale: float = MAX_IMAGE_SIDE / max_side_len
            page_img = page_img.resize(
                size=(
                    int(page_img.width * scale),
                    int(page_img.height * scale),
                ),
                resample=Image.Resampling.LANCZOS,
            )
        page_img = page_img.filter(ImageFilter.SHARPEN)
        page_img = ImageOps.autocontrast(page_img, cutoff=0.5)
        page_img.save(
            PAGE_IMAGES_DIR / f"page-{page_num}.png",
            format="PNG",
            compress_level=9,
            optimize=True,
        )
```

## Dependencies

```bash
# System
sudo apt install poppler-utils

# Python
uv run --with pymupdf --with Pillow script.py
```

SQLite ships with Python's standard library - no install needed.

## Requirements

When answering:

- Always cite page numbers
- Prefer multiple sources if available
