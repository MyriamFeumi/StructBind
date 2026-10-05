import { useState, useEffect, useRef } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'https://structbind.onrender.com';

export const useAnalyser = () => {
    const [sequence, setSequence]       = useState('');
    const [resultats, setResultats]     = useState(null);
    const [loading, setLoading]         = useState(false);
    const [nomProteine, setNomProteine] = useState('');
    const [selectedSite, setSelectedSite] = useState(null);
    const [etape, setEtape]             = useState('');
    const viewerRef = useRef(null);

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
            setEtape('🔬 ESMFold — Prédiction structure 3D...')

            // Normaliser : supprimer l'entête FASTA (>...) si présent
            const lignes = sequence.split('\n');
            const seqPure = lignes.filter(l => !l.startsWith('>')).join('').replace(/\s/g, '').trim();
            const seqFinale = seqPure || sequence.trim();

            const response = await fetch(`${API_URL}/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sequence: seqFinale })
            });

            setEtape('🧬 fpocket — Détection des cavités...');
            const data = await response.json();
            setEtape('🤖 XGBoost — Scoring des sites...');
            setResultats(data);

            fetch(`${API_URL}/identify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sequence: sequence }),
            })
                .then(r => r.json())
                .then(d => {
                setNomProteine(d.nom);
                })
                .catch(() => {
                    setNomProteine('Protéine inconnue');
                });

        } catch (error) {
            console.error('Erreur:', error);
            setResultats({ pdb_content: null, sites: [] });
        }
        setLoading(false);
    };


    return {
        sequence, setSequence,
        resultats,
        loading,
        nomProteine,
        selectedSite, setSelectedSite,
        etape,
        viewerRef,
            analyser,
    };
};