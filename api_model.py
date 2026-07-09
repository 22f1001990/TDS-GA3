from openai import OpenAI

client = OpenAI(
    base_url="https://aipipe.org/openrouter/v1",
    api_key="eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjEwMDE5OTBAZHMuc3R1ZHkuaWl0bS5hYy5pbiIsImlhdCI6MTc4MzU5MjU1OCwiaXNzIjoiaHR0cHM6Ly9haXBpcGUub3JnIiwiYXVkIjoiYWlwaXBlLWFwaSIsImV4cCI6MTc4NDE5NzM1OH0.gMmdM6W_AXtuHpJzoXxSE5xZ34z9Ujfcnu7iWtHZoy0",
)

models = client.models.list()
for m in models.data:
    print(m.id)
