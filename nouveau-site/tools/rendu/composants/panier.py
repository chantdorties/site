"""Le bouton « voir mon panier », partagé par les fiches livres et les pages de texte.

PayPal tient le panier de son côté : ce bouton ne fait que rouvrir celui du visiteur.
Contrairement aux boutons d'achat, il ne s'identifie pas par un `hosted_button_id` mais
par un bloc signé par PayPal (`panierEncrypted` dans content/reglages/paiement.json),
recopié tel quel depuis l'ancien site. Il ne se fabrique donc pas ici.

Le style correspondant est dans frontend/assets/css/32-page-livre.css (règle
.paypal-form, partagée par toute la feuille recollée) et, pour la rangée de boutons
des pages de texte, 35-pages-de-texte.css (règle .section-actions).
"""

from __future__ import annotations

from ..icones import icon
from ..outils import e


class Panier:
    def render_cart_link(self) -> str:
        return f"""
<form class="paypal-form" action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_blank">
  <input type="hidden" name="cmd" value="_s-xclick">
  <input type="hidden" name="encrypted" value="{e(self.payment_settings['panierEncrypted'])}">
  <button class="button button--secondary" type="submit">{icon('shopping-cart')} {e(self.payment_settings['libelleVoirPanier'])}</button>
</form>"""
