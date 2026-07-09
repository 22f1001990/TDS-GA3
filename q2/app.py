from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from openai import OpenAI

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

class Request(BaseModel):
    image_base64: str
    question: str


@app.post("/answer-image")
def answer(req: Request):

    response = client.chat.completions.create(
        model="gemma3:4b",
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
