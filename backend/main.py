# FastAPI Application Entry Point

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Motocross System Backend!"}