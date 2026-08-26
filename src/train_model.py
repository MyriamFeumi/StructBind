import pandas as pd
import numpy as np
import json
import os
import warnings
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report, roc_auc_score,
    confusion_matrix, accuracy_score
)
from sklearn.preprocessing import LabelEncoder
import pickle
from xgboost import XGBClassifier

from config import DATASET_CSV, DOSSIER_RESULTS

warnings.filterwarnings('ignore')

# ─── Configuration ────────────────────────────────────────────────

MODEL_FILE    = os.path.join(DOSSIER_RESULTS, "model_rf.pkl")
METRICS_FILE  = os.path.join(DOSSIER_RESULTS, "metrics.json")

# Features utilisées pour l'entraînement
FEATURES = [
    'taille',
    'hydrophobicite',
    'charge_nette',
    'bfactor',
    'ratio_aromatique',
    'ratio_hydrophobe',
    'ratio_donneurs_h',
    'ratio_accepteurs_h',
    'ratio_polaire',
    'ratio_charge',
    'ratio_petits',
    'ratio_grands',
    'diversite_aa',
    'ratio_positif', 'ratio_negatif',
    'ratio_flexible', 'ratio_cysteine',
    'hydro_max', 'hydro_min',
    'charge_absolue'
]

# ─── Fonctions ────────────────────────────────────────────────────

def charger_dataset():
    """Charge et prépare le dataset"""
    if not os.path.exists(DATASET_CSV):
        print(f"Dataset introuvable : {DATASET_CSV}")
        print("Lancez d'abord features.py et negative_examples.py")
        return None

    df = pd.read_csv(DATASET_CSV, sep=';')
    print(f"\nDataset chargé :")
    print(f"  Total lignes     : {len(df)}")
    print(f"  Positifs (1)     : {len(df[df['label']==1])}")
    print(f"  Négatifs (0)     : {len(df[df['label']==0])}")
    print(f"  Features         : {FEATURES}")

    return df

def preparer_donnees(df):
    """Prépare X (features) et y (labels)"""

    # Vérifier les valeurs manquantes
    manquants = df[FEATURES].isnull().sum()
    if manquants.any():
        print(f"\n⚠️ Valeurs manquantes détectées :")
        print(manquants[manquants > 0])
        print("Remplacement par la médiane...")
        df[FEATURES] = df[FEATURES].fillna(df[FEATURES].median())

    X = df[FEATURES].values
    y = df['label'].values

    return X, y

def diviser_dataset(X, y):
    """Divise en train (80%) et test (20%)"""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size    = 0.20,
        random_state = 42,
        stratify     = y  # garde le même ratio +/- dans les deux sets
    )

    print(f"\nDivision du dataset :")
    print(f"  Train : {len(X_train)} exemples")
    print(f"  Test  : {len(X_test)} exemples")

    return X_train, X_test, y_train, y_test

def entrainer_modele(X_train, y_train):
    """Entraîne le modèle Random Forest"""
    print(f"\nEntraînement du modèle Random Forest...")

    model = RandomForestClassifier(
        n_estimators = 100,   # nombre d'arbres
        max_depth    = 10,    # profondeur maximale
        random_state = 42,    # reproductibilité
        n_jobs       = -1,    # utilise tous les CPU
        class_weight = 'balanced'  # gère le déséquilibre +/-
    )

    model.fit(X_train, y_train)
    print(f"  Modèle entraîné ✅")

    return model

def entrainer_xgboost(X_train, y_train):
    """Entraîne le modèle XGBoost"""
    print(f"\nEntraînement du modèle XGBoost...")

    model = XGBClassifier(
        n_estimators     = 300,
        learning_rate    = 0.1,
        max_depth        = 6,
        subsample        = 0.8,
        colsample_bytree = 0.8,
        random_state     = 42,
        n_jobs           = -1,
        scale_pos_weight = 2.5,  # gère le déséquilibre
        eval_metric      = 'auc',
        verbosity        = 0
    )

    model.fit(X_train, y_train)
    print(f"  Modèle entraîné ✅")

    return model

def evaluer_modele(model, X_train, X_test, y_train, y_test):
    """Évalue les performances du modèle"""

    # Prédictions
    y_pred       = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    # Métriques principales
    accuracy = accuracy_score(y_test, y_pred)
    auc      = roc_auc_score(y_test, y_pred_proba)

    # Validation croisée sur le train
    cv_scores = cross_val_score(
        model, X_train, y_train,
        cv=5, scoring='roc_auc'
    )

    print(f"\n{'='*50}")
    print(f"  RÉSULTATS DU MODÈLE")
    print(f"{'='*50}")
    print(f"  Accuracy         : {accuracy:.3f} ({accuracy*100:.1f}%)")
    print(f"  AUC-ROC          : {auc:.3f}")
    print(f"  CV AUC (5-fold)  : {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    print(f"\n  Rapport détaillé :")
    print(classification_report(
        y_test, y_pred,
        target_names=['Faux site (0)', 'Vrai site (1)']
    ))

    print(f"  Matrice de confusion :")
    cm = confusion_matrix(y_test, y_pred)
    print(f"              Prédit 0  Prédit 1")
    print(f"  Réel 0   :    {cm[0][0]:<8}  {cm[0][1]}")
    print(f"  Réel 1   :    {cm[1][0]:<8}  {cm[1][1]}")

    return {
        'accuracy'      : round(accuracy, 4),
        'auc_roc'       : round(auc, 4),
        'cv_auc_mean'   : round(cv_scores.mean(), 4),
        'cv_auc_std'    : round(cv_scores.std(), 4),
    }

def afficher_importance_features(model):
    """Affiche l'importance de chaque feature"""
    importances = model.feature_importances_
    indices     = np.argsort(importances)[::-1]

    print(f"\n  Importance des features :")
    print(f"  {'─'*40}")
    for i, idx in enumerate(indices):
        barre = '█' * int(importances[idx] * 40)
        print(f"  {FEATURES[idx]:<20} : {importances[idx]:.3f} {barre}")

def sauvegarder_modele(model, metrics):
    """Sauvegarde le modèle et ses métriques"""

    # Sauvegarder le modèle
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(model, f)
    print(f"\n  Modèle sauvegardé → {MODEL_FILE} ✅")

    # Sauvegarder les métriques
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"  Métriques sauvegardées → {METRICS_FILE} ✅")

