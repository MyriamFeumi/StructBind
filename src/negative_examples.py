import json
import csv
import os
import random
import warnings
from Bio.PDB import PDBParser

from config import (
    PROTEINES, LIGANDS_JSON, DATASET_CSV,
    DOSSIER_PDB, HYDROPHOBICITE, CHARGE, AA_AROMATIQUES, AA_HYDROPHOBES,
    AA_DONNEURS_H, AA_ACCEPTEURS_H 
)
from load_pdb import load_structure

warnings.filterwarnings('ignore')

# ─── Configuration ────────────────────────────────────────────────

# Nombre d'exemples négatifs par protéine
NB_NEGATIFS_PAR_PROTEINE = 3

# Taille des fausses cavités (similaire aux vrais sites)
TAILLE_MIN_NEGATIF = 10
TAILLE_MAX_NEGATIF = 40

# ─── Fonctions utilitaires ────────────────────────────────────────

def charger_ligands_traites():
    """Charge les résultats de extract_ligand.py"""
    if not os.path.exists(LIGANDS_JSON):
        print("ligands.json introuvable → lancez extract_ligand.py d'abord")
        return {}
    with open(LIGANDS_JSON, 'r') as f:
        return json.load(f)

def charger_negatifs_existants():
    """Charge les exemples négatifs déjà dans dataset.csv"""
    if not os.path.exists(DATASET_CSV):
        return set()

    deja_traites = set()
    with open(DATASET_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if row['label'] == '0':
                deja_traites.add(row['pdb_id'])

    return deja_traites

def get_residus_proteiques(structure):
    """Retourne tous les résidus protéiques standards"""
    return [
        r for r in structure[0].get_residues()
        if r.id[0] == ' '
    ]

def get_residus_binding_site(ligand_data):
    """Retourne les numéros de résidus du vrai site de liaison"""
    return {
        (r['nom'], r['numero'], r['chaine'])
        for r in ligand_data['binding_residues']
    }

def generer_fausse_cavite(residus_proteiques, residus_site, taille):
    """
    Génère une fausse cavité en sélectionnant
    des résidus consécutifs hors du site de liaison.
    """
    # Filtrer les résidus qui ne font pas partie du vrai site
    residus_hors_site = [
        r for r in residus_proteiques
        if (r.get_resname(), r.id[1], r.get_parent().id)
        not in residus_site
    ]

    if len(residus_hors_site) < taille:
        return None

    # Choisir un point de départ aléatoire
    max_start = len(residus_hors_site) - taille
    start = random.randint(0, max_start)

    return residus_hors_site[start:start + taille]

def calculer_features_negatif(residus):
    """Calcule les 8 features d'une fausse cavité"""
    from config import (
        AA_AROMATIQUES, AA_HYDROPHOBES,
        AA_DONNEURS_H, AA_ACCEPTEURS_H
    )

    if not residus:
        return None

    hydro_values    = []
    charge_totale   = 0
    b_factors       = []
    composition     = {}
    nb_aromatiques  = 0
    nb_hydrophobes  = 0
    nb_donneurs_h   = 0
    nb_accepteurs_h = 0

    for res in residus:
        resname = res.get_resname()

        hydro_values.append(HYDROPHOBICITE.get(resname, 0))
        charge_totale += CHARGE.get(resname, 0)

        for atom in res:
            b_factors.append(atom.get_bfactor())

        composition[resname] = composition.get(resname, 0) + 1

        if resname in AA_AROMATIQUES  : nb_aromatiques  += 1
        if resname in AA_HYDROPHOBES  : nb_hydrophobes  += 1
        if resname in AA_DONNEURS_H   : nb_donneurs_h   += 1
        if resname in AA_ACCEPTEURS_H : nb_accepteurs_h += 1

    n = len(residus)

    return {
        'taille'            : n,
        'hydrophobicite_moy': round(sum(hydro_values) / n, 3),
        'charge_nette'      : round(charge_totale, 2),
        'bfactor_moy'       : round(sum(b_factors) / len(b_factors), 2),
        'ratio_aromatique'  : round(nb_aromatiques  / n, 3),
        'ratio_hydrophobe'  : round(nb_hydrophobes  / n, 3),
        'ratio_donneurs_h'  : round(nb_donneurs_h   / n, 3),
        'ratio_accepteurs_h': round(nb_accepteurs_h / n, 3),
        'composition'       : composition
    }

def sauvegarder_negatif(pdb_id, features, numero):
    """Ajoute un exemple négatif dans dataset.csv"""
    with open(DATASET_CSV, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([
            pdb_id,
            f"NEG_{numero}",
            "negatif",
            features['taille'],
            features['hydrophobicite_moy'],
            features['charge_nette'],
            features['bfactor_moy'],
            features['ratio_aromatique'],
            features['ratio_hydrophobe'],
            features['ratio_donneurs_h'],
            features['ratio_accepteurs_h'],
            0
        ])

def afficher_stats():
    """Affiche les statistiques du dataset"""
    if not os.path.exists(DATASET_CSV):
        return

    positifs = 0
    negatifs = 0

    with open(DATASET_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if row['label'] == '1':
                positifs += 1
            else:
                negatifs += 1

    print(f"\n{'='*50}")
    print(f"  STATISTIQUES DU DATASET")
    print(f"{'='*50}")
    print(f"  Exemples positifs (label=1) : {positifs}")
    print(f"  Exemples négatifs (label=0) : {negatifs}")
    print(f"  Total                        : {positifs + negatifs}")
    ratio = negatifs / positifs if positifs > 0 else 0
    print(f"  Ratio négatifs/positifs      : {ratio:.2f}")
    print(f"  (idéal : entre 1.0 et 3.0)")
    print(f"{'='*50}")

# ─── Point d'entrée ───────────────────────────────────────────────

if __name__ == "__main__":

    random.seed(42)  # reproductibilité

    # Charger les données
    resultats        = charger_ligands_traites()
    negatifs_existants = charger_negatifs_existants()

    proteines_valides = [
        pdb_id for pdb_id, ligands in resultats.items()
        if len(ligands) > 0  # protéines avec au moins un ligand valide
    ]

    print(f"Protéines avec ligands valides : {len(proteines_valides)}")
    print(f"Déjà avec exemples négatifs   : {len(negatifs_existants)}")
    print(f"A traiter                      : "
          f"{len([p for p in proteines_valides if p not in negatifs_existants])}")

    nouvelles = 0

    for pdb_id in proteines_valides:

        # Skip si déjà traité
        if pdb_id in negatifs_existants:
            continue

        # Charger la structure
        structure = load_structure(pdb_id)
        if not structure:
            continue

        # Récupérer les résidus protéiques
        residus_proteiques = get_residus_proteiques(structure)

        # Récupérer le vrai site de liaison
        ligand_data  = resultats[pdb_id][0]
        residus_site = get_residus_binding_site(ligand_data)

        # Générer NB_NEGATIFS_PAR_PROTEINE fausses cavités
        negatifs_generes = 0

        for i in range(NB_NEGATIFS_PAR_PROTEINE):
            taille = random.randint(
                TAILLE_MIN_NEGATIF,
                TAILLE_MAX_NEGATIF
            )
            fausse_cavite = generer_fausse_cavite(
                residus_proteiques, residus_site, taille
            )

            if not fausse_cavite:
                continue

            features = calculer_features_negatif(fausse_cavite)
            if not features:
                continue

            sauvegarder_negatif(pdb_id, features, i + 1)
            negatifs_generes += 1
            nouvelles += 1

        if negatifs_generes > 0:
            print(f"  {pdb_id} → {negatifs_generes} exemples négatifs ✅")

    print(f"\n  {nouvelles} exemples négatifs ajoutés au total")

    # Afficher les statistiques finales
    afficher_stats()