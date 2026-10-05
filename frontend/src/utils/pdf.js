import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { getLabel } from './scores';

export const telechargerPDF = (resultats, nomProteine) => {
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

export const telechargerPDFSite = (site, index, nomProteine) => {
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
}