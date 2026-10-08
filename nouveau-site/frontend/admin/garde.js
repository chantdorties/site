/**
 * Premières lignes exécutées par l’administration, avant Decap.
 *
 * Chez Free, aucun en-tête de sécurité ne peut être réglé : ce script et la politique
 * de sécurité écrite dans index.html en tiennent lieu.
 *
 * - Adresse sécurisée : le relais de connexion ne remet son jeton qu’à
 *   https://chantdorties.pages-perso.free.fr. Ouverte depuis l’ancienne adresse
 *   http://chantdorties.free.fr, l’administration ne pourrait pas se connecter : on y
 *   bascule donc d’office, chemin compris.
 * - Jamais dans un cadre : une page tierce ne doit pas pouvoir afficher l’administration
 *   sous un déguisement pour faire cliquer à l’aveugle (l’en-tête X-Frame-Options d’OVH).
 */

(function () {
  var adresseSecurisee = 'https://chantdorties.pages-perso.free.fr';
  if (location.hostname === 'chantdorties.free.fr' || location.hostname === 'chantdorties.pages-perso.free.fr') {
    if (location.protocol !== 'https:' || location.hostname !== 'chantdorties.pages-perso.free.fr') {
      location.replace(adresseSecurisee + location.pathname + location.search + location.hash);
      return;
    }
  }
  if (window.top !== window.self) {
    document.documentElement.style.display = 'none';
    window.top.location = window.self.location.href;
  }
})();
