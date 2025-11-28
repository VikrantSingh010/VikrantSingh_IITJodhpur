from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from bill_parser import extract_bill

api=FastAPI(title="Bill Extraction API")

class Req(BaseModel):
    document:HttpUrl

@api.post("/extract-bill-data")
def run(r:Req):
    return extract_bill(r.document)

@api.get("/")
def home():
    return {"status":"running","usage":"/extract-bill-data"}
