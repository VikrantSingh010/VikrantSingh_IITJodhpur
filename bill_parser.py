from concurrent.futures import ThreadPoolExecutor
import hashlib, re

from ocr_engine import load_document_as_images, extract_text_from_image
from llm_extractor import extract_line_items, extract_totals, call_llm_json

ALLOWED_PAGE_TYPES = {"Bill Detail", "Final Bill", "Pharmacy"}

def validate_items(items):
    
    valid=[]
    for i in items or []:
        if not isinstance(i,dict): continue
        name=str(i.get("item_name","")).strip()
        if not name: continue

        try: qty=float(i.get("item_quantity",0) or 0)
        except: qty=0
        try: rate=float(i.get("item_rate",0) or 0)
        except: rate=0
        try: amt=float(i.get("item_amount",0))
        except: continue

        valid.append({"item_name":name,"item_quantity":qty,"item_rate":rate,"item_amount":amt})
    return valid


# ================== DUPLICATE PAGE / TABLE REMOVAL ==================
def hash_text_block(text): return hashlib.md5(text.lower().replace(" ","").encode()).hexdigest()
def normalize_digits(text): return " ".join(re.findall(r"\d+\.?\d*",text))

def remove_duplicate_tables(page_texts):
    """REMOVE TABLE IF OCR IMAGE + PDF TEXT ARE SAME"""
    seen_text=set()
    seen_num=set()
    clean=[]

    for t in page_texts:
        h1=hash_text_block(t)           
        h2=hash_text_block(normalize_digits(t))  

        if h1 in seen_text or h2 in seen_num:
            continue         

        seen_text.add(h1); seen_num.add(h2)
        clean.append(t)

    return clean


# ================== OUTLIER / INFLATION CHECK ==================
def detect_inflation(item):
    amt=item["item_amount"]
    rate=item["item_rate"]
    qty=item["item_quantity"]

    if amt>20000 and qty<=5: return True
    if rate>10000: return True
    if amt>8000 and "bed" not in item["item_name"].lower(): return True
    return False


# ================== AUTO CORRECTION ==================
def auto_fix(item):
    rate,qty,amt=item["item_rate"],item["item_quantity"],item["item_amount"]

    if rate>10000: item["item_rate"]=rate/100
    if amt>20000: item["item_amount"]=amt/100

    expected=item["item_rate"]*qty
    if expected>0 and abs(expected-item["item_amount"])>item["item_amount"]*0.25:
        item["item_amount"]=expected
    return item


# ================== TARGETED RE-OCR ==================
def reocr_suspects(text,items):
    new=[]
    for it in items:
        if detect_inflation(it):
            for line in text.split("\n"):
                if it["item_name"].split()[0].lower() in line.lower():
                    nums=re.findall(r"\d+\.?\d*",line)
                    if nums:
                        amt=float(nums[-1])
                        it["item_amount"]=amt if amt<20000 else amt/100
        new.append(auto_fix(it))
    return new


# ================== LLM FINAL VERIFICATION ==================
def refine_by_llm(items,text):
    bad=[i for i in items if detect_inflation(i)]
    if not bad: return items
    bad=bad[:6]  # avoid slow cost

    for i in bad:
        prompt=f"""
        From this OCR bill below, correct ONLY if amount is wrong.
        Fix fields for: {i['item_name']}
        Return strict JSON only → {{ "quantity":?,"rate":?,"amount":? }}

        BILL:
        {text}
        """
        out,_,_,_=call_llm_json("",prompt)

        for k in ["quantity","rate","amount"]:
            if k in out:
                try: i[f"item_{k}"]=float(out[k])
                except: pass
    return items


# ============================ MAIN PIPELINE ============================
def extract_bill(url:str):
    images=load_document_as_images(url)

    # OCR images
    with ThreadPoolExecutor(max_workers=min(4,len(images))) as p:
        raw_texts=list(p.map(extract_text_from_image,images))

    # REMOVE DUPLICATE IMAGE+TEXT TABLES 
    texts=remove_duplicate_tables(raw_texts)

    pages=[]; full=""; T=IN=OUT=0

    # ---- PAGEWISE ITEM EXTRACTION ----
    for pg,text in enumerate(texts,1):
        full+=text+"\n"
        out,t,i,o=extract_line_items(text)
        T+=t;IN+=i;OUT+=o

        items=validate_items(out.get("bill_items",[]))
        items=reocr_suspects(text,items)
        items=refine_by_llm(items,text)  

        ptype=out.get("page_type","Bill Detail")
        if ptype not in ALLOWED_PAGE_TYPES: ptype="Bill Detail"

        pages.append({"page_no":str(pg),"page_type":ptype,"bill_items":items})

    # ---- TOTALS EXTRACTION ----
    totals,t2,i2,o2=extract_totals(full)
    T+=t2;IN+=i2;OUT+=o2

    return {
        "is_success":True,
        "token_usage":{"total_tokens":T,"input_tokens":IN,"output_tokens":OUT},
        "data":{
            "pagewise_line_items":pages,
            "total_item_count":sum(len(p["bill_items"]) for p in pages)
        },
        "totals":totals
    }
