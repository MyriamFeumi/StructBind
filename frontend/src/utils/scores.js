export const getTitreClass = (score) => {
    if (score >= 0.90) return "titre-principal";
    if (score >= 0.80) return "titre-tres-bon";
    if (score >= 0.60) return "titre-bon";
    if (score >= 0.40) return "titre-possible";
    return "titre-fausse";
};

export const getLabel = (score) => {
    if (score >= 0.90) return "Site principal";
    if (score >= 0.80) return "Très bon site";
    if (score >= 0.60) return "Bon site";
    if (score >= 0.40) return "Site possible";
    return "Fausse cavité";
};

export const getCouleurSite = (score) => {
    if (score >= 0.90) return '#086036';
    if (score >= 0.80) return '#337c34';
    if (score >= 0.60) return '#c6d21d';
    if (score >= 0.40) return '#f3a734';
    return '#cd4814';
};