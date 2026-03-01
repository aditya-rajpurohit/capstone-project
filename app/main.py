from fastapi import FastAPI

app = FastAPI(title="Capstone Project")


@app.get("/")
async def root():
    return {"status": "running"}
