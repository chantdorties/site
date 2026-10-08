// Les couvertures en miniature dans la liste des livres de l’administration.
//
// Decap n’affiche une image dans ses listes que pour un champ nommé « image »,
// « cover »… ; celui des livres s’appelle « couverture ». Plutôt que de renommer le
// champ dans les 64 fiches et le générateur, ce script pose une vignette devant chaque
// lien de fiche livre, d’après /data/livres.json — les couvertures de la dernière
// publication. Un livre créé depuis reste sans vignette jusqu’à la suivante.
//
// Decap redessine ses listes à chaque tri, filtre ou retour en arrière : on observe la
// page et on complète les liens qui n’ont pas encore leur vignette. Le style est dans
// admin.css (.vignette-livre).
(() => {
  const LIEN = 'a[href*="/collections/livres/entries/"]';
  let livres = null;
  const charger = () => {
    livres = livres || fetch('/data/livres.json', { cache: 'no-cache' })
      .then((reponse) => (reponse.ok ? reponse.json() : []))
      .catch(() => [])
      .then((liste) => new Map(liste.map((livre) => [livre.slug, livre])));
    return livres;
  };

  const decorer = async () => {
    const liens = [...document.querySelectorAll(LIEN)]
      .filter((lien) => !lien.querySelector(':scope > .vignette-livre'));
    if (!liens.length) return;
    const parSlug = await charger();
    liens.forEach((lien) => {
      if (lien.querySelector(':scope > .vignette-livre')) return;
      const slug = decodeURIComponent(lien.getAttribute('href').split('/entries/')[1] || '');
      const livre = parSlug.get(slug);
      if (!livre || !livre.couverture) return;
      const image = document.createElement('img');
      image.className = 'vignette-livre';
      image.src = livre.couverture;
      image.alt = '';
      image.loading = 'lazy';
      lien.classList.add('avec-vignette');
      lien.prepend(image);
    });
  };

  let prevu = false;
  new MutationObserver(() => {
    if (prevu) return;
    prevu = true;
    requestAnimationFrame(() => {
      prevu = false;
      decorer();
    });
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
