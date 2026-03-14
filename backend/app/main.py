
from fastapi import FastAPI
from .db.init_db import init_db
from .api.ingest import router as ingest_router
from .api.runs import router as runs_router

app = FastAPI(title="TLS energy impact backend")

API_KEY = "123456789"
HMAC_SECRET = b"987654321"

@app.on_event("startup")
def _startup():
    init_db()
    app.state.api_key = API_KEY
    app.state.hmac_secret = HMAC_SECRET

app.include_router(ingest_router)
app.include_router(runs_router)
