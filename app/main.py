from fastapi import FastAPI

from .api.rag import router as rag_router

app = FastAPI(title="Living Design PoC Backend")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(rag_router, prefix="/rag", tags=["rag"])
