from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI(title="JSON Crack Visualizer Service")

@app.get("/")
def read_root():
    return {"message": "Welcome to JSON Crack Visualizer Service"}

@app.post("/visualize")
async def visualize_json(request: Request):
    try:
        payload = await request.json()
        formatted = json.dumps(payload, indent=2)
        return {"formatted_json": formatted}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
