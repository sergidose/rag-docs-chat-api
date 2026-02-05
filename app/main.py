from fastapi import FastAPI

app = FastAPI(title="AI Portfolio Template")


@app.get("/health")
def health():
    return {"status": "ok"}
