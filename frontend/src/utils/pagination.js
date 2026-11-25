// Cuts a list into pages. `page` comes from the address (?page=2): anything odd falls back to page 1,
// a number past the end shows the last page.
export function pageDe(elements, page, parPage) {
  const liste = elements ?? []
  const nbPages = Math.max(1, Math.ceil(liste.length / parPage))
  const demandee = Number.parseInt(page, 10)
  const numero = Number.isInteger(demandee) && demandee >= 1 ? Math.min(demandee, nbPages) : 1
  return { elements: liste.slice((numero - 1) * parPage, numero * parPage), page: numero, nbPages }
}
