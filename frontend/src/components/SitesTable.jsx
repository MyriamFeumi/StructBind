import { getTitreClass, getLabel } from '../utils/scores';
import { telechargerPDF, telechargerPDFSite } from '../utils/pdf';

const SitesTable = ({ resultats, nomProteine, selectedSite, setSelectedSite, visualiserSite }) => {
    return (
        <>       
            <h2>Sites prédits
                <button className="pdf-btn" onClick={() => telechargerPDF(resultats, nomProteine)}>
                📄 Télécharger le rapport PDF
                </button>
            </h2>

            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
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
                </div>

                {selectedSite && (
                    <div className="popup-overlay" onClick={() => setSelectedSite(null)}>
                        <div className="popup" onClick={(e) => e.stopPropagation()}>
                            <button
                                className="pdf-btn"
                                onClick={() => telechargerPDFSite(selectedSite, resultats.sites.indexOf(selectedSite),  nomProteine)}
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
  );
};
  
export default SitesTable;