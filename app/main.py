from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def show_health():
    return {"status": "ok"}