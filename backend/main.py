import sys
import os
import requests
import re
sys.path.append(os.path.dirname(__file__))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import PredictRequest, PredictResponse, IdentifyRequest
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

@app.post("/identify")
def identifier_proteine(request: IdentifyRequest):
    try:
        raw = request.sequence.strip()
        if raw.startswith('>'):
            header = raw.split('\n')[0]
            # Format UniProt : >sp|P00698|LYSC_HUMAN Lysozyme C OS=Homo sapiens
            match = re.search(r'^>[^\s]+\s+(.+?)(?:\s+OS=|\s+GN=|$)', header)
            if match:
                return {"nom": match.group(1).strip()}
            # Format NCBI : >NP_000000.1 Protein name [Organism]
            match2 = re.search(r'^>[^\s]+\s+(.+?)(?:\s+\[|$)', header)
            if match2:
                return {"nom": match2.group(1).strip()}
    except Exception:
        return {"nom": "Protéine non identifiée"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=300
    )