---
name: reading-pdfs
description: Extract text, Table of Contents, page images and metadata from a PDF, and search over the PDF's text content using Full-Text Search. Use when the user asks you to read or answer questions using a PDF document.
---

# Reading PDFs

Follow the steps described in [Steps for a Single PDF](#steps-for-a-single-pdf) separately for each PDF you are working with.

## Steps for a Single PDF

First, make a temporary folder called `temp-<your-pdf-name/` (hereafter referred to as _your temp pdf folder_) to locally store all extracted content and metadata from the PDF you are working with. You must delete this temporary folder (and everything in it) after we have finished working with the PDF (but don't delete the original PDF file).

Most PDFs contain copyable text, in which case the step [Text Extraction and FTS-indexing](#text-extraction-and-fts-indexing) is applicable, although [PDF Page Images](#pdf-page-images) may still be helpful if the PDF has complex layout, tables or important visual elements.

For PDFs without copyable text (text in the PDF is contained within images), the text content of the PDF can only be viewed using [PDF Page Images](#pdf-page-images).

Both text and non-text PDFs can contain an [embedded Table of Contents](#embedded-table-of-contents).

### Text Extraction and FTS-indexing

Run the following python code to extract the text from each page of your PDF file, write this extracted text to a local sqlite database, and index these page texts for Full-Text Search (FTS).

```bash
import sqlite3
import subprocess
from contextlib import contextmanager
from pathlib import Path

result = subprocess.run(
    ["pdftotext", "-enc", "UTF-8", "-eol", "unix", "-layout", "input.pdf", "-"],
    check=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)

pages: list[str] = result.stdout.split("\f")

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


with open_db(Path("{{your_temp_pdf_folder}}/page.sqlite")) as conn:
    conn.execute("""
    CREATE VIRTUAL TABLE pages USING fts5(
        page_num  UNINDEXED
      , page_text
      , tokenize = 'porter unicode61' -- use just tokenize='unicode61' if not english
    )
    """)
    conn.executemany(
        "INSERT INTO pages(page_num, page_text) VALUES (?, ?)",
        enumerate(pages, start=1),
    )
```

If your system does not have poppler `pdftotext` installed, then you can use `pymupdf` as a replacement (although note that the visual layout is objectively inferior using `pymupdf`):

```python
import pymupdf

with pymupdf.open("path/to/your/file.pdf") as pdf:
  pages: list[str] = [page.get_text(sort=True) for page in pdf]
```

### Embedded Table of Contents

If there is an embedded Table of Contents ("bookmarks") within the PDF, you can extract it using `pymupdf` (although in my experience very few PDFs actually have this):

```bash
import pymupdf

with pymupdf.open("path/to/your/file.pdf") as pdf:
  toc: list[int, str, int] = pdf.get_toc()

print("[HEADING_LEVEL, TITLE, PAGE_NUMBER]")
for toc_item in toc:
  print(toc_item)
```

`get_toc()` returns an empty list if the PDF has no bookmarks.

## Page images with PyMuPDF

You can use [pymupdf](https://pymupdf.readthedocs.io/en/latest/) to extract each PDF page as a page image. Save these images to `your-temp-pdf-folder/images/*.jpeg`. Be sure to compress the images to avoid massive image file sizes. I will provide proper instructions on how to do this here tomorrow.

## Dependencies

```bash
# System
sudo apt install poppler-utils

# Python
uv tool install pymupdf
```

SQLite ships with Python's standard library - no install needed.
