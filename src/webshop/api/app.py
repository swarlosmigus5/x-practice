import logging

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Webshop Analytics API", version="1.0.0")


@app.get("/health")
def health_check():
    return {"status": "healthy"}

