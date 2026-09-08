import os
import tempfile
from Bio.PDB import PDBParser
import requests
import subprocess
import json
import numpy
import time
import pickle # Sauvegarder les objets python dans un fichier binaire (XGBoost)
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from features import calculer_features, calculer_sasa_et_volume

class Predictor:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
            'results','model_rf.pkl')

        with open (self.model_path, 'rb') as f:
            self.model = pickle.load(f)

        print("model charché avec succes ✅")

    def predire_structure(self, sequence):
        #Prend en entrée une séquence fasta de protéine et retouse la structure prédite sous format .pdb
        url = "https://api.esmatlas.com/foldSequence/v1/pdb/"
        reponse = requests.post(url, data=sequence)
        if reponse.status_code == 200:
           return reponse.text
        else:
            raise Exception("Erreur ESMFold : structure non générée") 

    def detecter_sites(self, pdb_content):
        # Détecte les cavité dans la structure avec fpocket #
        with tempfile.NamedTemporaryFile(
            suffix='.pdb', mode='w', delete=False

        ) as tmp:
            tmp.write(pdb_content)
            tmp_path = tmp.name

        subprocess.run(['fpocket', '-f', tmp_path], capture_output=True)
        output_dir = tmp_path.replace('.pdb', '_out')
        print(f"output dir : {output_dir}")
        print(f"Existe : {os.path.exists(output_dir)}")
        if os.path.exists(output_dir):
            print(f"Fichiers : {os.listdir(output_dir)}")

        sites = []

        if os.path.exists(output_dir):
            pockets_dir = os.path.join(output_dir, 'pockets')

            if os.path.exists(pockets_dir):
                parser = PDBParser()

                for fichier in os.listdir(pockets_dir):
                    if fichier.endswith('.pdb') :
                        pocket_path = os.path.join(pockets_dir, fichier)
                        structure_pocket = parser.get_structure('pocket', pocket_path)
                        residues = [f"{r.get_resname()}{r.id[1]}"
                                    for r in structure_pocket[0].get_residues()]
                        sites.append({
                                'residues':residues,
                                'volume'  :len(residues)*150.0 # 150 est le volume moyen d'un aa
                                })
        return {'sites': sites}

    def calculer_features(self, binding_residues, structure):
        # alcule des features pour chacune des cavités détectées par DoGSiteScorer
        return calculer_features(binding_residues, structure)

    def predire_scores(self, features):
        # Prédit le score ente 0 et 1 d'un site de laison déttecté
        valeurs = [v for v in features.values()
                    if isinstance(v, (int, float))]

        X = numpy.array(valeurs).reshape(1, -1)
        score = self.model.predict_proba(X)[0][1]
        return score

    def get_residus_biopython(self, structure, residus_str):
        # convertit les strings de résidus en objets BioPython #
        residus_bio = []
        for res in structure[0].get_residues():
            res_id = f"{res.get_resname()}{res.id[1]}"
            if res_id in residus_str:
                residus_bio.append(res)
        return residus_bio

    def predire(self, sequence):
        """
        prend une séquence FASTA, génère la structure 3D de la protéine via ESMFold, 
        envoie cette structure à DoGSiteScorer pour détecter les cavités, 
        calcule les 23 features biophysiques de chaque cavité, 
        utilise le modèle XGBoost pour scorer chaque cavité, et retourne la liste des sites de liaison classés du plus probable au moins probable avec leur score et leurs résidus environnants.
        """
        pdb_content = self.predire_structure(sequence)
        with tempfile.NamedTemporaryFile(
            suffix='.pdb', mode='w', delete=False
            ) as tmp:
            tmp.write(pdb_content)
            tmp_path = tmp.name
        parser    = PDBParser()
        structure = parser.get_structure('prot', tmp_path)

        sites_json = self.detecter_sites(pdb_content)
        resultats = [] 

        for site in sites_json.get('sites', []):
            residus_bio = self.get_residus_biopython(structure, site['residues'])
            features = self.calculer_features(residus_bio, structure)
            if not features:
                continue
            score = self.predire_scores(features)

            resultats.append({
                        'score'   : round(score, 3),
                        'residus' : site['residues'],
                        'volume'  : site.get('volume', 0)
                        })
        resultats.sort(key=lambda x: x['score'], reverse=True)
        return {
                'pdb_content' : pdb_content,
                'sites'       : resultats
                }

if __name__ == "__main__":
    predictor = Predictor()
    sequence  = "PQITLWQRPLVTIKIGGQLKEALLDTGADDTVLEEMSLPGRWKPKMIGGIGGFIKVRQYDQILIEICGHKAIGTVLVGPTPVNIIGRNLLTQIGCTLNF"
    resultats = predictor.predire(sequence)

    print(f"\n{'='*50}")
    print(f"  {len(resultats['sites'])} sites de liaison détectés")
    print(f"{'='*50}")

    for i, site in enumerate(resultats['sites'], 1):
        print(f"\n  Site {i} :")
        print(f"  Score          : {site['score']*100:.2f}%")
        print(f"  Volume         : {site['volume']:.1f} Å³")
        print(f"  Résidus ({len(site['residus'])}) : {', '.join(site['residus'][:5])}...")