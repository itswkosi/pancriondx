from fastapi import FastAPI

from .routes import router

app = FastAPI(title="Genomic Clinical Decision Support")
app.include_router(router)
