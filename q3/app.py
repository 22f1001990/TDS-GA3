from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import json
from dateutil import parser
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    base_url="https://aipipe.org/openrouter/v1",
    api_key="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjEwMDE5OTBAZHMuc3R1ZHkuaWl0bS5hYy5pbiIsImlhdCI6MTc4MzU5MjU1OCwiaXNzIjoiaHR0cHM6Ly9haXBpcGUub3JnIiwiYXVkIjoiYWlwaXBlLWFwaSIsImV4cCI6MTc4NDE5NzM1OH0.gMmdM6W_AXtuHpJzoXxSE5xZ34z9Ujfcnu7iWtHZoy0",
)
class InvoiceRequest(BaseModel):
    invoice_text: str

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
- Copy the date exactly as it appears on the invoice.
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
    print(text)
    # Remove markdown fences if present
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(text)
    except Exception:
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

        return data