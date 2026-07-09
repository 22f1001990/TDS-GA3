from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)

class InvoiceRequest(BaseModel):
    invoice_text: str

@app.post("/extract")
def extract(req: InvoiceRequest):

    prompt = f"""
Extract these fields from the invoice.

Return ONLY valid JSON.

Schema:
{{
    "invoice_no": string|null,
    "date": "YYYY-MM-DD"|null,
    "vendor": string|null,
    "amount": number|null,
    "tax": number|null,
    "currency": string|null
}}

Invoice:

{req.invoice_text}
"""

    response = client.chat.completions.create(
        model="llama3.2:latest",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
    )

    text = response.choices[0].message.content

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
    for key in ["invoice_no", "date", "vendor", "amount", "tax", "currency"]:
        data.setdefault(key, None)

    return data