import './App.css';
import { useState } from 'react';
import { useEffect, useRef } from 'react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

const API_URL = process.env.REACT_APP_API_URL || 'https://structbind.onrender.com';

function App() {
  const [sequence, setSequence]   = useState('');
  const [resultats, setResultats] = useState(null);
  const [loading, setLoading]     = useState(false);
  const [nomProteine, setNomProteine] = useState('');
  const viewerRef = useRef(null);
  const [selectedSite, setSelectedSite] = useState(null);
  const [etape, setEtape] = useState('');
  const [, setSiteVisualise] = useState(null);

  const getTitreClass = (score) => {
    if (score >= 0.90) return "titre-principal";
    if (score >= 0.80) return "titre-tres-bon";
    if (score >= 0.60) return "titre-bon";
    if (score >= 0.40) return "titre-possible";
    return "titre-fausse";
  };

  const getLabel = (score) => {
    if (score >= 0.90) return "Site principal";
    if (score >= 0.80) return "Très bon site";
    if (score >= 0.60) return "Bon site";
    if (score >= 0.40) return "Site possible";
    return "Fausse cavité";
  };

  useEffect(() => {
    if (resultats && resultats.pdb_content && viewerRef.current) {
      viewerRef.current.innerHTML = '';
      const viewer = window.$3Dmol.createViewer(
        viewerRef.current,
        { backgroundColor: '#16213e' }
      );
      viewer.addModel(resultats.pdb_content, 'pdb');
      viewer.setStyle({}, { cartoon: { color: 'spectrum' } });
      viewer.zoomTo();
      viewer.render();
    }
  }, [resultats]);

  const analyser = async () => {
    setLoading(true);
    setResultats(null);
    setNomProteine('');
    setSelectedSite(null);
    try {
      setEtape('🔬 ESMFold — Prédiction structure 3D...');

      const response = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sequence: sequence })
      });

      setEtape('🧬 fpocket — Détection des cavités...');
      const data = await response.json();
      setEtape('🤖 XGBoost — Scoring des sites...');
      setResultats(data);

      fetch(`${API_URL}/identify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sequence: sequence })
      })
        .then(r => r.json())
        .then(d => { if (d.nom) setNomProteine(d.nom); })
        .catch(() => setNomProteine('Protéine inconnue'));

    } catch (error) {
      console.error('Erreur:', error);
    }
    setLoading(false);
  };

  const telechargerPDF = () => {
    const doc = new jsPDF();
    doc.setFontSize(12);
    doc.setTextColor(31, 78, 121);
    doc.text('StructBind — Rapport d\'analyse', 20, 20);
    doc.setFontSize(12);
    doc.setTextColor(0, 0, 0);
    doc.text(`Protéine : ${nomProteine}`, 20, 30);
    doc.text(`Date : ${new Date().toLocaleDateString()}`, 20, 38);
    doc.line(20, 42, 190, 42);

    const rows = resultats.sites.map((site, index) => [
      `Site ${index + 1} — ${getLabel(site.score)}`,
      `${(site.score * 100).toFixed(2)}%`,
      `${site.volume} Å³`,
      site.residus.slice(0, 4).join(', ') + '...',
      site.features ? site.features.hydrophobicite_moy?.toFixed(3) : '-',
      site.features ? site.features.charge_nette?.toFixed(2) : '-',
      site.features ? site.features.sasa_totale?.toFixed(2) : '-',
    ]);

    autoTable(doc, {
      startY: 48,
      head: [['Site', 'Score', 'Volume', 'Résidus', 'Hydropho.', 'Charge', 'SASA']],
      body: rows,
      styles: { fontSize: 8, cellPadding: 3, fillColor: false },
      headStyles: { fillColor: [31, 78, 121], textColor: 255, fontStyle: 'bold' },
    });

    doc.save('StructBind_rapport.pdf');
  };

  const telechargerPDFSite = (site, index) => {
    const doc = new jsPDF();
    doc.setFontSize(14);
    doc.setTextColor(31, 78, 121);
    doc.text(`StructBind — Site ${index + 1} — ${getLabel(site.score)}`, 20, 20);
    doc.setFontSize(10);
    doc.setTextColor(0, 0, 0);
    doc.text(`Protéine : ${nomProteine}`, 20, 30);
    doc.text(`Date : ${new Date().toLocaleDateString()}`, 20, 38);
    doc.line(20, 42, 190, 42);

    if (site.features) {
      const rows = Object.entries(site.features)
        .filter(([key]) => key !== 'composition')
        .map(([key, value]) => [
          key,
          typeof value === 'number' ? value.toFixed(3) : value
        ]);

      autoTable(doc, {
        startY: 48,
        head: [['Features', 'Valeurs']],
        body: rows,
        styles: { fontSize: 9, cellPadding: 3, fillColor: false },
        headStyles: { fillColor: [31, 78, 121], textColor: 255, fontStyle: 'bold' },
        columnStyles: {
          0: { fontStyle: 'bold', cellWidth: 80 },
          1: { cellWidth: 60 }
        }
      });
    }

    doc.save(`StructBind_site_${index + 1}.pdf`);
  };

  const getCouleurSite = (score) => {
    if (score >= 0.90) return '#086036';
    if (score >= 0.80) return '#337c34';
    if (score >= 0.60) return '#c6d21d';
    if (score >= 0.40) return '#f3a734';
    return '#cd4814';
  };

  const visualiserSite = (site) => {
    if (!viewerRef.current) return;
    setSiteVisualise(site);
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

      <br/><button onClick={analyser}>
        {loading ? 'Analyzing...' : 'Analiser'}
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
                {nomProteine}<br/><br/><strong>Structure 3D</strong>
                <button
                  className="reset-btn"
                  onClick={() => {
                    const viewer = window.$3Dmol.createViewer(viewerRef.current, { backgroundColor: '#16213e' });
                    viewer.addModel(resultats.pdb_content, 'pdb');
                    viewer.setStyle({}, { cartoon: { color: 'spectrum' } });
                    viewer.zoomTo();
                    viewer.render();
                    setSiteVisualise(null);
                  }}
                >
                  → reinitialiser structure
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
                    <>
                      <h2>Sites prédits
                        <button className="pdf-btn" onClick={telechargerPDF}>
                          📄 Télécharger le rapport PDF
                        </button>
                      </h2>
                      <table className="sites-table">
                        <thead>
                          <tr>
                            <th>Site</th>
                            <th>Score</th>
                            <th>Volume</th>
                            <th>Résidus</th>
                            <th>Détails</th>
                          </tr>
                        </thead>
                        <tbody>
                          {resultats.sites.map((site, index) => (
                            <tr key={index}>
                              <td
                                className={getTitreClass(site.score)}
                                onClick={() => visualiserSite(site)}
                                style={{ cursor: 'pointer' }}
                                title="Cliquez pour visualiser le site"
                              >
                                Site {index + 1} — {getLabel(site.score)}
                              </td>
                              <td>{(site.score * 100).toFixed(2)}%</td>
                              <td>{site.volume} Å³</td>
                              <td>{site.residus.slice(0, 3).join(', ')}...</td>
                              <td>
                                <button onClick={() => setSelectedSite(site)}>View</button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>

                      {selectedSite && (
                        <div className="popup-overlay" onClick={() => setSelectedSite(null)}>
                          <div className="popup" onClick={(e) => e.stopPropagation()}>
                            <button
                              className="pdf-btn"
                              onClick={() => telechargerPDFSite(selectedSite, resultats.sites.indexOf(selectedSite))}
                            >
                              ⬇️ Télécharger
                            </button>
                            <h3>Détails du site</h3>
                            <button className="close-btn" onClick={() => setSelectedSite(null)}>✕</button>
                            <table className="details-table">
                              <tbody>
                                <tr><td>Score</td><td>{(selectedSite.score * 100).toFixed(2)}%</td></tr>
                                <tr><td>Volume</td><td>{selectedSite.volume} Å³</td></tr>
                                <tr><td>Résidus</td><td>{selectedSite.residus.join(', ')}</td></tr>
                                {selectedSite.features && Object.entries(selectedSite.features)
                                  .filter(([key]) => key !== 'composition')
                                  .map(([key, value]) => (
                                    <tr key={key}>
                                      <td>{key}</td>
                                      <td>{typeof value === 'number' ? value.toFixed(3) : value}</td>
                                    </tr>
                                  ))
                                }
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </>
          ) : ""}
        </div>
      )}
    </div>
  );
}

export default App;