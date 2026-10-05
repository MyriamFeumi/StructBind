import { getCouleurSite } from '../utils/scores';

const ViewerPanel = ({ resultats, viewerRef, setSiteVisualise }) => {
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

    const reinitialiser = () => {
        const viewer = window.$3Dmol.createViewer(viewerRef.current, { backgroundColor: '#16213e' });
        viewer.addModel(resultats.pdb_content, 'pdb');
        viewer.setStyle({}, { cartoon: { color: 'spectrum' } });
        viewer.zoomTo();
        viewer.render();
        setSiteVisualise(null);
    };

    return { visualiserSite, reinitialiser };
};

export default ViewerPanel;

