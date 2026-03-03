
from fastapi import FastAPI
from .db.init_db import init_db
from .api.ingest import router as ingest_router
from .api.runs import router as runs_router

app = FastAPI(title="TLS energy impact backend")

@app.on_event("startup")
def _startup():
    init_db()

app.include_router(ingest_router)
app.include_router(runs_router)
