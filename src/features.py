import csv
import json
import os
import warnings
from Bio.PDB import PDBParser

from config import (
    PROTEINES, DATASET_CSV, LIGANDS_JSON,
    DOSSIER_PDB, RAYON_SITE_LIAISON,
    HYDROPHOBICITE, CHARGE, AA_AROMATIQUES, AA_HYDROPHOBES,
    AA_DONNEURS_H, AA_ACCEPTEURS_H          # ← importées depuis config
)
from load_pdb import load_structure
from extract_ligand import find_binding_site, get_residues

warnings.filterwarnings('ignore')

# ─── Fonctions utilitaires ────────────────────────────────────────

def charger_ligands_traites():
    """Charge les pdb_id/ligands déjà dans le dataset CSV"""
    if not os.path.exists(DATASET_CSV):
        return set()

    deja_traites = set()
    with open(DATASET_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            deja_traites.add(f"{row['pdb_id']};{row['ligand']}")

    return deja_traites

def initialiser_csv():
    """Crée le fichier CSV avec en-têtes si inexistant"""
    if not os.path.exists(DATASET_CSV):
        with open(DATASET_CSV, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([
                'pdb_id', 'ligand', 'tag',
                'taille', 'hydrophobicite',
                'charge_nette', 'bfactor',
                'ratio_aromatique', 'ratio_hydrophobe',
                'ratio_donneurs_h', 'ratio_accepteurs_h',
                'label'
            ])
        print(f"Dataset initialisé → {DATASET_CSV} ✅")

def sauvegarder_features(pdb_id, ligand, tag, features, label=1):
    """Ajoute une ligne au dataset CSV"""
    with open(DATASET_CSV, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([
            pdb_id, ligand, tag,
            features['taille'],
            features['hydrophobicite_moy'],
            features['charge_nette'],
            features['bfactor_moy'],
            features['ratio_aromatique'],
            features['ratio_hydrophobe'],
            features['ratio_donneurs_h'],
            features['ratio_accepteurs_h'],
            label
            ])

def calculer_features(binding_residues):
    """Calcule 8 features biophysiques d'un site de liaison"""
    if not binding_residues:
        return None

    hydro_values    = []
    charge_totale   = 0
    b_factors       = []
    composition     = {}
    nb_aromatiques  = 0
    nb_hydrophobes  = 0
    nb_donneurs_h   = 0
    nb_accepteurs_h = 0

    for res in binding_residues:
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

    n = len(binding_residues)

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
def afficher_features(pdb_id, ligand, features):
    """Affiche les features de façon lisible"""
    print(f"\n  Features — {pdb_id} / {ligand}")
    print(f"  {'-'*40}")
    print(f"    Taille          : {features['taille']} résidus")
    print(f"    Hydrophobicité  : {features['hydrophobicite_moy']}")
    print(f"    Charge nette    : {features['charge_nette']}")
    print(f"    Flexibilité     : {features['bfactor_moy']}")
    print(f"    Composition     :")
    for aa, count in sorted(features['composition'].items()):
        print(f"      {aa} : {count}")

def afficher_dataset():
    """Affiche le contenu du dataset de façon lisible"""
    if not os.path.exists(DATASET_CSV):
        print("Dataset vide.")
        return

    with open(DATASET_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows   = list(reader)

    if not rows:
        print("Dataset vide.")
        return

    headers = list(rows[0].keys())
    widths  = {
        h: max(len(h), max(len(str(r[h])) for r in rows))
        for h in headers
    }
    sep = "+" + "+".join("-" * (widths[h]+2) for h in headers) + "+"

    print(f"\n{sep}")
    print("|" + "|".join(
        f" {h:<{widths[h]}} " for h in headers
    ) + "|")
    print(sep)
    for row in rows:
        print("|" + "|".join(
            f" {str(row[h]):<{widths[h]}} " for h in headers
        ) + "|")
    print(sep)
    print(f"\n  {len(rows)} entrée(s) dans le dataset.")

def recuperer_residus_depuis_structure(pdb_id, ligand_data):
    """Recharge la structure et recalcule les résidus du site"""
    structure = load_structure(pdb_id)
    if not structure:
        return None

    all_ligands = get_residues(structure, 'ligand')
    ligand_obj  = next(
        (l for l in all_ligands
         if l.get_resname() == ligand_data['resname']),
        None
    )

    if not ligand_obj:
        return None

    return find_binding_site(structure, ligand_obj)

# ─── Point d'entrée ───────────────────────────────────────────────

if __name__ == "__main__":

    # Vérifier que ligands.json existe
    if not os.path.exists(LIGANDS_JSON):
        print("Aucun résultat trouvé.")
        print("Lancez d'abord : python src/extract_ligand.py")
        exit()

    # Charger les résultats de extract_ligand.py
    with open(LIGANDS_JSON, 'r') as f:
        resultats = json.load(f)

    # Initialiser le CSV si nécessaire
    initialiser_csv()

    # Charger les entrées déjà dans le dataset
    deja_traites = charger_ligands_traites()
    print(f"Entrées déjà dans le dataset : {len(deja_traites)}")

    nouvelles = 0

    # Itérer sur les protéines dans ligands.json
    for pdb_id, ligands in resultats.items():

        # Skip si pas de ligands valides
        if not ligands:
            continue

        
        for ligand_data in ligands:

            # Vérifier que l'entrée est complète
            if not isinstance(ligand_data, dict):
                continue
            if 'resname' not in ligand_data:
                continue
            if 'binding_residues' not in ligand_data:
                continue
            if not ligand_data['binding_residues']:
                continue

            resname = ligand_data['resname']
            tag     = ligand_data.get('tag', 'inconnu')
            cle     = f"{pdb_id};{resname}"

            # Déjà dans le dataset → skip
            if cle in deja_traites:
                continue

            # Recalculer les résidus
            binding_residues = recuperer_residus_depuis_structure(
                pdb_id, ligand_data
            )

            if not binding_residues:
                continue

            # Calculer + sauvegarder
            features = calculer_features(binding_residues)
            if not features:
                continue

            afficher_features(pdb_id, resname, features)
            sauvegarder_features(pdb_id, resname, tag, features)
            deja_traites.add(cle)
            nouvelles += 1

    # Résumé
    print(f"\n{'='*60}")
    print(f"  {nouvelles} nouvelle(s) entrée(s) ajoutée(s)")
    print(f"{'='*60}")
    afficher_dataset()