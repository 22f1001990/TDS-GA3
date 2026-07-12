from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dateutil import parser
import json
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    base_url="https://aipipe.org/openrouter/v1",
    api_key="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjEwMDE5OTBAZHMuc3R1ZHkuaWl0bS5hYy5pbiIsImlhdCI6MTc4Mzc4ODIzMSwiaXNzIjoiaHR0cHM6Ly9haXBpcGUub3JnIiwiYXVkIjoiYWlwaXBlLWFwaSIsImV4cCI6MTc4NDM5MzAzMX0.1KsHShZ9N4nBAIah6rtVmnFdIXHN0uv-Q0s18ptyBKY"
    )
class InvoiceRequest(BaseModel):
    invoice_text: str   
import re

def parse_amount(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value

    s = str(value)

    m = re.search(r"\d[\d,]*(?:\.\d+)?", s)
    if not m:
        return None

    num = m.group().replace(",", "")

    return float(num) if "." in num else int(num)


def clean_invoice_no(value):
    if value is None:
        return None

    s = str(value).strip()

    s = re.sub(
        r'^(Invoice\s*(Number|No\.?|#)?|Ref(?:erence)?\.?)\s*:?\s*',
        '',
        s,
        flags=re.IGNORECASE
    )

    return s
@app.post("/extract")
def extract(req: InvoiceRequest):
    prompt = f"""
Extract the following fields from the invoice.

Return ONLY valid JSON.

Rules:
- Always return all six keys.
- If a value is missing, return null.
- amount is the subtotal before tax.
- tax is the tax amount only.
- amount is the pre-tax amount.
- The pre-tax amount may be labelled as Goods, Amount, Subtotal, Net Amount, or similar.
- tax is the tax amount only.
- Invoice number may be labelled as Invoice Number, Invoice No, Invoice #, Number, Ref, or Reference. Copy it exactly.
- Currency may be given in a Currency field or as a prefix to monetary values (e.g. USD 780.00, Rs. 3,100.00, EUR 45.00). Return the currency code or symbol shown.
- Copy the date exactly as it appears on the invoice.
- Currency must be returned exactly as it appears on the invoice.
- If the invoice shows "USD 780.00", return "USD".
- If the invoice shows "$780.00", return "$".
- Do not convert currency codes to symbols or symbols to codes.
- Do NOT guess or reinterpret ambiguous dates.

Schema:
{{
  "invoice_no": null,
  "date": null,
  "vendor": null,
  "amount": null,
  "tax": null,
  "currency": null
}}

Invoice:

{req.invoice_text}
"""
    #print("===== PROMPT =====")
    #print(prompt)
    #print("==================")

    response = client.chat.completions.create(
        model="openai/gpt-4.1-nano",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
    )

    text = response.choices[0].message.content
    
    #print(text)
    
    # Remove markdown fences if present
    text = text.replace("```json", "").replace("```", "").strip()
    #print("===== RAW MODEL RESPONSE =====")
    #print(text)
    #print("==============================")
    try:
        data = json.loads(text)
        
    
    except Exception as e:
        print("JSON error:", e)
        print("Model returned:")
        print(text)
        data = {
            "invoice_no": None,
            "date": None,
            "vendor": None,
            "amount": None,
            "tax": None,
            "currency": None,
        }

    # Ensure all required keys exist
    # Ensure all required keys exist
    for key in ["invoice_no", "date", "vendor", "amount", "tax", "currency"]:
        data.setdefault(key, None)

    # Normalize the date only if it exists
        if data["date"]:
            try:
                data["date"] = parser.parse(
                    data["date"],
                    dayfirst=True
                ).strftime("%Y-%m-%d")
            except Exception:
                pass
        #print("===== PARSED JSON =====")
        #print(data)
        #print("=======================")
    data["amount"] = parse_amount(data["amount"])
    data["tax"] = parse_amount(data["tax"])

    data["invoice_no"] = clean_invoice_no(data["invoice_no"])
    print(data)
    return data
