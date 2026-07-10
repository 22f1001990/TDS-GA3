from typing import Dict, Any, Optional
from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,  create_model, TypeAdapter, Field
from openai import OpenAI

app = FastAPI()

# 1. Enable CORS (Required by Assignment Rules)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client (Make sure OPENAI_API_KEY environment variable is set)
client = OpenAI(
    base_url="https://aipipe.org/openrouter/v1",
    api_key="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjEwMDE5OTBAZHMuc3R1ZHkuaWl0bS5hYy5pbiIsImlhdCI6MTc4MzU5MjU1OCwiaXNzIjoiaHR0cHM6Ly9haXBpcGUub3JnIiwiYXVkIjoiYWlwaXBlLWFwaSIsImV4cCI6MTc4NDE5NzM1OH0.gMmdM6W_AXtuHpJzoXxSE5xZ34z9Ujfcnu7iWtHZoy0",
)

# 2. Define the Incoming Request Structure
class ExtractRequest(BaseModel):
    text: str
    schema_def: Dict[str, str] =Field(..., alias="schema")


# Map user-provided string types to actual Python/Pydantic types
TYPE_MAPPING = {
    "string": str,
    "integer": int,
    "float": float,
    "boolean": bool,
    "date": date
}

# 3. Create the API Endpoint

@app.post("/dynamic-extract")
async def dynamic_extract(payload: ExtractRequest):
    text = payload.text
    schema_def = payload.schema_def
    print(schema_def)
    # Step A: Build a Dynamic Pydantic Model on the fly
    fields = {}
    for field_name, type_str in schema_def.items():
        if type_str not in TYPE_MAPPING:
            raise HTTPException(status_code=400, detail=f"Unsupported type: {type_str}")
        if type_str == "date":
            field_definition = (
                Optional[TYPE_MAPPING[type_str]], 
                Field(default=None, description="The date extracted from text, strictly formatted as YYYY-MM-DD.")
            )
        else:
            field_definition = (Optional[TYPE_MAPPING[type_str]], None)
        fields[field_name] = field_definition
        # Make every field Optional and default to None (Rule #2)
        fields[field_name] = (Optional[TYPE_MAPPING[type_str]], None)

    try:
        # Generate a real, dynamic Pydantic class at runtime
        DynamicModel = create_model("DynamicExtractionSchema", **fields)
        
        # Step B: Ask the LLM to fill the schema using OpenAI Structured Outputs
        # This natively guarantees correct keys, correct types, and no extras
        response = client.beta.chat.completions.parse(
            model="openai/gpt-4.1-nano",
            #messages=[
            #            {"role": "system", "content": "Extract the requested fields from the user text. If a field cannot be found, leave it as null."},
            #    {"role": "user", "content": text}
            #],
            messages=[
        {
            "role": "system", 
            "content": (
                "Extract the requested fields from the user text. "
                "If a field cannot be found, leave it as null. "
                "CRITICAL: Any fields representing a date must be strictly formatted in ISO format: YYYY-MM-DD (e.g., '2026-06-12')."
                "You are a strict data extraction engine.\n\n"
                "Rules:\n"
                 "1. Extract ONLY the precise value requested. Do not include extra context, filler words, or suffixes (e.g., extract 'HDFC', NOT 'HDFC Acct 7890' or 'HDFC Bank').\n"
                 "2. If a field cannot be found or is not explicitly clear in the text, leave it as null.\n"
                 "3. Any fields representing a date must be strictly formatted in ISO format: YYYY-MM-DD.\n"
                 "4. NEVER include leading grammatical articles such as 'The', 'A', or 'An' at the start of an extracted text phrase (e.g., extract 'laptop arrived damaged', NOT 'The laptop arrived damaged')\n"
            )
        },
        {"role": "user", "content": text}
    ],
            response_format=DynamicModel, # Forces the LLM to output exactly our dynamic structure
        )
        
        # Step C: Return the validated structure directly
        extracted_data = response.choices[0].message.parsed
        
        # Convert Pydantic object back into clean JSON
        # TypeAdapter helps handle complex date-to-string serialized exports
        return TypeAdapter(DynamicModel).dump_python(extracted_data, mode="json")

    except Exception as e:

        #raise HTTPException(status_code=500, detail=str(e))
        
        import traceback
        traceback.print_exc()
        raise
