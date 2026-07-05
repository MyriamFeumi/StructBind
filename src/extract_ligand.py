import requests
import json
import os
import warnings
from Bio.PDB import NeighborSearch
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

from config import (
    PROTEINES, RAYON_SITE_LIAISON,
    ATOMES_MIN_LIGAND, POIDS_MIN_LIGAND,
    NUCLEOTIDES_NATURELS, NON_DRUG_TYPES,
    LIGANDS_JSON
)
from load_pdb import load_structure

warnings.filterwarnings('ignore')

# ─── Fonctions utilitaires ────────────────────────────────────────

def charger_resultats_existants():
    """Charge les résultats déjà traités depuis le fichier JSON"""
    if os.path.exists(LIGANDS_JSON):
        with open(LIGANDS_JSON, 'r') as f:
            return json.load(f)
    return {}

def sauvegarder_resultats(resultats):
    """Sauvegarde tous les résultats dans le fichier JSON"""
    with open(LIGANDS_JSON, 'w') as f:
        json.dump(resultats, f, indent=2)

def get_residues(structure, residue_type='protein'):
    """
    Retourne les résidus selon leur type :
    - protein : acides aminés standards
    - ligand  : molécules non-eau (HETATM)
    - water   : molécules d'eau (HOH)
    """
    all_residues = list(structure[0].get_residues())

    if residue_type == 'protein':
        return [r for r in all_residues if r.id[0] == ' ']

    elif residue_type == 'ligand':
        return [r for r in all_residues
                if r.id[0] != ' '
                and r.get_resname() != 'HOH']

    elif residue_type == 'water':
        return [r for r in all_residues
                if r.get_resname() == 'HOH']

    else:
        print(f"Type inconnu : {residue_type}")
        return []

def get_ligand_info(resname):
    """Interroge RCSB pour obtenir les détails + SMILES du ligand"""
    url = f"https://data.rcsb.org/rest/v1/core/chemcomp/{resname}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            comp = data.get('chem_comp', {})
            smiles = None
            for d in data.get('pdbx_chem_comp_descriptor', []):
                if d.get('type') == 'SMILES':
                    smiles = d.get('descriptor')
                    break
            return {
                'nom'    : comp.get('name', 'Inconnu'),
                'type'   : comp.get('type', 'Inconnu'),
                'poids'  : comp.get('formula_weight', 0),
                'formule': comp.get('formula', 'Inconnue'),
                'smiles' : smiles
            }
    except:
        pass
    return None

def calculer_proprietes(smiles):
    """Calcule LogP, HBD, HBA depuis le SMILES avec RDKit"""
    if not smiles:
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            return {
                'logP': round(Descriptors.MolLogP(mol), 2),
                'hbd' : rdMolDescriptors.CalcNumHBD(mol),
                'hba' : rdMolDescriptors.CalcNumHBA(mol),
            }
    except:
        pass
    return None

def compter_violations_ro5(mw, logP, hbd, hba):
    """Compte les violations Ro5 — informatif seulement"""
    violations = 0
    if mw   > 500: violations += 1
    if logP > 5  : violations += 1
    if hbd  > 5  : violations += 1
    if hba  > 10 : violations += 1
    return violations

def classifier_ligand(resname, n_atoms, info, props):
    """Classifie un ligand selon son profil pharmacologique"""
    if not info:
        return "Données introuvables", "inconnu", False

    mol_type = info.get('type', '').lower()
    mw       = info.get('poids', 0)

    # Briques du vivant
    if mol_type in NON_DRUG_TYPES:
        return f"Non-thérapeutique ({info['type']})", "non_drug", False

    # Nucléotides naturels
    if resname in NUCLEOTIDES_NATURELS:
        return "Nucléotide naturel (cofacteur)", "non_drug", False

    # Trop petit
    if n_atoms < ATOMES_MIN_LIGAND or mw < POIDS_MIN_LIGAND:
        return f"Trop petit ({n_atoms} atomes, {mw} Da)", "non_drug", False

    # Macromolécule
    if mw > 2000:
        return f"Macromolécule ({mw} Da)", "macro", True

    # Calcul violations Ro5
    violations = 0
    if props:
        violations = compter_violations_ro5(
            mw, props['logP'], props['hbd'], props['hba']
        )

    # Oral drug-like
    if mw <= 500 and violations == 0:
        return "Oral drug-like (Ro5)", "ro5", True

    # Injectable / bRo5
    return (f"Injectable / bRo5 "
            f"({violations} violation(s), {mw} Da)"), "bro5", True

