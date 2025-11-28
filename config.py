import os

# ================== GROQ CONFIG ======================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL  = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # CHANGE FLEXIBLE

# ================== LLM PROMPTS ======================
PROMPT_LINE_ITEM_EXTRACTION = """
You are a strict Bill Line-Item extractor.

Important Rules:
- If item rate is not present, set item_rate = 0.0
- If item quantity is not present, set item_quantity = 0.0
- Item amount needs to be exactly extracted as present in the document. No rounding off allowed.
- page_type must always be exactly one of: Bill Detail, Final Bill, Pharmacy.

General Rules:
1. Output only actual purchasable bill items — not totals, not headers, not dates.
2. VALID ITEM = MUST contain name and amount. Rate and quantity may be 0.0 as per rules above.
3. Ignore rows like: GST, Invoice Date, Doctor Name, Patient ID, RoundOff, Grand Total.
4. Identify numeric currency-like values ONLY as monetary values.
5. DO NOT extract invoice number, date, mobile numbers as amount.
6. Return JSON only.

Output Format:
{
 "page_type": "Bill Detail | Final Bill | Pharmacy",
 "bill_items":[
   {"item_name":string, "item_quantity":float, "item_rate":float, "item_amount":float}
 ]
}
"""


PROMPT_TOTAL_EXTRACTION = """
Extract final bill totals from OCR text.

Output strictly JSON:
{
 "subtotal": float | null,
 "discount": float | null,
 "tax": float | null,
 "final_total": float
}

Rules:
- If multiple totals exist, choose the one closest to payable amount.
- Never confuse Invoice Date or ID as amounts.
- Final total = amount patient must pay.
"""
