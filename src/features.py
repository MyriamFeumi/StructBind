import csv
import json
import math
import os
import warnings
from Bio.PDB import PDBParser
from Bio.PDB.SASA import ShrakeRupley

from config import (
    PROTEINES, DATASET_CSV, LIGANDS_JSON,
    DOSSIER_PDB, RAYON_SITE_LIAISON,
    HYDROPHOBICITE, CHARGE, 
    AA_AROMATIQUES, AA_HYDROPHOBES,
    AA_DONNEURS_H, AA_ACCEPTEURS_H,
    AA_POLAIRES, AA_CHARGES,
    AA_PETITS, AA_GRANDS,
    AA_POSITIFS, AA_NEGATIFS,   
    AA_FLEXIBLES, AA_CYSTEINE             
)
from load_pdb import load_structure
from extract_ligand import find_binding_site, get_residues

warnings.filterwarnings('ignore')

# Fonctions utilitaires

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

    if not os.path.exists(DATASET_CSV):
        with open(DATASET_CSV, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([
                'pdb_id', 'ligand', 'tag',
                'taille', 'hydrophobicite',
                'charge_nette', 'bfactor',
                'ratio_aromatique', 'ratio_hydrophobe',
                'ratio_donneurs_h', 'ratio_accepteurs_h',
                'ratio_polaire', 'ratio_charge',
                'ratio_petits', 'ratio_grands', 
                'diversite_aa',
                'ratio_positif', 'ratio_negatif',
                'ratio_flexible', 'ratio_cysteine',
                'hydro_max', 'hydro_min',
                'charge_absolue', 
                'sasa_totale', 'sasa_moy', 'volume',
                'label'
            ])
        print(f"Dataset initialisé → {DATASET_CSV} ✅")

def sauvegarder_features(pdb_id, ligand, tag, features, geo, label=1):
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
            features['ratio_polaire'],
            features['ratio_charge'],
            features['ratio_petits'],
            features['ratio_grands'],
            features['diversite_aa'],
            features['ratio_positif'],
            features['ratio_negatif'],
            features['ratio_flexible'],
            features['ratio_cysteine'],
            features['hydro_max'],
            features['hydro_min'],
            features['charge_absolue'],
            geo['sasa_totale'],           
            geo['sasa_moy'],
            geo['volume'],
            label
        ])

def calculer_features(binding_residues):
    """Calcule 12 features biophysiques d'un site de liaison"""
    nb_petits = 0
    nb_grands  = 0
    nb_positifs  = 0
    nb_negatifs  = 0
    nb_flexibles = 0
    nb_cysteine  = 0
    hydro_list   = []

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
    nb_polaires     = 0
    nb_charges      = 0

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
        if resname in AA_POLAIRES     : nb_polaires     += 1
        if resname in AA_CHARGES      : nb_charges      += 1
        if resname in AA_PETITS       : nb_petits       += 1
        if resname in AA_GRANDS       : nb_grands       += 1
        if resname in AA_POSITIFS  : nb_positifs  += 1
        if resname in AA_NEGATIFS  : nb_negatifs  += 1
        if resname in AA_FLEXIBLES : nb_flexibles += 1
        if resname in AA_CYSTEINE  : nb_cysteine  += 1

    n = len(binding_residues)

    # Calcul de l'écart-type des B-factors
    bfactor_moy = sum(b_factors) / len(b_factors)
    bfactor_std = round(
        (sum((b - bfactor_moy)**2 for b in b_factors)
         / len(b_factors)) ** 0.5, 2
    )

    # Calcul de la diversité des acides aminés
    # Entropie de Shannon normalisée
    total_residus = sum(composition.values())
    entropie = 0
    for count in composition.values():
        p = count / total_residus
        if p > 0:
            entropie -= p * math.log2(p)
    # Normaliser entre 0 et 1
    max_entropie  = math.log2(20)  # 20 acides aminés possibles
    diversite_aa  = round(entropie / max_entropie, 3)

    return {
        # Features existantes
        'taille'            : n,
        'hydrophobicite_moy': round(sum(hydro_values) / n, 3),
        'charge_nette'      : round(charge_totale, 2),
        'bfactor_moy'       : round(bfactor_moy, 2),
        'ratio_aromatique'  : round(nb_aromatiques  / n, 3),
        'ratio_hydrophobe'  : round(nb_hydrophobes  / n, 3),
        'ratio_donneurs_h'  : round(nb_donneurs_h   / n, 3),
        'ratio_accepteurs_h': round(nb_accepteurs_h / n, 3),

        'ratio_polaire'     : round(nb_polaires / n, 3),
        'ratio_charge'      : round(nb_charges  / n, 3),

        'ratio_petits'      : round(nb_petits / n, 3),
        'ratio_grands'      : round(nb_grands  / n, 3),
        'ratio_positif'  : round(nb_positifs  / n, 3),
        'ratio_negatif'  : round(nb_negatifs  / n, 3),
        'ratio_flexible' : round(nb_flexibles / n, 3),
        'ratio_cysteine' : round(nb_cysteine  / n, 3),
        'hydro_max'      : round(max(hydro_values), 3),
        'hydro_min'      : round(min(hydro_values), 3),
        'charge_absolue' : round(sum(abs(CHARGE.get(r.get_resname(), 0))
                   for r in binding_residues), 2),
        'diversite_aa'      : diversite_aa,
        'composition'       : composition,
        'sasa_totale' : 0.0,
        'sasa_moy'    : 0.0,
        'volume'      : 0.0
    }

