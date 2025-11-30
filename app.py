from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from bill_parser import extract_bill

api = FastAPI(title="Bill Extraction API")

class Req(BaseModel):
    document: HttpUrl

@api.post("/extract-bill-data")
def run(r: Req):
    return extract_bill(r.document)

@api.get("/")
def home():
    return {"status": "running", "usage": "/extract-bill-data"}


# -------- Running inference without starting server -------- #
if __name__ == "__main__":
    pdf_url = "https://hackrx.blob.core.windows.net/assets/datathon-IIT/Sample%20Document%203.pdf?sv=2025-07-05&spr=https&st=2025-11-28T10%3A08%3A55Z&se=2025-11-30T10%3A08%3A00Z&sr=b&sp=r&sig=S7bEYe%2FswaS7BZPZBiEnc6gXfb9YUH22H%2BBn%2FG2Vycc%3D"  # <--- put URL here
    result = extract_bill(pdf_url)
    print(result)
