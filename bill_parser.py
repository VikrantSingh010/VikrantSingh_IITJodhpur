from concurrent.futures import ThreadPoolExecutor
import re

from ocr_engine import load_document_as_images, extract_text_from_image
from llm_extractor import extract_line_items, extract_totals

ALLOWED_PAGE_TYPES = {"Bill Detail", "Final Bill", "Pharmacy"}

def validate_items(items):
    """Apply rules:
    - if rate missing → 0.0
    - if qty missing → 0.0
    - NEVER modify item_amount (must match document)
    """
    valid = []
    for raw in items or []:
        if not isinstance(raw, dict):
            continue

        name = str(raw.get("item_name", "")).strip()
        if not name:
            continue

        # default 0.0 for missing rate/qty
        qty = raw.get("item_quantity", 0.0) or 0.0
        rate = raw.get("item_rate", 0.0) or 0.0
        amt  = raw.get("item_amount", 0.0)

        # convert to float where possible, but don't recompute amount
        try:
            qty = float(qty)
        except Exception:
            qty = 0.0

        try:
            rate = float(rate)
        except Exception:
            rate = 0.0

        try:
            amt = float(amt)
        except Exception:
            # if amount not numeric, skip the row – can't be valid bill
            continue

        valid.append({
            "item_name": name,
            "item_quantity": qty,
            "item_rate": rate,
            "item_amount": amt,
        })

    return valid

def extract_bill(url: str):
    # OCR all pages (in parallel for speed)
    images = load_document_as_images(url)

    with ThreadPoolExecutor(max_workers=min(4, len(images) or 1)) as pool:
        texts = list(pool.map(extract_text_from_image, images))

    pages = []
    T_total = T_in = T_out = 0
    full_text = ""

    # PAGEWISE LLM CALLS
    for i, text in enumerate(texts, 1):
        full_text += text + "\n"

        out, t, in_t, out_t = extract_line_items(text)

        items = validate_items(out.get("bill_items", []))

        page_type = out.get("page_type", "Bill Detail")
        if page_type not in ALLOWED_PAGE_TYPES:
            page_type = "Bill Detail"

        pages.append({
            "page_no": str(i),
            "page_type": page_type,
            "bill_items": items,
        })

        T_total += t
        T_in    += in_t
        T_out   += out_t

    # OPTIONAL: handle image URLs found inside OCR text (e.g., your sample PDFs)
    # Look for URLs ending with image extensions
    url_pattern = r"(https?://\S+?(?:jpg|jpeg|png|webp|tif|tiff|bmp))"
    extra_image_urls = re.findall(url_pattern, full_text, flags=re.IGNORECASE)

    for idx, img_url in enumerate(extra_image_urls, start=len(pages) + 1):
        try:
            extra_img_text = extract_text_from_image(
                load_document_as_images(img_url)[0]
            )
        except Exception:
            continue

        full_text += "\n" + extra_img_text

        out, t, in_t, out_t = extract_line_items(extra_img_text)
        items = validate_items(out.get("bill_items", []))

        page_type = out.get("page_type", "Bill Detail")
        if page_type not in ALLOWED_PAGE_TYPES:
            page_type = "Bill Detail"

        pages.append({
            "page_no": str(idx),
            "page_type": page_type,
            "bill_items": items,
        })

        T_total += t
        T_in    += in_t
        T_out   += out_t

    # GLOBAL TOTALS
    totals, t2, in2, out2 = extract_totals(full_text)
    T_total += t2
    T_in    += in2
    T_out   += out2

    return {
        "is_success": True,
        "token_usage": {
            "total_tokens": T_total,
            "input_tokens": T_in,
            "output_tokens": T_out,
        },
        "data": {
            "pagewise_line_items": pages,
            "total_item_count": sum(len(p["bill_items"]) for p in pages),
        },
        "totals": totals,
    }
