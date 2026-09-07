import json
import sys

sys.setrecursionlimit(100000)  # augmenter la limite

fichier = "results/ligands.json"

# Lire le contenu brut
with open(fichier, 'r', encoding='utf-8') as f:
    contenu = f.read()

# Trouver toutes les clés PDB valides
resultats = {}
position  = 0

while True:
    # Chercher le prochain PDB ID
    debut = contenu.find('"', position)
    if debut == -1:
        break

    fin = contenu.find('"', debut + 1)
    if fin == -1:
        break

    cle = contenu[debut+1:fin]

    # Vérifier que c'est un PDB ID (4 caractères)
    if len(cle) == 4 and cle.isalnum():
        # Chercher le début du tableau
        debut_array = contenu.find('[', fin)
        if debut_array == -1:
            break

        # Chercher la fin du tableau
        # On compte les crochets ouverts/fermés
        profondeur = 0
        i          = debut_array

        for i in range(debut_array, len(contenu)):
            if contenu[i] == '[':
                profondeur += 1
            elif contenu[i] == ']':
                profondeur -= 1
                if profondeur == 0:
                    break

        fin_array = i
        try:
            valeur = json.loads(contenu[debut_array:fin_array+1])
            resultats[cle] = valeur
            position = fin_array + 1
        except:
            position = fin + 1
    else:
        position = fin + 1

print(f"Proteines recuperees : {len(resultats)}")

if len(resultats) > 0:
    with open('results/ligands_repare.json', 'w') as f:
        json.dump(resultats, f, indent=2)
    print(f"Sauvegarde → results/ligands_repare.json ✅")