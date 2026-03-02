from fastapi import FastAPI, Request
from datetime import datetime
import json

app = FastAPI()

@app.post("/ingest")
async def ingest(request: Request):
    data = await request.json()

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "payload_size": len(json.dumps(data)),
        "data": data
    }

    with open("log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return {"status": "received"}
