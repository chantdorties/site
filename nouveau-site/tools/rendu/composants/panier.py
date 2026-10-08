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
    PAYPAL_ACTION = "https://www.paypal.com/cgi-bin/webscr"

    def render_paypal_form(
        self,
        *,
        hosted_button_id: str = "",
        encrypted: str = "",
        label: str = "",
        button_class: str = "button",
        form_class: str = "paypal-form",
        form_id: str = "",
    ) -> str:
        """Le seul formulaire PayPal du site : achat d'un livre ou d'une offre, panier.

        Un bouton d'achat s'identifie par `hosted_button_id`, le panier par le bloc
        `encrypted`. Sans `label`, le formulaire n'a pas de bouton : c'est celui du
        menu, que ses boutons rejoignent par leur attribut « form ».
        """
        attributes = f' id="{form_id}"' if form_id else ""
        if hosted_button_id:
            identity = f'<input type="hidden" name="hosted_button_id" value="{e(hosted_button_id)}">'
        else:
            identity = f'<input type="hidden" name="encrypted" value="{e(encrypted)}">'
        lines = ['<input type="hidden" name="cmd" value="_s-xclick">', identity]
        if label:
            lines.append(f'<button class="{button_class}" type="submit">{icon("shopping-cart")} {e(label)}</button>')
        body = "\n".join(f"  {line}" for line in lines)
        return (
            f'\n<form class="{form_class}"{attributes} action="{self.PAYPAL_ACTION}" method="post" target="_blank">'
            f"\n{body}\n</form>"
        )

    def render_cart_link(self) -> str:
        return self.render_paypal_form(
            encrypted=self.payment_settings["panierEncrypted"],
            label=self.payment_settings["libelleVoirPanier"],
            button_class="button button--secondary",
        )
