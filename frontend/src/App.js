import './App.css';
import { useState } from 'react';
import { useEffect, useRef } from 'react';

function App() {
  // Les états vont ICI
  const [sequence, setSequence] = useState('');
  const [fichier, setFichier]   = useState(null);
  const [resultats, setResultats] = useState(null);
  const [loading, setLoading]   = useState(false);
  const viewerRef = useRef(null);
  const getTitreClass = (score) => {
  if (score >= 0.90) return "titre-principal";
  if (score >= 0.80) return "titre-tres-bon";
  if (score >= 0.60) return "titre-bon";
  if (score >= 0.40) return "titre-possible";
  return "titre-fausse";
};

  useEffect(() => {
    if (resultats && viewerRef.current) {
      viewerRef.current.innerHTML = '';
    
    // Créer le viewer 3Dmol
      const viewer = window.$3Dmol.createViewer(
        viewerRef.current,
        { backgroundColor: '#16213e' }
      );

    // Charger la structure .pdb
      viewer.addModel(resultats.pdb_content, 'pdb');

    // Style cartoon pour la protéine
      viewer.setStyle({}, { cartoon: { color: 'spectrum' } });

    // Rendu
        viewer.zoomTo();
    viewer.render();
    }
}, [resultats]);

  const analyser = async () => {
  setLoading(true);
  try {
    const response = await fetch('http://127.0.0.1:8000/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sequence: sequence })
    });
    const data = await response.json();
    setResultats(data);
  } catch (error) {
    console.error('Erreur:', error);
  }
  setLoading(false);
  };

  const getLabel = (score) => {
  if (score >= 0.90) return "Site principal";
  if (score >= 0.80) return "Très bon site";
  if (score >= 0.60) return "Bon site";
  if (score >= 0.40) return "Site possible";
  return "fausse cavité";
  };

  return (
    <div className="App">

      {/* Titre */}
      <h1>🧬 StructBind</h1>
      <p>Prédiction des siites de liaison des protéines et identification des médicaments potentiels</p>

      {/* Zone de texte */}
     <textarea
      placeholder=">MyProtein&#10;MKTAYIAKQR..."
      value={sequence}
      onChange={(e) => setSequence(e.target.value)}
    />

      <p>── OU ──</p>

      {/* Charger un fichier */}
      <input 
        type="file" 
        accept=".fasta,.fa,.txt"
        onChange={(e) => {
          const file = e.target.files[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
            setSequence(event.target.result);
          };
      reader.readAsText(file);
          }
        }}
      />

      <br/><button onClick={analyser}>
      {loading ? 'Analyzing...' : 'Analiser'}
      </button>

      {resultats && resultats.sites && (
  <div> 
  <h2>Résultats</h2>
  <div className="results-container">

    {/* Panneau gauche — Visualisation 3D */}
  <div className="viewer-panel">
    <div
      id="viewer3d"
      ref={viewerRef}
      style={{ width: '100%', height: '100%', position: 'relative' }}
    />
  </div>

    {/* Panneau droit — Résultats */}
    <div className="results-panel">
      <h2>Sites prédits</h2>
      {resultats.sites && resultats.sites.map((site, index) => (
        <div key={index} className= "site-card" >

          <h3 className={getTitreClass(site.score)}>
            Site {index + 1} — {getLabel(site.score)}
          </h3>
          <p className="score">
            Score : {(site.score * 100).toFixed(2)}%
          </p>
          <p>Volume : {site.volume} Å³</p>
          <p className="residus">
              Residues : {site.residus.join(', ')}
            </p>
        </div>
      ))}
    </div>

  </div>
  </div>
)}

    </div>

    
  );
}

export default App