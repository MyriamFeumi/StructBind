# ================================================================
# StructBind — Fichier de configuration central
# où les paramètres sont définis
# ================================================================

import os

# ─── Dossiers ───────────────────────────────────────────────────
DOSSIER_PDB     = "data"
DOSSIER_RESULTS = "results"
DATASET_CSV     = "data/dataset.csv"

# Création automatique des dossiers si inexistants
os.makedirs(DOSSIER_PDB,     exist_ok=True)
os.makedirs(DOSSIER_RESULTS, exist_ok=True)

# ─── Fichiers de sortie ─────────────────────────────────────────
DATASET_CSV      = os.path.join(DOSSIER_RESULTS, "dataset.csv")
LIGANDS_JSON     = os.path.join(DOSSIER_RESULTS, "ligands.json")


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

# ─── Nucléotides naturels à exclure ─────────────────────────────
NUCLEOTIDES_NATURELS = {
    'ATP', 'ADP', 'AMP',
    'GTP', 'GDP', 'GMP',
    'CTP', 'CDP', 'CMP',
    'UTP', 'UDP', 'UMP',
    'NAD', 'FAD', 'FMN',
    'HEM', 'HEA',
}

# ─── Types non-thérapeutiques (classification RCSB) ─────────────
NON_DRUG_TYPES = {
    'l-peptide linking',
    'd-peptide linking',
    'l-peptide nh3 amino terminus',
    'd-peptide nh3 amino terminus',
    'peptide linking',
    'rna linking',
    'dna linking',
    'l-rna linking',
    'l-dna linking',
    'saccharide',
    'l-saccharide',
    'd-saccharide',
}