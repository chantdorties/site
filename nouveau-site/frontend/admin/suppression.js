// Le bouton « Supprimer » d’une fiche, et sa garde : une fiche dont dépendent d’autres fiches
// ne se supprime pas, et la raison s’affiche en mots simples.
//
// Decap supprime une fiche publiée directement sur la branche publiée. Si un livre
// citait encore la personne supprimée, la validation refuserait ensuite toute
// publication jusqu’à réparation. La génération sait retirer d’elle-même les liens
// d’agrément (un livre montré dans une page, un lien du menu…) ; pas les liens de
// structure : la collection d’un livre, ses auteurs, les personnes d’un projet, le
// dernier livre d’une collection, les mentions légales. Ces fiches-là sont listées,
// avec leur raison, dans /data/suppression.json (tools/rendu/sortie.py,
// deletion_guard), écrit à chaque publication.
//
// Le fichier date de la dernière publication : un lien créé depuis lui échappe. La
// validation le refuse alors encore, avec un message qui dit quoi corriger.
//
// Decap ne permet pas de retirer son bouton : on le grise, et un clic est arrêté avant
// la demande de confirmation de Decap pour afficher la raison. React redessine la barre
// à chaque navigation ; on observe la page et on remet la marque si elle a disparu.
(() => {
  // Les mots de Decap pour supprimer (« Supprimer l’entrée publiée »…) ne parlent pas à
  // la rédaction, et sa traduction française a des fautes. Decap copie ses traductions
  // au démarrage, avant ce fichier : modifier CMS.getLocale('fr') ici ne change plus
  // rien. On remplace donc le texte du bouton dans la page, et celui des demandes de
  // confirmation (window.confirm) au moment où elles s’affichent. « Annuler les
  // modifications » garde un autre mot : ce bouton-là n’efface pas la fiche.
  const SUPPRIMER = 'Supprimer';
  const archiver = 'Pour la retirer du site en la gardant, choisissez plutôt Publication : Archivé.';
  const BOUTONS = new Map([
    ['Supprimer l\'entrée', SUPPRIMER],
    ['Supprimer l\'entrée publiée', SUPPRIMER],
    ['Supprimer l\'entrée non publiée', SUPPRIMER],
    ['Supprimer la nouvelle entrée', SUPPRIMER],
    ['Supprimer les modications non publiées', 'Annuler les modifications'],
  ]);
  const CONFIRMATIONS = new Map([
    ['Voulez-vous vraiment supprimer cette entrée ?',
      `Supprimer cette fiche pour de bon ? ${archiver}`],
    ['Voulez-vous vraiment supprimer cette entrée publiée ?',
      `Supprimer cette fiche pour de bon ? Elle disparaît du site tout de suite. ${archiver}`],
    ['Voulez-vous vraiment supprimer cette entrée publiée ainsi que vos modifications non enregistrées de cette session ?',
      `Supprimer cette fiche pour de bon, avec les modifications en cours ? Elle disparaît du site tout de suite. ${archiver}`],
    ['Toutes les modifications non publiées de cette entrée seront supprimées. Voulez-vous toujours supprimer ?',
      'Annuler toutes les modifications pas encore publiées de cette fiche ?'],
    ['Ceci supprimera toutes les modifications non publiées de cette entrée ainsi que vos modifications non enregistrées de cette session. Voulez-vous toujours supprimer ?',
      'Annuler toutes les modifications pas encore publiées de cette fiche, y compris celles en cours ?'],
  ]);
  const confirmer = window.confirm.bind(window);
  window.confirm = (message) => confirmer(CONFIRMATIONS.get(message) ?? message);

  // Seul le nœud de texte change : React garde son bouton et ses écouteurs.
  const renommer = () => {
    for (const bouton of document.querySelectorAll('button')) {
      if (bouton.getBoundingClientRect().top >= 70) continue;
      for (const noeud of bouton.childNodes) {
        const nouveau = noeud.nodeType === Node.TEXT_NODE && BOUTONS.get(noeud.nodeValue.trim());
        if (nouveau) noeud.nodeValue = nouveau;
      }
    }
  };

  const RUBRIQUES = { livres: 'livres', personnes: 'personnes', collections: 'collections', pages: 'pages' };
  let gardes = null;
  fetch('/data/suppression.json', { cache: 'no-store' })
    .then((reponse) => (reponse.ok ? reponse.json() : null))
    .then((donnees) => { gardes = donnees; })
    .catch(() => {});

  // La raison d’empêcher la suppression de la fiche ouverte, ou null.
  const raison = () => {
    const ouverte = /#\/collections\/([^/]+)\/entries\/([^/?]+)/.exec(location.hash);
    const rubrique = ouverte && RUBRIQUES[ouverte[1]];
    return (rubrique && gardes?.[rubrique]?.[decodeURIComponent(ouverte[2])]) || null;
  };
  // Le bouton de la barre du haut de la fiche : d’autres « Supprimer » existent dans le
  // formulaire (une image, un élément de liste), plus bas.
  const boutonSupprimer = () => [...document.querySelectorAll('button')]
    .find((bouton) => {
      const texte = bouton.textContent.trim();
      return (texte === SUPPRIMER || BOUTONS.get(texte) === SUPPRIMER) && bouton.getBoundingClientRect().top < 70;
    });

  const avertir = (texte) => {
    let note = document.querySelector('.garde-suppression');
    if (!note) {
      note = document.createElement('div');
      note.className = 'garde-suppression';
      note.setAttribute('role', 'alert');
      document.body.append(note);
    }
    note.innerHTML = '';
    const titre = document.createElement('strong');
    titre.textContent = 'Cette fiche ne peut pas être supprimée';
    const corps = document.createElement('p');
    corps.textContent = texte;
    const fermer = document.createElement('button');
    fermer.type = 'button';
    fermer.textContent = 'Compris';
    fermer.addEventListener('click', () => note.remove());
    note.append(titre, corps, fermer);
  };

  // Phase de capture : le clic est arrêté avant d’atteindre Decap.
  document.addEventListener('click', (evenement) => {
    const bouton = evenement.target.closest?.('button');
    const motif = raison();
    if (!bouton || !motif || bouton !== boutonSupprimer()) return;
    evenement.preventDefault();
    evenement.stopPropagation();
    avertir(motif);
  }, true);

  const marquer = () => {
    renommer();
    const bouton = boutonSupprimer();
    const motif = raison();
    if (!motif) document.querySelector('.garde-suppression')?.remove();
    if (!bouton) return;
    bouton.classList.toggle('suppression-bloquee', Boolean(motif));
    if (motif) bouton.title = motif;
    else bouton.removeAttribute('title');
  };

  let prevu = false;
  const planifier = () => {
    if (prevu) return;
    prevu = true;
    requestAnimationFrame(() => {
      prevu = false;
      marquer();
    });
  };
  new MutationObserver(planifier).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('hashchange', planifier);
})();
