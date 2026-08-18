import os
import re
from config import DOSSIER_RESULTS, PDBBIND_INDEX, PDBBIND_IDS_OUT


# ─── Fonctions ────────────────────────────────────────────────────

def parser_ligne(ligne):
    """
    Parse une ligne du fichier PDBbind.
    Format : PDB_ID  resolution  year  affinity  // ref (ligand)

    Retourne un dictionnaire ou None si la ligne est invalide.
    """
    # Ignorer les commentaires et lignes vides
    ligne = ligne.strip()
    if not ligne or ligne.startswith('#'):
        return None

    parties = ligne.split()
    if len(parties) < 4:
        return None

    pdb_id     = parties[0].upper()
    resolution = parties[1]
    affinity   = parties[3] if len(parties) > 3 else None

    # Extraire le nom du ligand entre parenthèses
    ligand = None
    match = re.search(r'\(([^)]+)\)', ligne)
    if match:
        ligand = match.group(1)

    return {
        'pdb_id'    : pdb_id,
        'resolution': resolution,
        'affinity'  : affinity,
        'ligand'    : ligand,
        'ligne'     : ligne
    }

def est_valide(entry, resolution_max=2.5):
    """
    Vérifie si une entrée PDBbind est utilisable
    pour entraîner notre modèle.
    """
    if not entry:
        return False, "ligne invalide"

    resolution = entry['resolution']
    affinity   = entry['affinity']
    ligne      = entry['ligne']

    # Exclure les structures NMR (pas de résolution numérique)
    if resolution.upper() == 'NMR':
        return False, "NMR"

    # Exclure les structures sans résolution numérique
    try:
        res_val = float(resolution)
    except ValueError:
        return False, "résolution invalide"

    # Filtrer par résolution
    if res_val > resolution_max:
        return False, f"résolution {res_val}Å > {resolution_max}Å"

    # Exclure les structures incomplètes
    if 'incomplete' in ligne.lower():
        return False, "structure incomplète"

    # Exclure les complexes covalents (liaison différente)
    if 'covalent' in ligne.lower():
        return False, "complexe covalent"

    # Vérifier qu'on a une affinité mesurée
    if not affinity:
        return False, "pas d'affinité"

    if '<' in affinity or '~' in affinity:
        return False, "affinité approximative"

    return True, "ok"

def lire_pdbbind(fichier, resolution_max=2.5):
    """
    Lit le fichier PDBbind et retourne les entrées valides.
    """
    if not os.path.exists(fichier):
        print(f"Fichier introuvable : {fichier}")
        return []

    entrees_valides  = []
    entrees_totales  = 0
    raisons_rejet    = {}

    with open(fichier, 'r') as f:
        for ligne in f:
            entry = parser_ligne(ligne)
            if not entry:
                continue

            entrees_totales += 1
            valide, raison  = est_valide(entry, resolution_max)

            if valide:
                entrees_valides.append(entry)
            else:
                raisons_rejet[raison] = raisons_rejet.get(raison, 0) + 1

    # Résumé du filtrage
    print(f"\nFichier : {fichier}")
    print(f"{'='*50}")
    print(f"  Total lu          : {entrees_totales}")
    print(f"  Valides           : {len(entrees_valides)}")
    print(f"  Rejetés           : {entrees_totales - len(entrees_valides)}")
    print(f"\n  Raisons de rejet :")
    for raison, count in sorted(raisons_rejet.items(),
                                 key=lambda x: -x[1]):
        print(f"    {raison:<30} : {count}")

    return entrees_valides

def sauvegarder_ids(entrees, fichier_sortie):
    """
    Sauvegarde les PDB IDs valides dans un fichier texte.
    Format : PDB_ID;resolution;affinity;ligand
    """
    os.makedirs(os.path.dirname(fichier_sortie), exist_ok=True)

    with open(fichier_sortie, 'w') as f:
        f.write("# PDB IDs valides extraits de PDBbind\n")
        f.write("# Format : pdb_id;resolution;affinity;ligand\n")
        for entry in entrees:
            f.write(f"{entry['pdb_id']};"
                    f"{entry['resolution']};"
                    f"{entry['affinity']};"
                    f"{entry['ligand']}\n")

    print(f"\n  IDs sauvegardés → {fichier_sortie} ✅")

def afficher_exemples(entrees, n=5):
    """Affiche quelques exemples d'entrées valides"""
    print(f"\n  Exemples ({n} premières entrées valides) :")
    print(f"  {'-'*50}")
    for entry in entrees[:n]:
        print(f"    {entry['pdb_id']}  "
              f"res={entry['resolution']}Å  "
              f"affinité={entry['affinity']}  "
              f"ligand={entry['ligand']}")

# ─── Point d'entrée ───────────────────────────────────────────────

if __name__ == "__main__":

    print("Lecture du fichier PDBbind...")

    # Lire et filtrer
    entrees = lire_pdbbind(PDBBIND_INDEX, resolution_max=2.5)

    # Afficher des exemples
    afficher_exemples(entrees)

    # Sauvegarder
    sauvegarder_ids(entrees, PDBBIND_IDS_OUT)

    print(f"\n  Ces {len(entrees)} structures seront utilisées")
    print(f"  pour entraîner notre modèle IA.")