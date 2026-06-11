from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.routes import router

app = FastAPI(
    title="HealthAI Meal Service",
    description="Service de gestion des repas, aliments et utilisateurs pour HealthAI.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Expose Prometheus metrics on /metrics (scraped by Prometheus, visualised in Grafana).
Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
