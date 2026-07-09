from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
from openai import OpenAI

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
    api_key="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjEwMDE5OTBAZHMuc3R1ZHkuaWl0bS5hYy5pbiIsImlhdCI6MTc4MzU5MjU1OCwiaXNzIjoiaHR0cHM6Ly9haXBpcGUub3JnIiwiYXVkIjoiYWlwaXBlLWFwaSIsImV4cCI6MTc4NDE5NzM1OH0.gMmdM6W_AXtuHpJzoXxSE5xZ34z9Ujfcnu7iWtHZoy0",
)


class Request(BaseModel):
    image_base64: str
    question: str


@app.post("/answer-image")
def answer(req: Request):

    response = client.chat.completions.create(
        model="openai/gpt-4.1-nano",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Answer ONLY the question. "
                            "If the answer is numeric, return only the number without units.\n\n"
                            f"Question: {req.question}"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{req.image_base64}"
                        },
                    },
                ],
            }
        ],
    )

    answer = response.choices[0].message.content.strip()

    return {"answer": answer}
