from fastapi import FastAPI

app = FastAPI(
    title="Py-Scaffold API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url=None,
)
