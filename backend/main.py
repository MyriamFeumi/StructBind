from fastapi import FastAPI

app = FastAPI()

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

@app.get("/predict")
def predict(fasta):
    return