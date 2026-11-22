"""StudentIQ conference API: health and research metadata endpoints.

Individual predictions remain disabled until a validated, versioned model and
matching feature schema are implemented and deployed. No synthetic outputs.
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

VERSION = "1.0.0"
app = FastAPI(title="StudentIQ Research API", description="Health and experiment metadata for the StudentIQ conference platform.", version=VERSION)
origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins or ["*"], allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])

class PredictionRequest(BaseModel):
    features: dict = Field(..., description="Named features matching a validated, versioned model schema.")

@app.get("/")
def root():
    return {"service": "StudentIQ Research API", "version": VERSION, "docs": "/docs", "health": "/health"}

@app.get("/health")
def health():
    return {"status": "ok", "service": "studentiq-api", "version": VERSION, "prediction_model": "not_configured"}

@app.get("/research/summary")
def research_summary():
    return {
        "dataset": "Open University Learning Analytics Dataset (OULAD)",
        "task": "four-class classification",
        "target": "final_result",
        "early_feature_cutoff_day": 60,
        "split": "random 80/20 holdout",
        "metrics": {
            "LogisticRegression": {"accuracy": 0.5961751225, "weighted_f1": 0.5447597494},
            "DecisionTree": {"accuracy": 0.5881144302, "weighted_f1": 0.5624797129},
            "RandomForest": {"accuracy": 0.5990200727, "weighted_f1": 0.5535384517}
        },
        "evidence_status": "preliminary; requires stronger validation before publication"
    }

@app.post("/predict")
def predict(request: PredictionRequest):
    raise HTTPException(status_code=503, detail="Individual prediction is not enabled. A validated model artifact and matching feature schema must be configured before this endpoint can make predictions.")