def tester_prediction(model):
    """Simulation de prédiction réelle équilibrée"""
    print(f"\n{'='*60}")
    print(f"  SIMULATION DE PRÉDICTION RÉELLE")
    print(f"{'='*60}")

    df = pd.read_csv(DATASET_CSV, sep=';')

    # Prendre aléatoirement 3 vrais et 3 faux
    vrais = df[df['label'] == 1].sample(3, random_state=42)
    faux  = df[df['label'] == 0].sample(3, random_state=42)
    sample = pd.concat([vrais, faux]).sample(frac=1, random_state=42)

    corrects = 0
    total    = len(sample)

    for _, row in sample.iterrows():
        features = row[FEATURES].values.reshape(1, -1)
        score    = model.predict_proba(features)[0][1]
        attendu  = int(row['label'])
        predit   = 1 if score > 0.5 else 0
        correct  = predit == attendu
        emoji    = "✅" if correct else "❌"

        if correct:
            corrects += 1

        type_reel = "vrai site" if attendu == 1 else "faux site"
        print(f"\n  {row['pdb_id']}/{row['ligand']} ({type_reel})")
        print(f"  Score IA : {score:.3f} ({score*100:.1f}%) {emoji}")

    print(f"\n{'─'*60}")
    print(f"  Résultat : {corrects}/{total} ({corrects/total*100:.0f}%)")
    print(f"{'='*60}")

# ─── Point d'entrée ───────────────────────────────────────────────

if __name__ == "__main__":

    print(f"{'='*60}")
    print(f"  STRUCTBIND — Comparaison Random Forest vs XGBoost")
    print(f"{'='*60}")

    # 1. Charger le dataset
    df = charger_dataset()
    if df is None:
        exit()

    # 2. Préparer les données
    X, y = preparer_donnees(df)

    # 3. Diviser train/test
    X_train, X_test, y_train, y_test = diviser_dataset(X, y)

    # 4. Random Forest
    print(f"\n{'─'*60}")
    print(f"  RANDOM FOREST")
    print(f"{'─'*60}")
    model_rf = entrainer_modele(X_train, y_train)
    metrics_rf = evaluer_modele(
        model_rf, X_train, X_test, y_train, y_test
    )
    afficher_importance_features(model_rf)

    # 5. XGBoost
    print(f"\n{'─'*60}")
    print(f"  XGBOOST")
    print(f"{'─'*60}")
    model_xgb = entrainer_xgboost(X_train, y_train)
    metrics_xgb = evaluer_modele(
        model_xgb, X_train, X_test, y_train, y_test
    )
    afficher_importance_features(model_xgb)

    # 6. Comparaison finale
    print(f"\n{'='*60}")
    print(f"  COMPARAISON FINALE")
    print(f"{'='*60}")
    print(f"  {'Métrique':<20} {'Random Forest':>15} {'XGBoost':>15}")
    print(f"  {'─'*50}")
    print(f"  {'AUC-ROC':<20} {metrics_rf['auc_roc']:>15.3f} {metrics_xgb['auc_roc']:>15.3f}")
    print(f"  {'Accuracy':<20} {metrics_rf['accuracy']:>15.3f} {metrics_xgb['accuracy']:>15.3f}")
    print(f"  {'CV AUC':<20} {metrics_rf['cv_auc_mean']:>15.3f} {metrics_xgb['cv_auc_mean']:>15.3f}")

    # 7. Garder le meilleur modèle
    if metrics_xgb['auc_roc'] > metrics_rf['auc_roc']:
        print(f"\n  → XGBoost est meilleur ✅")
        print(f"  → Gain AUC : +{metrics_xgb['auc_roc'] - metrics_rf['auc_roc']:.3f}")
        sauvegarder_modele(model_xgb, metrics_xgb)
    else:
        print(f"\n  → Random Forest est meilleur ✅")
        sauvegarder_modele(model_rf, metrics_rf)

    # 8. Test de prédiction
    meilleur_model = model_xgb if metrics_xgb['auc_roc'] > metrics_rf['auc_roc'] else model_rf
    tester_prediction(meilleur_model)