// Le lien « Tutoriel » de la barre du haut de l’administration, après « Contenus » et
// « Media » : il ouvre le mode d’emploi de l’administration dans un nouvel onglet.
//
// Decap ne permet pas d’ajouter un lien à sa barre : on pose un élément à la suite de
// ses boutons, avec leur classe pour en avoir l’apparence. React redessine la barre à
// chaque navigation ; on observe la page et on remet le lien s’il a disparu.
(() => {
  const ADRESSE = 'https://tuto-des-orties.varascundo.com/';
  const ICONE = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
    + 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">'
    + '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6v.6"/>'
    + '<circle cx="12" cy="17" r=".6" fill="currentColor"/></svg>';

  const poser = () => {
    const liste = document.querySelector('header nav ul');
    if (!liste || liste.querySelector(':scope > li.lien-tutoriel')) return;
    const modele = liste.querySelector(':scope > li > button, :scope > li > a');
    const element = document.createElement('li');
    element.className = 'lien-tutoriel';
    const lien = document.createElement('a');
    lien.href = ADRESSE;
    lien.target = '_blank';
    lien.rel = 'noopener';
    lien.title = 'Le mode d’emploi de l’administration, dans un nouvel onglet';
    // La classe des boutons voisins, sans la marque du bouton actif.
    lien.className = modele ? modele.className.replace(/\bactive\b/g, '') : '';
    lien.innerHTML = `<span class="lien-tutoriel__icone">${ICONE}</span>Tutoriel`;
    element.append(lien);
    liste.append(element);
  };

  let prevu = false;
  new MutationObserver(() => {
    if (prevu) return;
    prevu = true;
    requestAnimationFrame(() => {
      prevu = false;
      poser();
    });
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
