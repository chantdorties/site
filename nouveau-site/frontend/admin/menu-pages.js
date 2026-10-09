// Le groupe dépliant « Pages » du menu de gauche de l’administration.
//
// Decap range ses rubriques en une liste plate, sans groupe. « Mes pages » et « Pages
// principales » sont deux rubriques (l’une de fichiers libres, l’autre de fiches
// fixes) que la rédaction cherche pourtant au même endroit : ce script pose au-dessus
// d’elles un titre « Pages » qui les replie et les déplie.
//
// Les éléments de la liste appartiennent à React, qui les redessine à chaque
// navigation : on ne les déplace pas, on leur pose des classes. L’ordre affiché (le
// groupe sous les Réglages, « Mes pages » en premier) vient de admin.css, par la
// propriété CSS order ; dans config.yml, les ancres YAML imposent un autre ordre.
(() => {
  const RUBRIQUES = ['pages', 'pages_du_site'];
  const MEMOIRE = 'admin-menu-pages-ouvert';

  const lireMemoire = () => {
    try { return localStorage.getItem(MEMOIRE) === '1'; } catch { return false; }
  };
  const ecrireMemoire = (ouvert) => {
    try { localStorage.setItem(MEMOIRE, ouvert ? '1' : '0'); } catch { /* sans mémoire */ }
  };
  let ouvert = lireMemoire();
  const rubriqueActive = () => RUBRIQUES.some((nom) =>
    location.hash.startsWith(`#/collections/${nom}`));

  const lien = (liste, nom) => liste.querySelector(`:scope > li > a[data-testid="${nom}"]`);

  const appliquer = () => {
    const liste = [...document.querySelectorAll('aside ul')]
      .find((ul) => RUBRIQUES.every((nom) => lien(ul, nom)));
    if (!liste) return;
    liste.classList.add('menu-avec-groupe');
    RUBRIQUES.forEach((nom) => lien(liste, nom).parentElement
      .classList.add('menu-groupe__rubrique', `menu-groupe__rubrique--${nom}`));
    lien(liste, 'reglages')?.parentElement.classList.add('menu-groupe__avant');

    let titre = liste.querySelector(':scope > li.menu-groupe');
    if (!titre) {
      // Même apparence que les liens voisins : on reprend leur classe, sans la marque
      // « sidebar-active » que porte la rubrique ouverte.
      const modele = liste.querySelector(':scope > li > a:not([aria-current])');
      titre = document.createElement('li');
      titre.className = 'menu-groupe';
      const bouton = document.createElement('button');
      bouton.type = 'button';
      bouton.className = `menu-groupe__bouton ${modele ? modele.className.replace('sidebar-active', '') : ''}`;
      const icone = lien(liste, 'pages').querySelector('span');
      if (icone) bouton.append(icone.cloneNode(true));
      bouton.append(document.createTextNode('Pages'));
      const fleche = document.createElement('span');
      fleche.className = 'menu-groupe__fleche';
      fleche.setAttribute('aria-hidden', 'true');
      bouton.append(fleche);
      bouton.addEventListener('click', () => {
        ouvert = !liste.classList.contains('menu-groupe--ouvert');
        ecrireMemoire(ouvert);
        afficher(liste);
      });
      titre.append(bouton);
      liste.append(titre);
    }
    afficher(liste);
  };

  const afficher = (liste) => {
    const deplie = ouvert || rubriqueActive();
    if (liste.classList.contains('menu-groupe--ouvert') !== deplie) {
      liste.classList.toggle('menu-groupe--ouvert', deplie);
    }
    const bouton = liste.querySelector('.menu-groupe__bouton');
    if (bouton && bouton.getAttribute('aria-expanded') !== String(deplie)) {
      bouton.setAttribute('aria-expanded', String(deplie));
    }
  };

  let prevu = false;
  const planifier = () => {
    if (prevu) return;
    prevu = true;
    requestAnimationFrame(() => {
      prevu = false;
      appliquer();
    });
  };
  new MutationObserver(planifier).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('hashchange', planifier);
})();
