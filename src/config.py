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
NUCLEOTIDES_NATURELS =  {
    'ATP', 'ADP', 'AMP',  # Adénosine
    'GTP', 'GDP', 'GMP',  # Guanosine
    'CTP', 'CDP', 'CMP',  # Cytidine
    'UTP', 'UDP', 'UMP',  # Uridine
    'NAD', 'FAD', 'FMN',  # Cofacteurs
    'HEM', 'HEA',         # Hème
}

# ─── Types non-thérapeutiques (classification RCSB) ─────────────
NON_DRUG_TYPES = {
    'l-peptide linking',              # Acides aminés naturels
    'd-peptide linking',              # Acides aminés configuration D
    'l-peptide nh3 amino terminus',   # Acides aminés N-terminaux
    'd-peptide nh3 amino terminus',   # Idem configuration D
    'peptide linking',                # Acides aminés modifiés
    'rna linking',                    # Nucléotides ARN
    'dna linking',                    # Nucléotides ADN
    'l-rna linking',                  # ARN configuration L
    'l-dna linking',                  # ADN configuration L
    'saccharide',                     # Sucres généraux
    'l-saccharide',                   # Sucres configuration L
    'd-saccharide',                   # Sucres configuration D
}

# ─── Échelles biophysiques ───────────────────────────────────────
# Échelle de Kyte & Doolittle (1982)
HYDROPHOBICITE = {
    'ALA':  1.8, 'VAL':  4.2, 'ILE':  4.5, 'LEU':  3.8,
    'MET':  1.9, 'PHE':  2.8, 'TRP': -0.9, 'PRO': -1.6,
    'GLY': -0.4, 'SER': -0.8, 'THR': -0.7, 'CYS':  2.5,
    'TYR': -1.3, 'HIS': -3.2, 'ASP': -3.5, 'GLU': -3.5,
    'ASN': -3.5, 'GLN': -3.5, 'LYS': -3.9, 'ARG': -4.5
}

# Charges nettes des acides aminés à pH physiologique (7.4)
CHARGE = {
    'ASP': -1,   # Acide aspartique — négatif
    'GLU': -1,   # Acide glutamique — négatif
    'LYS': +1,   # Lysine — positif
    'ARG': +1,   # Arginine — positif
    'HIS': +0.1  # Histidine — partiellement positif
}