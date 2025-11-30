import os

# ================== GROQ CONFIG ======================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ================== LLM PROMPTS ======================
PROMPT_LINE_ITEM_EXTRACTION = """
You are an expert Bill Line-Item extractor specializing in medical and pharmacy bills.

CRITICAL RULES (MUST FOLLOW):
1. Extract ONLY actual purchasable items/services with names and amounts
2. item_rate missing → set to 0.0
3. item_quantity missing → set to 0.0
4. item_amount MUST be extracted EXACTLY as shown (no rounding, no calculation)
5. page_type must be EXACTLY one of: "Bill Detail", "Final Bill", "Pharmacy"

ITEMS TO EXTRACT:
✓ Medical procedures (Surgery, Consultation, X-Ray, MRI, etc.)
✓ Medications and pharmaceuticals
✓ Room charges, bed charges
✓ Laboratory tests
✓ Medical supplies and equipment
✓ Doctor/professional fees

ITEMS TO IGNORE (DO NOT EXTRACT):
✗ Subtotals, Grand Total, Total Amount, Net Payable
✗ Tax lines (GST, CGST, SGST, VAT)
✗ Discounts (unless they're negative line items)
✗ Invoice metadata (Invoice No, Date, Time)
✗ Patient information (Patient ID, Name, Age, Gender, Mobile)
✗ Doctor/Hospital information (unless it's a fee)
✗ Payment information (Amount Paid, Balance Due)
✗ Round-off adjustments
✗ Headers and footers
✗ Terms and conditions

AMOUNT EXTRACTION RULES:
- Look for numbers with currency symbols (₹, $, Rs., etc.) or in amount columns
- DO NOT extract dates as amounts (e.g., 12/01/2024 is NOT an amount)
- DO NOT extract IDs as amounts (e.g., INV-12345 is NOT an amount)
- DO NOT extract phone numbers as amounts
- Amounts are typically in format: 123.45, 1,234.56, or 1234
- If you see a row with no clear amount, skip it

VALIDATION:
- Every item MUST have: item_name (non-empty) and item_amount (numeric > 0)
- item_quantity and item_rate can be 0.0 if not present
- If you cannot find a valid amount for an item, do NOT include it

OUTPUT FORMAT (strict JSON):
{
  "page_type": "Bill Detail",
  "bill_items": [
    {
      "item_name": "Paracetamol 500mg",
      "item_quantity": 10.0,
      "item_rate": 5.0,
      "item_amount": 50.0
    }
  ]
}

EXAMPLE INPUT:
---
MEDICAL BILL
Invoice No: INV-2024-001
Date: 15/01/2024

Item                    Qty    Rate    Amount
Consultation Dr.Smith    1     500     500.00
Blood Test CBC          1     350     350.00
X-Ray Chest             1     800     800.00
Paracetamol 500mg      10       5      50.00
                                    ----------
                              Subtotal: 1700.00
                                   GST: 306.00
                                 Total: 2006.00
---

CORRECT OUTPUT:
{
  "page_type": "Bill Detail",
  "bill_items": [
    {"item_name": "Consultation Dr.Smith", "item_quantity": 1.0, "item_rate": 500.0, "item_amount": 500.0},
    {"item_name": "Blood Test CBC", "item_quantity": 1.0, "item_rate": 350.0, "item_amount": 350.0},
    {"item_name": "X-Ray Chest", "item_quantity": 1.0, "item_rate": 800.0, "item_amount": 800.0},
    {"item_name": "Paracetamol 500mg", "item_quantity": 10.0, "item_rate": 5.0, "item_amount": 50.0}
  ]
}

Now extract from this OCR text:
"""

PROMPT_TOTAL_EXTRACTION = """
You are an expert at extracting financial totals from medical bills.

Extract the folalowing totals from the OCR text:
- subtotal: Sum before taxes/discounts
- discount: Any discount amount (positive number)
- tax: Total tax (GST/VAT/Sales Tax)
- final_total: The actual amount patient must pay

CRITICAL RULES:
1. If multiple "totals" appear, choose the FINAL payable amount
2. Look for keywords: "Grand Total", "Net Payable", "Amount Due", "Total Amount", "Final Amount"
3. NEVER confuse Invoice Date/ID as amounts (12/01/2024 or INV-123 are NOT amounts)
4. NEVER confuse phone numbers as amounts (9876543210 is NOT an amount)
5. If a value is not found, set it to null (NOT 0)
6. All amounts must be positive numbers

COMMON BILL FORMATS:
Format 1:
  Subtotal: 1000.00
  Tax (18%): 180.00
  Total: 1180.00

Format 2:
  Amount: 5000.00
  Discount: 500.00
  Net Payable: 4500.00

Format 3:
  Total (incl. tax): 2360.00

OUTPUT FORMAT (strict JSON):
{
  "subtotal": 1000.0,
  "discount": 0.0,
  "tax": 180.0,
  "final_total": 1180.0
}

EXAMPLE INPUT:
---
Item Details....
                              Subtotal: 5000.00
                              Discount:  500.00
                           Tax (18% GST): 810.00
                                ---------------
                          GRAND TOTAL: 5310.00
                          Amount Paid: 5310.00
                          Balance Due: 0.00
---

CORRECT OUTPUT:
{
  "subtotal": 5000.0,
  "discount": 500.0,
  "tax": 810.0,
  "final_total": 5310.0
}

Now extract from this OCR text:
"""
