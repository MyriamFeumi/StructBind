import sys
import os
sys.path.append(os.path.dirname(__file__))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import PredictRequest, PredictResponse
from predict import Predictor

app = FastAPI()

predictor = Predictor()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def accueil():
    return {"message": "Bienvenue sur StructBind !"}

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/info")
def info():
    return {
    "name"     : "StructBind",
    "version"  : "1.0",
    "model"    : "XGBoost",
    "auc"      : 0.956,
    "features" : 23,
    "dataset"  : 30513,
    "author"   : "Myriam Feumi"
    }   

@app.post("/predict")
def predict(request: PredictRequest):
    resultats = predictor.predire(request.sequence)
    return resultats