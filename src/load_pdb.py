import requests
import os
import sys
import time
import warnings
from Bio.PDB import PDBParser
from config import DOSSIER_PDB, PROTEINES
warnings.filterwarnings('ignore')

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

def charger_pdbbind_ids(fichier=None):
    """
    Charge les PDB IDs depuis results/pdbbind_ids.txt
    généré par search_pdb.py
    Retourne une liste de PDB IDs propres
    """
    from config import PDBBIND_IDS_OUT
    fichier = fichier or PDBBIND_IDS_OUT

    if not os.path.exists(fichier):
        print(f"Fichier PDBbind introuvable : {fichier}")
        print(f"Lancez d'abord : python src/search_pdb.py")
        return []

    proteines = []
    with open(fichier, 'r') as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith('#'):
                continue
            pdb_id = ligne.split(';')[0].upper()
            proteines.append(pdb_id)

    print(f"{len(proteines)} PDB IDs chargés depuis PDBbind")
    return proteines

def est_deja_telechargee(pdb_id):
    """Vérifie si une structure est déjà téléchargée"""
    return os.path.exists(f"{DOSSIER_PDB}/{pdb_id}.pdb")

def telecharger_pdb(pdb_id, tentatives=3, pause=1):
    """
    Télécharge un fichier PDB depuis RCSB.
    Réessaie automatiquement en cas d'erreur de connexion.
    """

    os.makedirs(DOSSIER_PDB, exist_ok=True)
    filename = f"{DOSSIER_PDB}/{pdb_id}.pdb"
    url      = f"https://files.rcsb.org/download/{pdb_id}.pdb"

    for tentative in range(1, tentatives + 1):
        try:
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                with open(filename, 'w') as f:
                    f.write(response.text)
                time.sleep(pause)  # pause entre chaque téléchargement
                return filename

            else:
                print(f"  Erreur HTTP {response.status_code} — "
                      f"tentative {tentative}/{tentatives}")

        except requests.exceptions.ConnectionError:
            print(f"  Connexion interrompue — "
                  f"tentative {tentative}/{tentatives}")
            time.sleep(pause * tentative)  # pause progressive

        except requests.exceptions.Timeout:
            print(f"  Timeout — tentative {tentative}/{tentatives}")
            time.sleep(pause * tentative)

    print(f"  Échec après {tentatives} tentatives ❌")
    return None

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

def traiter_proteine(pdb_id, i, total, auto=False):
    """
    Gère le téléchargement d'une protéine.
    auto=True → pas de confirmation nécessaire
    """
    print(f"\n[{i}/{total}] {pdb_id}")

    # Déjà téléchargée → skip
    if est_deja_telechargee(pdb_id):
        print(f"  Déjà téléchargée ✅")
        afficher_info(pdb_id)
        return 'ignore'

    # Mode automatique → pas de confirmation
    if auto:
        print(f"  Téléchargement automatique...")
    else:
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

def telecharger_avec_confirmation(proteines, auto=False):
    """Orchestre le téléchargement de toutes les protéines"""
    print(f"\n{'='*50}")
    print(f"  {len(proteines)} protéine(s) à traiter")
    if auto:
        print(f"  Mode : automatique (sans confirmation)")
    print(f"{'='*50}")

    resultats = {}
    for i, pdb_id in enumerate(proteines, 1):
        resultats[pdb_id] = traiter_proteine(
            pdb_id, i, len(proteines), auto=auto
        )

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

if __name__ == "__main__":

    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "--pdbbind":
            print("Mode : PDBbind complet (automatique)")
            proteines = charger_pdbbind_ids()
            # Auto=True → pas de confirmation pour PDBbind
            telecharger_avec_confirmation(proteines, auto=True)

        elif arg == "--pdbbind-batch":
            # Télécharger par lot de BATCH_SIZE
            from config import BATCH_SIZE
            print(f"Mode : PDBbind par lot de {BATCH_SIZE}")
            proteines = charger_pdbbind_ids()
            # Prendre seulement les non-téléchargées
            a_telecharger = [
                p for p in proteines
                if not est_deja_telechargee(p)
            ][:BATCH_SIZE]
            print(f"  {len(a_telecharger)} structures à télécharger ce lot")
            telecharger_avec_confirmation(a_telecharger, auto=True)

        else:
            proteines = charger_liste_externe(arg)
            if not proteines:
                proteines = PROTEINES
            telecharger_avec_confirmation(proteines)

    else:
        print("Mode : config.py (avec confirmation)")
        telecharger_avec_confirmation(PROTEINES)

    verifier_structures(PROTEINES)