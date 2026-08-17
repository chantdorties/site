/**
 * Remise du résultat de l’authentification à l’administration.
 *
 * Ce fichier existe parce que la politique de sécurité du sous-domaine impose
 * « script-src 'self' » : un script écrit directement dans callback.php serait refusé par
 * le navigateur, et la fenêtre resterait indéfiniment sur « Connexion en cours… ».
 * Le résultat de l’échange voyage donc par les attributs « data- » de cette balise.
 *
 * Le protocole est celui qu’attend Decap : la fenêtre surgissante annonce sa présence,
 * l’administration répond, la fenêtre transmet alors la charge utile. L’origine est
 * toujours nommée — avec « * », n’importe quelle page ouvrant ce relais repartirait avec
 * un jeton autorisant l’écriture dans le dépôt.
 */

(function () {
  var script = document.currentScript;
  var origine = script.dataset.origine;
  var message = script.dataset.message;
  var etat = document.getElementById('etat');

  if (!window.opener) {
    etat.textContent = 'Cette page doit être ouverte par l’administration.';
    return;
  }

  function transmettre(evenement) {
    if (evenement.origin !== origine) { return; }
    window.opener.postMessage(message, origine);
    window.removeEventListener('message', transmettre, false);
  }

  window.addEventListener('message', transmettre, false);
  window.opener.postMessage('authorizing:github', origine);
})();
