import json
from groq import Groq
from config import GROQ_API_KEY,GROQ_MODEL,PROMPT_LINE_ITEM_EXTRACTION,PROMPT_TOTAL_EXTRACTION

client=Groq(api_key=GROQ_API_KEY)

def call_llm_json(system,user):
    res=client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0,
        response_format={"type":"json_object"},
        messages=[{"role":"system","content":system},{"role":"user","content":user}]
    )
    raw=res.choices[0].message.content
    try: out=json.loads(raw)
    except: out={}
    return out,res.usage.total_tokens,res.usage.prompt_tokens,res.usage.completion_tokens

def extract_line_items(text):
    user=f"Extract structured line items from bill:\n{text}"
    return call_llm_json(PROMPT_LINE_ITEM_EXTRACTION,user)

def extract_totals(text):
    user=f"Find subtotal, taxes, final payable amount:\n{text}"
    return call_llm_json(PROMPT_TOTAL_EXTRACTION,user)
