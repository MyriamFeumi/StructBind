# StructBind

Pipeline de prédiction des sites de liaison des protéines 
et de criblage virtuel de médicaments à partir d'une séquence FASTA

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![AUC](https://img.shields.io/badge/AUC--ROC-0.980-brightgreen)]()

## Qu'est-ce que StructBind ?

StructBind est un pipeline bioinformatique open source qui prédit 
les sites de liaison des protéines et identifie les médicaments 
potentiels directement à partir d'une séquence FASTA, en utilisant 
l'intelligence artificielle.

## Pipeline

Séquence FASTA
↓
ESMFold → Structure 3D (.pdb)
↓
fpocket → Détection des cavités
↓
XGBoost → Score des sites (AUC = 0.980)
↓
AutoDock Vina → Criblage virtuel des médicaments
↓
Résultats : sites classés + ligands potentiels


---

## Installation

```bash

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Installer fpocket
sudo apt install fpocket

# Installer AutoDock Vina
sudo apt install autodock-vina
```

## Utilisation

### Lancer le backend

```bash
uvicorn backend.main:app --reload
```

### Lancer le frontend

```bash
npm start
```

