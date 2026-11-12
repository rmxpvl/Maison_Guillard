// Helpers of the quote editor (back-office). Money is typed by hand, so amounts are strings
// ("250,5") and totals are computed in cents to avoid floating point surprises.

// "250,5" -> 25050; anything that is not a non-negative amount -> null.
export function versCentimes(valeur) {
  const texte = String(valeur ?? '').trim().replace(',', '.')
  if (!/^\d+(\.\d{1,2})?$/.test(texte)) return null
  return Math.round(Number(texte) * 100)
}

function enDecimal(valeur) {
  return (versCentimes(valeur) / 100).toFixed(2)
}

// The editor state, from a request as the back-office detail route sends it.
export function editionDepuisDemande(demande) {
  return {
    lignes: demande.lignes
      .filter((l) => l.produit_id !== null)
      .map((l) => ({
        id: l.id,
        libelle: l.libelle,
        quantite: l.quantite,
        prix: l.prix_final ?? l.prix_indicatif,
      })),
    libres: demande.lignes
      .filter((l) => l.produit_id === null)
      .map((l) => ({ libelle: l.libelle, quantite: l.quantite, prix: l.prix_final })),
    frais: demande.frais_livraison ?? demande.frais_livraison_suggere ?? '0',
    message: demande.message_artisane ?? '',
  }
}

// Total in euros; an amount not typed correctly yet counts for 0.
export function totalDevis(edition) {
  const lignes = [...edition.lignes, ...edition.libres]
  const centimes = lignes.reduce((somme, l) => somme + (versCentimes(l.prix) ?? 0) * l.quantite, 0)
  return (centimes + (versCentimes(edition.frais) ?? 0)) / 100
}

export function devisValide(edition) {
  const lignes = [...edition.lignes, ...edition.libres]
  return (
    lignes.length > 0 &&
    lignes.every((l) => versCentimes(l.prix) !== null) &&
    edition.libres.every((l) => l.libelle.trim() !== '') &&
    versCentimes(edition.frais) !== null
  )
}

export function devisPourApi(edition) {
  return {
    lignes: edition.lignes.map((l) => ({ id: l.id, prix_final: enDecimal(l.prix) })),
    lignes_libres: edition.libres.map((l) => ({
      libelle: l.libelle.trim(),
      quantite: l.quantite,
      prix: enDecimal(l.prix),
    })),
    frais_livraison: enDecimal(edition.frais),
    message_artisane: edition.message.trim() || null,
  }
}

export function insererMessageType(message, texte) {
  return message.trim() === '' ? texte : [message.trimEnd(), texte].join('\n\n')
}
