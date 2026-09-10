import './App.css';
import { useState } from 'react';

function App() {
  // Les états vont ICI
  const [sequence, setSequence] = useState('');
  const [fichier, setFichier]   = useState(null);
  const [resultats, setResultats] = useState(null);
  const [loading, setLoading]   = useState(false);

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
      <p>Protein Binding Site Prediction</p>

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

      <button onClick={analyser}>
      {loading ? 'Analyzing...' : 'Analyze'}
      </button>

      {resultats && (
        <div>
          <h2>Results</h2>
          {resultats.sites.map((site, index) => (
            <div key={index}>
              <h3>Site {index + 1} — {getLabel(site.score)}</h3>
              <p>Score : {(site.score * 100).toFixed(2)}%</p>
              <p>Volume : {site.volume} Å³</p>
              <p>Residues : {site.residus.join(', ')}</p>
            </div>
        ))}
        </div>
)}

    </div>

    
  );
}

export default App