def calculer_sasa_et_volume(structure, binding_residues):
    """
    Calcule la SASA et le volume estimé du site de liaison
    en utilisant ShrakeRupley (BioPython)
    """

    try:
        # Calculer la SASA pour toute la structure
        sr = ShrakeRupley()
        sr.compute(structure, level="R")

        sasa_totale = 0
        for res in binding_residues:
            # Récupérer la SASA calculée pour ce résidu
            sasa_totale += res.sasa

        n = len(binding_residues)
        sasa_moy = sasa_totale / n if n > 0 else 0

        # Estimation du volume par comptage d'atomes
        # Rayon de Van der Waals moyen = 1.8 Å
        # Volume sphère = 4/3 × π × r³
        nb_atomes = sum(len(list(r.get_atoms())) for r in binding_residues)
        volume_estime = round(nb_atomes * (4/3) * math.pi * (1.8**3), 2)

        return {
            'sasa_totale' : round(sasa_totale, 2),
            'sasa_moy'    : round(sasa_moy, 2),
            'volume'      : volume_estime
        }

    except Exception as e:
        return {
            'sasa_totale' : 0.0,
            'sasa_moy'    : 0.0,
            'volume'      : 0.0
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
    """Recharge la structure et recalcule les résidus + SASA + volume"""
    structure = load_structure(pdb_id)
    if not structure:
        return None, None

    all_ligands = get_residues(structure, 'ligand')
    ligand_obj  = next(
        (l for l in all_ligands
         if l.get_resname() == ligand_data['resname']),
        None
    )

    if not ligand_obj:
        return None, None

    binding_residues = find_binding_site(structure, ligand_obj)

    # Calculer SASA et volume
    geo = calculer_sasa_et_volume(structure, binding_residues)

    return binding_residues, geo

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

            # Recalculer les résidus + géométrie
            binding_residues, geo = recuperer_residus_depuis_structure(
                pdb_id, ligand_data
            )

            if not binding_residues or not geo:
                continue

            # Calculer + sauvegarder
            features = calculer_features(binding_residues)
            if not features:
                continue

            afficher_features(pdb_id, resname, features)
            sauvegarder_features(pdb_id, resname, tag, features, geo)
            deja_traites.add(cle)
            nouvelles += 1

    # Résumé
    print(f"\n{'='*60}")
    print(f"  {nouvelles} nouvelle(s) entrée(s) ajoutée(s)")
    print(f"{'='*60}")
    afficher_dataset()