def find_binding_site(structure, ligand):
    """Trouve les résidus protéiques autour du ligand"""
    protein_atoms = [
        atom
        for res in get_residues(structure, 'protein')
        for atom in res
    ]
    ns = NeighborSearch(protein_atoms)

    binding_residues = set()
    for atom in ligand:
        nearby = ns.search(atom.coord, RAYON_SITE_LIAISON, 'R')
        binding_residues.update(nearby)

    return list(binding_residues)

def traiter_proteine(pdb_id, structure):
    """Traite une protéine et retourne ses ligands valides"""
    ligands         = get_residues(structure, 'ligand')
    ligands_valides = []

    print(f"\n  Ligands trouvés : {len(ligands)}")
    print(f"  {'-'*40}")

    for lig in ligands:
        resname = lig.get_resname()
        n_atoms = len(list(lig.get_atoms()))
        info    = get_ligand_info(resname)
        props   = calculer_proprietes(
            info.get('smiles') if info else None
        )
        categorie, tag, est_valide = classifier_ligand(
            resname, n_atoms, info, props
        )

        violations = 0
        if props and info:
            violations = compter_violations_ro5(
                info['poids'], props['logP'],
                props['hbd'], props['hba']
            )

        # Affichage
        verdict = "Valide ✅" if est_valide else "Rejeté ❌"
        print(f"\n  Ligand  : {resname}")
        if info:
            print(f"    Nom     : {info['nom'][:50]}")
            print(f"    Formule : {info['formule']}")
            print(f"    Poids   : {info['poids']} Da")
        if props:
            print(f"    LogP    : {props['logP']} (informatif)")
            print(f"    HBD/HBA : {props['hbd']} / {props['hba']}")
            print(f"    Ro5     : {violations} violation(s)")
        print(f"    Classe  : {categorie}")
        print(f"    Verdict : {verdict}")

        if est_valide:
            binding_residues = find_binding_site(structure, lig)
            residus_liste    = [
                {
                    'nom'   : r.get_resname(),
                    'numero': r.id[1],
                    'chaine': r.get_parent().id
                }
                for r in sorted(
                    binding_residues, key=lambda r: r.id[1]
                )
            ]

            print(f"\n    Site de liaison "
                  f"({len(residus_liste)} résidus) :")
            for r in residus_liste:
                print(f"      → {r['nom']} {r['numero']} "
                      f"(chaîne {r['chaine']})")

            ligands_valides.append({
                'resname'         : resname,
                'tag'             : tag,
                'categorie'       : categorie,
                'poids'           : info['poids'] if info else 0,
                'logP'            : props['logP'] if props else None,
                'violations_ro5'  : violations,
                'binding_residues': residus_liste
            })

    return ligands_valides

def afficher_resume(resultats):
    """Affiche un résumé de toutes les protéines traitées"""
    print(f"\n{'='*60}")
    print(f"  RÉSUMÉ GLOBAL")
    print(f"{'='*60}")
    for pdb_id, ligands in resultats.items():
        print(f"\n  {pdb_id} → {len(ligands)} ligand(s) valide(s)")
        for lig in ligands:
            print(f"    [{lig['tag'].upper()}] {lig['resname']} "
                  f"— {len(lig['binding_residues'])} résidus")
    print(f"\n  Résultats sauvegardés → {LIGANDS_JSON} ✅")

# ─── Point d'entrée ───────────────────────────────────────────────

if __name__ == "__main__":

    # Charger les résultats déjà traités
    resultats    = charger_resultats_existants()
    deja_traites = set(resultats.keys())

    print(f"Protéines déjà traitées : {len(deja_traites)}")
    print(f"Protéines à traiter     : "
          f"{len([p for p in PROTEINES if p not in deja_traites])}")

    for pdb_id in PROTEINES:

        if pdb_id in deja_traites:
            print(f"\n[{pdb_id}] Déjà traité ✅ — ignoré")
            continue

        print(f"\n{'='*60}")
        print(f"  Traitement de {pdb_id}")
        print(f"{'='*60}")

        structure = load_structure(pdb_id)
        if not structure:
            print(f"  Structure introuvable → lancez load_pdb.py d'abord")
            continue

        ligands_valides   = traiter_proteine(pdb_id, structure)
        resultats[pdb_id] = ligands_valides
        sauvegarder_resultats(resultats)

    afficher_resume(resultats)