from pydantic import BaseModel, validator

"""
Décrit la structure des séquences entrées : 
utilise AlphaFold pour les séquences protéiques existantes
et EmsFold pour des nouvelles protéines
"""

"""
X → acide aminé inconnu
    (on ne sait pas lequel)

B → ASN ou ASP (ambiguïté)
Z → GLN ou GLU (ambiguïté)
J → LEU ou ILE (ambiguïté)

U → Sélénocystéine (rare)
O → Pyrrolysine (très rare)
"""
liste_aa = ('A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N', 'P', 
      'Q', 'R', 'S', 'T', 'V', 'W', 'Y', 'X', 'B', 'Z', 'J', 'U', 'O')

class PredictRequest(BaseModel):
    sequence : str

    @validator('sequence')
    def valider_sequence(cls, v):
        if v[0] == '>':
            lignes = v.split("\n")
            sequenceAA  = "".join(lignes[1:])
            sequenceAA = sequenceAA.upper()
        else:
            sequenceAA = v.upper()

        if len(sequenceAA) < 10:
            raise ValueError("Séquence trop courte")

        for aa in sequenceAA:
            if aa not in liste_aa:
                raise ValueError(f"Caractère invalide : {aa}")

        return sequenceAA
    
class  SiteResult(BaseModel):
    site_id : int
    score : float
    residus : list
    

class PredictResponse(BaseModel):
    sites : list[SiteResult]
    temps : float
    