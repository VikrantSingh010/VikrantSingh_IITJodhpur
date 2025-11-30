Below is the complete README.md exactly in plain text format. No special symbols were added beyond standard markdown headers. You can directly copy and paste.

---

# BILL EXTRACTION PIPELINE

Bajaj Finserv Health Datathon Project
API based invoice to structured dataset extraction

This repository contains a complete solution to extract line-items and bill totals from multi-page medical bills or pharmacy invoices. The extraction system converts PDF or image bills into structured JSON output following the competition specifications.

The core objective is to build a pipeline that captures every line item without missing or double counting and reconciles extracted totals against the actual invoice total.

---

## 1. Features of the Solution

1. Accepts document URL (PDF or Images)
2. Converts PDF pages to images and performs high-accuracy OCR
3. Uses dual OCR mode with preprocessing for clean text extraction
4. Uses LLM powered line item extraction and total calculation
5. Filters, validates and fixes item errors using custom rules
6. Detects and removes duplicate pages or repeated text blocks
7. Auto-corrects inflated numerical values using heuristic adjustment
8. Re-OCR suspects lines and LLM based refinement for final precision
9. Returns output in EXACT format required by evaluation API signature
10. Returns token usage and total item count for complete tracking

---

## 2. API Endpoint Specification

Request
POST /extract-bill-data
Content-Type application/json

Body
{
"document": "[https://path-to-file](https://path-to-file)"
}

Response
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
"page_type": "Bill Detail or Final Bill or Pharmacy",
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

---

## 3. Code Flow Explanation

### Step A: Document Handling

Module ocr_engine.py

1. Downloads file from URL
2. Detects PDF or Image automatically
3. Converts PDF to images pagewise
4. Performs preprocessing with thresholding, sharpening, denoising
5. Runs multi-pass OCR extraction to maximize text accuracy

### Step B: Duplicate Page and Noise Removal

bill_parser.py

1. Hash and compare text blocks
2. Remove repeated OCR pages
3. Normalize numeric sequences to avoid double count tables

### Step C: Line Item Extraction

llm_extractor.py

1. Sends OCR text to Groq LLM
2. Uses structured JSON enforced prompt
3. Extracts page_type and bill_items list

### Step D: Item Validation and Fixing

1. Filters out invalid or empty rows
2. Detects inflated values and auto rescales
3. Suspicious entries are re-OCR’ d at text level
4. LLM refinement corrects wrong values selectively

### Step E: Final Totals Extraction

1. Full joined text processed by LLM
2. Extracts subtotal tax discount final payable
3. Returned with item table in unified JSON response

---

## 4. How to Run Locally

Clone repo
git clone <repo-link>
cd project-directory

Create environment
python3 -m venv venv
source venv/bin/activate    (Linux/Mac)
venv\Scripts\activate.bat   (Windows)

Install libraries
pip install -r requirements.txt

Set API key
export GROQ_API_KEY=your_key_here
export GROQ_MODEL=llama-3.1-8b-instant

Run server
uvicorn app:api --host 0.0.0.0 --port 8000

---

## 5. Testing the API

curl -X POST [http://localhost:8000/extract-bill-data](http://localhost:8000/extract-bill-data) 
-H "Content-Type: application/json" 
-d '{"document":"[https://sample-pdf-url-here"}](https://sample-pdf-url-here%22})'

or open browser
[http://localhost:8000/docs](http://localhost:8000/docs)
and use interactive interface

---

## 6. Strengths of Approach

High OCR recall using dual strategy
LLM enforced JSON accuracy
Auto repair of wrong values and inflation detection
Duplicate data removal prevents double counting
End to end standardised response format
Works for multi page PDF and complex tabular bills

---

## 7. Future Enhancements

Add image based line detection for better segmentation
Train custom small OCR post-correction model
Use confidence scoring per item row
Merge items across pages for unified grouping
Support multilingual bills

---

