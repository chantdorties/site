// Les images en miniature dans les listes de l’administration : la couverture devant
// chaque livre, l’emblème devant chaque collection, le portrait devant chaque auteur
// ou illustrateur — ou ses initiales s’il n’a pas de portrait, comme sur le site.
//
// Decap n’affiche une image dans ses listes que pour un champ nommé « image »,
// « cover »… ; ceux d’ici s’appellent « couverture » et « logo », et Decap ne montre
// de toute façon rien en vue liste. Plutôt que de renommer les champs dans toutes les
// fiches et le générateur, ce script pose une vignette devant chaque lien de fiche,
// d’après les fichiers publics /data/livres.json, collections.json et personnes.json —
// ceux de la dernière publication. Une fiche créée depuis reste sans vignette jusqu’à la
// suivante.
//
// Decap redessine ses listes à chaque tri, filtre ou retour en arrière : on observe la
// page et on complète les liens qui n’ont pas encore leur vignette. Le style est dans
// admin.css (.vignette).
(() => {
  // Rubrique de l’administration → fichier public et champ qui porte l’image.
  const RUBRIQUES = {
    livres: { donnees: 'livres', image: 'couverture', forme: 'vignette--couverture' },
    collections: { donnees: 'collections', image: 'logo', forme: 'vignette--embleme' },
    personnes: { donnees: 'personnes', image: 'imagePrincipale', forme: 'vignette--portrait', repli: 'monogram' }
  };
  const charges = {};
  const charger = (nom) => {
    charges[nom] = charges[nom] || fetch(`/data/${nom}.json`, { cache: 'no-cache' })
      .then((reponse) => (reponse.ok ? reponse.json() : []))
      .catch(() => [])
      .then((liste) => new Map(liste.map((fiche) => [fiche.slug, fiche])));
    return charges[nom];
  };

  const decorer = () => Object.entries(RUBRIQUES).forEach(async ([rubrique, regle]) => {
    const liens = [...document.querySelectorAll(`a[href*="/collections/${rubrique}/entries/"]`)]
      .filter((lien) => !lien.querySelector(':scope > .vignette'));
    if (!liens.length) return;
    const parSlug = await charger(regle.donnees);
    liens.forEach((lien) => {
      if (lien.querySelector(':scope > .vignette')) return;
      const slug = decodeURIComponent(lien.getAttribute('href').split('/entries/')[1] || '');
      const fiche = parSlug.get(slug);
      const source = fiche?.[regle.image];
      const initiales = regle.repli && fiche?.[regle.repli];
      if (!source && !initiales) return;
      const vignette = document.createElement(source ? 'img' : 'span');
      vignette.className = `vignette ${regle.forme}`;
      if (source) {
        vignette.src = source;
        vignette.alt = '';
        vignette.loading = 'lazy';
      } else {
        vignette.classList.add('vignette--initiales');
        vignette.setAttribute('aria-hidden', 'true');
        vignette.textContent = initiales;
      }
      lien.classList.add('avec-vignette');
      lien.prepend(vignette);
    });
  });

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
