// Applique config.js : l'adresse de l'application et les profils de l'équipe.
// Sans JavaScript la page reste complète : les liens par défaut sont déjà dans le HTML.
(function () {
  var config = window.LANDING || {}

  if (config.urlApplication) {
    document.querySelectorAll('[data-app]').forEach(function (lien) {
      lien.href = config.urlApplication
      lien.textContent = 'Voir l’application'
      lien.target = '_blank'
      lien.rel = 'noopener'
    })
  }

  ;['linkedin', 'twitter'].forEach(function (reseau) {
    if (!config[reseau]) return
    var lien = document.querySelector('[data-reseau="' + reseau + '"]')
    if (!lien) return
    lien.href = config[reseau]
    lien.target = '_blank'
    lien.rel = 'noopener'
    lien.parentElement.hidden = false
  })

  // Section courante dans le menu : le lien de la section affichée est souligné.
  var liens = Array.prototype.slice.call(document.querySelectorAll('.entete__nav a'))
  if ('IntersectionObserver' in window) {
    var sections = liens
      .map(function (lien) { return document.querySelector(lien.getAttribute('href')) })
      .filter(Boolean)
    var observateur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (entree) {
        if (!entree.isIntersecting) return
        liens.forEach(function (lien) {
          lien.classList.toggle('actif', lien.getAttribute('href') === '#' + entree.target.id)
        })
      })
    }, { rootMargin: '-45% 0px -50% 0px' })
    sections.forEach(function (section) { observateur.observe(section) })
  }
})()
