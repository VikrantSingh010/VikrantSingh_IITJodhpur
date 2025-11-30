---

# BILL EXTRACTION PIPELINE

Bajaj Finserv Health Datathon Project
API based invoice to structured dataset extraction

This repository contains a complete solution to extract line-items and bill totals from multipage medical bills or pharmacy invoices. The pipeline converts PDF or image bills into structured JSON as required in the competition.

The core objective is to capture every bill item without missing or double counting and reconcile totals against the invoice final amount.

---

## 1. Features of the Solution

1. Accepts document URL (PDF or Image)
2. Converts PDFs to page-level images
3. Dual OCR pass with aggressive preprocessing
4. LLM powered item extraction and total estimation
5. Invalid/missing entries auto-corrected
6. Page & table duplicate removal logic
7. Inflation error correction heuristics
8. Re-OCR on suspect entries + LLM refinement
9. Fully compliant output format for datathon evaluation
10. Returns token usage + item count

---

## 2. API Endpoint Specification

### Request

```
POST /extract-bill-data
Content-Type: application/json
```

### Body

```
{
  "document": "https://path-to-file"
}
```

### Expected Response Format

```
{
  "is_success": boolean,
  "token_usage": {
      "total_tokens": int,
      "input_tokens": int,
      "output_tokens": int
  },
  "data": {
      "pagewise_line_items": [
        {
          "page_no": "string",
          "page_type": "Bill Detail | Final Bill | Pharmacy",
          "bill_items": [
            {
              "item_name": "string",
              "item_quantity": float,
              "item_rate": float,
              "item_amount": float
            }
          ]
        }
      ],
      "total_item_count": int
  },
  "totals": {
      "subtotal": float or null,
      "discount": float or null,
      "tax": float or null,
      "final_total": float or null
  }
}
```

---

## 3. Code Flow Explanation

### A. Document Handling (ocr_engine.py)

1. Downloads document from URL
2. Detects PDF/image extension automatically
3. Converts PDF → images pagewise
4. Applies thresholding, denoising and sharpening
5. Dual OCR mode to maximize text recall

### B. Duplicate Page Removal (bill_parser.py)

1. Hash based content comparison
2. Removes repeated OCR texts
3. Numeric-pattern normalisation prevents table duplication

### C. Line-Item Extraction (llm_extractor.py)

1. OCR text sent to Groq LLM
2. Prompt ensures strict JSON return
3. Extracts page_type + bill_items list

### D. Item Validation & Fixing

1. Invalid rows removed
2. High amount spikes scaled intelligently
3. Re-OCR used for mismatched entries
4. LLM final refinement applied to suspect rows

### E. Totals Extraction

1. Full text passed to LLM
2. Extracts Subtotal Discount Tax Final Total
3. Appended to final output JSON

---

## 4. How to Run Locally

### Clone repository

```
git clone <repo-link>
cd project-directory
```

### Create environment

```
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate.bat       # Windows
```

### Install dependencies

```
pip install -r requirements.txt
```

### Export API keys

```
export GROQ_API_KEY=your_key_here
export GROQ_MODEL=llama-3.1-8b-instant
```

### Start server

```
uvicorn app:api --host 0.0.0.0 --port 8000
```

---

## 5. Testing the API

### Using cURL

```
curl -X POST http://localhost:8000/extract-bill-data \
-H "Content-Type: application/json" \
-d '{"document":"https://sample-pdf-url-here"}'
```

### Swagger UI

Open in browser:

```
http://localhost:8000/docs
```

---

## 6. Strengths of Approach

High OCR recall with dual stage preprocessing
LLM enforced JSON structured item extraction
Inflation and numeric correction logic improves accuracy
Duplicate detection avoids double-counting
Supports multi-page complex layouts

---

## 7. Future Enhancements

Add table boundary detection using OpenCV
Confidence based scoring per item row
Training custom OCR corrector model
Cross-page item grouping
Support multilingual billing formats

---
