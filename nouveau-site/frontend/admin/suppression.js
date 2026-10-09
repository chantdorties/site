// La garde du bouton « Supprimer l’entrée » : une fiche dont dépendent d’autres fiches
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
  const boutonSupprimer = () => [...document.querySelectorAll('button')]
    .find((bouton) => /^Supprimer l[’']entrée/.test(bouton.textContent.trim()));

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
