/**
 * Remise du résultat de l’authentification à l’administration.
 *
 * Ce fichier existe parce que la politique de sécurité du sous-domaine impose
 * « script-src 'self' » : un script écrit directement dans callback.php serait refusé par
 * le navigateur, et la fenêtre resterait indéfiniment sur « Connexion en cours… ».
 * Le résultat de l’échange voyage donc par les attributs « data- » de cette balise.
 *
 * Le protocole est celui qu’attend Decap : la fenêtre surgissante annonce sa présence,
 * l’administration répond, la fenêtre transmet alors la charge utile. Les origines
 * sont toujours nommées — avec « * », n’importe quelle page ouvrant ce relais
 * repartirait avec un jeton autorisant l’écriture dans le dépôt. L’annonce part vers
 * chacune ; le navigateur ne la remet qu’à celle qui a réellement ouvert la fenêtre, et
 * la charge utile ne part que vers l’origine qui a répondu, si elle figure dans la liste.
 */

(function () {
  var script = document.currentScript;
  var origines = script.dataset.origines.split(' ');
  var message = script.dataset.message;
  var etat = document.getElementById('etat');

  if (!window.opener) {
    etat.textContent = 'Cette page doit être ouverte par l’administration.';
    return;
  }

  function transmettre(evenement) {
    if (origines.indexOf(evenement.origin) === -1) { return; }
    window.opener.postMessage(message, evenement.origin);
    window.removeEventListener('message', transmettre, false);
  }

  window.addEventListener('message', transmettre, false);
  origines.forEach(function (origine) {
    window.opener.postMessage('authorizing:github', origine);
  });
})();
