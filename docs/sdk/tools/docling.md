# Docling Python SDK — Comprehensive Developer Documentation

> **Last verified:** 9 Sep 2025
> **Sources:** [Docling GitHub README](https://github.com/docling-project/docling), [Docling usage & advanced options](https://docling-project.github.io/docling/usage/advanced_options/)
> **Audience:** Python developers integrating the **Docling SDK** for document parsing, text extraction, layout analysis, and structured data output.

---

## 1) Introduction

**Docling** is a Python library for **document parsing** and **layout‑aware text extraction**. It processes PDFs, images, and office documents into structured data (JSON, Markdown, HTML, plain text) using a pipeline of models and heuristics. Advanced configuration allows fine control over parsing, OCR, image handling, and output.

**Core capabilities:**

* Parse PDFs, Word, PowerPoint, and images.
* Extract text with layout preservation (tables, lists, headings).
* Generate structured outputs: Markdown, HTML, JSON, plain text.
* Integrate OCR for scanned documents.
* Enable/disable features: math extraction, table structure, images, metadata.

---

## 2) Installation

```bash
pip install docling
# optional extras
pip install "docling[ocr]"      # with OCR support
pip install "docling[all]"      # OCR + vision + tables
```

---

## 3) Quick Start Example

```python
from docling.pipeline import Pipeline

# Create default pipeline
doc = Pipeline.from_file("sample.pdf")

# Access structured outputs
print(doc.to_markdown())
print(doc.to_json())
```

---

## 4) Input Sources

Docling supports multiple document sources:

* **File path**: `Pipeline.from_file("report.pdf")`
* **Bytes**: `Pipeline.from_bytes(data, filename="report.pdf")`
* **Streams**: pass `BytesIO` or file‑like objects.
* **URLs**: some integrations allow remote documents.

---

## 5) Outputs

Docling provides multiple output formats:

```python
md   = doc.to_markdown()
html = doc.to_html()
json = doc.to_json()
txt  = doc.to_text()
```

**Examples:**

* Markdown preserves headings, bullet lists, and code blocks.
* JSON includes semantic structure (sections, paragraphs, tables, figures).
* HTML mirrors layout with semantic tags.

---

## 6) Advanced Options (Configuration)

Docling exposes options through a `PipelineConfig` object.

```python
from docling.pipeline import Pipeline, PipelineConfig

config = PipelineConfig(
    use_ocr=True,               # enable OCR for scanned pages
    extract_tables=True,        # parse and export table structures
    extract_math=True,          # capture LaTeX/math content
    extract_images=True,        # include embedded images
    extract_metadata=True,      # preserve document metadata
    output_format="markdown",  # default output format
    max_pages=50,               # limit number of pages to parse
)

pipe = Pipeline(config)
doc = pipe.from_file("scanned.pdf")
print(doc.to_markdown())
```

### 6.1 Key Config Parameters

| Parameter          | Type       | Purpose                                              |
| ------------------ | ---------- | ---------------------------------------------------- |
| `use_ocr`          | bool       | Enable OCR (requires `[ocr]` extra).                 |
| `extract_tables`   | bool       | Extract tables as structured JSON/Markdown.          |
| `extract_math`     | bool       | Extract math expressions (LaTeX/MathML).             |
| `extract_images`   | bool       | Extract inline and embedded images.                  |
| `extract_metadata` | bool       | Include metadata (author, creation date, etc.).      |
| `output_format`    | str        | Default output (`markdown`, `html`, `json`, `text`). |
| `max_pages`        | int        | Stop parsing after N pages.                          |
| `languages`        | list\[str] | OCR language(s), e.g. `["en", "fr"]`.                |
| `ocr_engine`       | str        | Choose OCR backend (e.g., `tesseract`).              |
| `dpi`              | int        | Override image resolution for OCR.                   |
| `preserve_layout`  | bool       | Retain visual spacing in text.                       |
| `skip_empty`       | bool       | Skip empty/blank pages.                              |

---

## 7) OCR Support

* Install with `pip install "docling[ocr]"`.
* Default OCR backend: **Tesseract**.
* Configurable via `languages`, `dpi`, and `ocr_engine`.

```python
config = PipelineConfig(use_ocr=True, languages=["en", "de"])
pipe = Pipeline(config)
doc = pipe.from_file("scanned.pdf")
print(doc.to_text())
```

---

## 8) Handling Tables & Math

Enable structured table extraction:

```python
config = PipelineConfig(extract_tables=True)
doc = Pipeline(config).from_file("tables.pdf")
print(doc.to_json()["tables"])
```

Math extraction:

```python
config = PipelineConfig(extract_math=True)
doc = Pipeline(config).from_file("math.pdf")
print(doc.to_json()["math"])
```

---

## 9) Image & Metadata Extraction

```python
config = PipelineConfig(extract_images=True, extract_metadata=True)
doc = Pipeline(config).from_file("slides.pptx")

# Access extracted images
doc.images  # list of image objects

# Metadata
print(doc.metadata)
```

---

## 10) Advanced Usage Patterns

### 10.1 Limiting pages

```python
config = PipelineConfig(max_pages=10)
doc = Pipeline(config).from_file("large.pdf")
```

### 10.2 Preserve layout spacing

```python
config = PipelineConfig(preserve_layout=True)
doc = Pipeline(config).from_file("report.pdf")
print(doc.to_text())
```

### 10.3 Streaming large docs

```python
with open("big.pdf", "rb") as f:
    for chunk in Pipeline.from_stream(f, chunk_size=5):
        print(chunk.to_markdown())
```

---

## 11) Integration with Other Tools

* **LangChain / LlamaIndex**: Feed extracted structured content for retrieval‑augmented generation (RAG).
* **Pandas / PyArrow**: Load extracted tables into DataFrames.
* **Search/Indexing**: Index JSON/Markdown outputs into ElasticSearch, Weaviate, or Pinecone.
* **Machine Learning**: Use structured math/tables/images as supervised training data.

---

## 12) Error Handling

```python
from docling.exceptions import DoclingError
try:
    doc = Pipeline.from_file("bad.pdf")
except DoclingError as e:
    print("Parse failed:", e)
```

**Common errors:**

* `DoclingError`: Generic pipeline failure.
* `OCRNotInstalledError`: Using OCR without installing `[ocr]` extra.
* `UnsupportedFormatError`: Unsupported file extension.

---

## 13) Performance & Scaling

* Use `max_pages` and `skip_empty` to optimize large docs.
* Enable async/parallel parsing (e.g., multiprocessing across files).
* Caching outputs for unchanged documents reduces compute.
* Disable heavy features (`extract_math`, `extract_images`) if not needed.

---

## 14) Roadmap & Extensibility

Docling supports **plugin parsers** and **custom pipeline stages**. Future roadmap includes:

* Better OCR backends (cloud OCR APIs).
* Improved math recognition.
* Multilingual layout heuristics.

---

## 15) Best Practices

* Always pin Docling version in `requirements.txt` for reproducibility.
* For OCR, tune `dpi` and `languages` for accuracy.
* Use JSON output for structured tasks (RAG, analytics). Use Markdown/HTML for human‑readable tasks.
* Run tests on representative documents before production rollout.
* Log parsing stats (pages, tables, OCR usage) for observability.

---

## 16) FAQ

**Q: Which formats are supported?**
A: PDF, Word (`.docx`), PowerPoint (`.pptx`), and images (`.png`, `.jpg`).

**Q: Do I need OCR for native PDFs?**
A: No, OCR is only required for scanned/image‑only PDFs.

**Q: What languages does OCR support?**
A: Tesseract supports 100+ languages; install language packs separately.

**Q: Can Docling export CSVs?**
A: Not natively, but extracted tables can be written to CSV via Pandas.

**Q: Is GPU required?**
A: No, default pipeline runs on CPU; heavy OCR/image features benefit from GPU if available.

---

### Changelog

* **2025‑09‑09:** First complete SDK guide covering config, OCR, tables, math, images, metadata, error handling, and best practices.
