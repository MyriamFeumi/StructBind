import requests
import os
import sys
import warnings
from Bio.PDB import PDBParser
from config import DOSSIER_PDB, PROTEINES
warnings.filterwarnings('ignore')

# ─── Fonctions utilitaires ────────────────────────────────────────

def charger_liste_externe(fichier):
    """
    Charge une liste de PDB IDs depuis un fichier texte externe.
    Format : un PDB ID par ligne, commentaires avec #
    """
    if not os.path.exists(fichier):
        print(f"Fichier '{fichier}' introuvable.")
        return []

    proteines = []
    with open(fichier, 'r') as f:
        for ligne in f:
            ligne = ligne.strip()
            if ligne and not ligne.startswith('#'):
                proteines.append(ligne.upper())

    print(f"{len(proteines)} protéines chargées depuis '{fichier}'")
    return proteines

def est_deja_telechargee(pdb_id):
    """Vérifie si une structure est déjà téléchargée"""
    return os.path.exists(f"{DOSSIER_PDB}/{pdb_id}.pdb")

def telecharger_pdb(pdb_id):
    """Télécharge un fichier PDB depuis RCSB et le sauvegarde"""
    os.makedirs(DOSSIER_PDB, exist_ok=True)
    filename = f"{DOSSIER_PDB}/{pdb_id}.pdb"
    url      = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"  Erreur : {pdb_id} introuvable sur RCSB")
        return None

    with open(filename, 'w') as f:
        f.write(response.text)

    return filename

def load_structure(pdb_id):
    """
    Charge et retourne une structure BioPython.
    Utilisée par extract_ligand.py et features.py
    """
    filename = f"{DOSSIER_PDB}/{pdb_id}.pdb"

    if not os.path.exists(filename):
        print(f"  Structure {pdb_id} introuvable → lancez load_pdb.py")
        return None

    parser = PDBParser()
    return parser.get_structure(pdb_id, filename)

def afficher_info(pdb_id):
    """Affiche les informations de base d'une structure"""
    structure = load_structure(pdb_id)
    if not structure:
        return

    model = structure[0]
    print(f"  Chaines : {len(list(model.get_chains()))}")
    print(f"  Résidus : {len(list(model.get_residues()))}")
    print(f"  Atomes  : {len(list(model.get_atoms()))}")

def traiter_proteine(pdb_id, i, total):
    """
    Gère le téléchargement d'une protéine avec confirmation.
    Retourne : 'succes', 'ignore', 'erreur'
    """
    print(f"\n[{i}/{total}] {pdb_id}")

    # Déjà téléchargée → afficher infos et passer
    if est_deja_telechargee(pdb_id):
        print(f"  Déjà téléchargée ✅")
        afficher_info(pdb_id)
        return 'ignore'

    # Demander confirmation
    reponse = input(f"  Télécharger {pdb_id} ? (o/n) : ").strip().lower()

    if reponse != 'o':
        print(f"  Ignorée ⏭️")
        return 'ignore'

    # Télécharger
    filename = telecharger_pdb(pdb_id)
    if not filename:
        return 'erreur'

    print(f"  Téléchargée ✅")
    afficher_info(pdb_id)
    return 'succes'

def afficher_resume(resultats):
    """Affiche le résumé final des téléchargements"""
    succes  = [p for p, r in resultats.items() if r == 'succes']
    ignores = [p for p, r in resultats.items() if r == 'ignore']
    erreurs = [p for p, r in resultats.items() if r == 'erreur']

    print(f"\n{'='*50}")
    print(f"  Résumé")
    print(f"{'='*50}")
    print(f"  Téléchargées   : {len(succes)}  → {succes}")
    print(f"  Déjà présentes : {len(ignores)} → {ignores}")
    print(f"  Erreurs        : {len(erreurs)} → {erreurs}")
    print(f"{'='*50}")

def telecharger_avec_confirmation(proteines):
    """Orchestre le téléchargement de toutes les protéines"""
    print(f"\n{'='*50}")
    print(f"  {len(proteines)} protéine(s) à traiter")
    print(f"{'='*50}")

    resultats = {}
    for i, pdb_id in enumerate(proteines, 1):
        resultats[pdb_id] = traiter_proteine(pdb_id, i, len(proteines))

    afficher_resume(resultats)
    return resultats

def verifier_structures(proteines):
    """Vérifie que toutes les structures se chargent correctement"""
    print(f"\nVérification des structures :")
    print(f"{'='*50}")
    for pdb_id in proteines:
        structure = load_structure(pdb_id)
        statut    = "✅" if structure else "❌"
        print(f"  {pdb_id} → {statut}")

# ─── Point d'entrée ───────────────────────────────────────────────

if __name__ == "__main__":

    # Fichier externe fourni ? → priorité sur config.py
    if len(sys.argv) > 1:
        fichier   = sys.argv[1]
        proteines = charger_liste_externe(fichier)
        if not proteines:
            print("Fichier vide → utilisation de config.py")
            proteines = PROTEINES
    else:
        proteines = PROTEINES

    # Téléchargement
    telecharger_avec_confirmation(proteines)

    # Vérification finale
    verifier_structures(proteines)