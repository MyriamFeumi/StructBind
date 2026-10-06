import './App.css';
import { useState } from 'react';
import { useAnalyser } from './hooks/useAnalyser';
import { getCouleurSite } from './utils/scores';
import SitesTable from './components/SitesTable';

function App() {
  const {
    sequence, setSequence,
    resultats,
    loading,
    nomProteine,
    selectedSite, setSelectedSite,
    etape,
    viewerRef,
    analyser,
  } = useAnalyser();

  const visualiserSite = (site) => {
    if (!viewerRef.current) return;
    const numerosResidus = site.residus.map(r => parseInt(r.replace(/[A-Z]/g, '')));
    const couleur = getCouleurSite(site.score);
    const viewer = window.$3Dmol.createViewer(viewerRef.current, { backgroundColor: '#16213e' });
    viewer.addModel(resultats.pdb_content, 'pdb');
    viewer.setStyle({}, { cartoon: { color: 'grey' } });
    viewer.setStyle(
      { resi: numerosResidus },
      { cartoon: { color: couleur }, stick: { color: couleur } }
    );
    viewer.zoomTo({ resi: numerosResidus });
    viewer.render();
  };

  const reinitialiser = () => {
    const viewer = window.$3Dmol.createViewer(viewerRef.current, { backgroundColor: '#16213e' });
    viewer.addModel(resultats.pdb_content, 'pdb');
    viewer.setStyle({}, { cartoon: { color: 'spectrum' } });
    viewer.zoomTo();
    viewer.render();
  };

  return (
    <div className="App">
      <h1>🧬 StructBind</h1>
      <p>Prédiction des sites de liaison des protéines et identification des médicaments potentiels</p>

      <textarea
        placeholder=">MyProtein&#10;MKTAYIAKQR..."
        value={sequence}
        onChange={(e) => setSequence(e.target.value)}
      />

      <p>── OU ──</p>

      <input
        type="file"
        accept=".fasta,.fa,.txt"
        onChange={(e) => {
          const file = e.target.files[0];
          if (file) {
            const reader = new FileReader();
            reader.onload = (event) => { setSequence(event.target.result); };
            reader.readAsText(file);
          }
        }}
      />

      <br /><button onClick={analyser}>
        {loading ? 'Analyzing...' : 'Analyser'}
      </button>

      {loading && etape && (
        <div className="etape-indicator">
          <p>{etape}</p>
        </div>
      )}

      {resultats && (
        <div>
          <h2>Résultats</h2>

          {resultats.pdb_content ? (
            <>
              <p className="protein-title">
                {nomProteine}<br /><br /><strong>Structure 3D</strong>
                <button className="reset-btn" onClick={reinitialiser}>
                  → réinitialiser structure
                </button>
              </p>

              <div className="results-container">
                <div className="viewer-panel">
                  <div
                    id="viewer3d"
                    ref={viewerRef}
                    style={{ width: '100%', height: '500px', position: 'relative' }}
                  />
                </div>

                <div className="results-panel">
                  {(!resultats.sites || resultats.sites.length === 0) ? (
                    <p>Aucun site de liaison prédit pour cette protéine.</p>
                  ) : (
                    <SitesTable
                      resultats={resultats}
                      nomProteine={nomProteine}
                      selectedSite={selectedSite}
                      setSelectedSite={setSelectedSite}
                      visualiserSite={visualiserSite}
                    />
                  )}
                </div>
              </div>
            </>
          ) : (
            <p>⚠️ La structure 3D n'a pas pu être prédite pour cette séquence.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default App;