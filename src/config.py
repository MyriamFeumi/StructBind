# ================================================================
# StructBind — Fichier de configuration central
# où les paramètres sont définis
# ================================================================

# ─── Dossiers ───────────────────────────────────────────────────
DOSSIER_PDB     = "data"
DOSSIER_RESULTS = "results"
DATASET_CSV     = "data/dataset.csv"

# ─── Protéines à analyser ───────────────────────────────────────
# Ajoutez ou supprimez des PDB IDs selon vos besoins
PROTEINES = [
    "1HVR",   # Protéase VIH
    "1JFF",   # Tubuline + Taxol
    "2J6M",   # EGFR + Erlotinib
]

# ─── Paramètres d'analyse ───────────────────────────────────────
RAYON_SITE_LIAISON = 5.0   # en Angströms
ATOMES_MIN_LIGAND  = 10    # nb atomes minimum pour un ligand valide
POIDS_MIN_LIGAND   = 150   # Da
POIDS_MAX_LIGAND   = 2000  # Da