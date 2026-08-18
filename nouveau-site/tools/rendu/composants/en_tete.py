"""L'en-tête, présent en haut de chaque page.

Il contient le logo suivi du nom de la maison, la navigation principale, le bouton
loupe, le panier PayPal, et — sur téléphone — le bouton d'ouverture du menu puis le
menu lui-même.

Les entrées du menu ne sont pas écrites ici : elles viennent de
content/reglages/navigation.json et se modifient depuis l'administration.

Le style correspondant est dans frontend/assets/css/10-en-tete.css pour le
bandeau et la navigation, et 12-menu-mobile.css pour le menu des petits écrans.
"""

from __future__ import annotations

from ..icones import icon
from ..outils import e


class EnTete:
    CART_FORM_ID = "panier-paypal"

    def render_nav(self, active: str, *, mobile: bool = False) -> str:
        links = []
        navigation = sorted(
            (item for item in self.navigation_settings["liens"] if item["visible"]),
            key=lambda item: (item["ordre"], item["id"]),
        )
        for item in navigation:
            current = ' aria-current="page"' if item["id"] == active else ""
            links.append(
                f'<a class="nav-link" href="{e(item["url"])}"{current}>'
                f'{e(item["libelle"])}</a>'
            )
        search_settings = self.navigation_settings["recherche"]
        search = (
            f'<a class="nav-link" href="{e(search_settings["url"])}">'
            f'{e(search_settings["libelle"])}</a>'
            if mobile
            else (
                f'<a class="icon-button" href="{e(search_settings["url"])}" '
                f'title="{e(search_settings["libelle"])}" '
                f'aria-label="{e(search_settings["libelle"])}">'
                f'{icon("search")}</a>'
            )
        )
        return "".join(links) + search + self.render_nav_cart(mobile=mobile)

    def render_nav_cart(self, *, mobile: bool) -> str:
        """Le bouton panier du menu, sur le modèle de la loupe.

        Sur grand écran il prend la forme d'une icône ronde, sur téléphone celle
        d'une entrée de menu ordinaire. Le menu principal et le menu mobile en
        portent chacun un, mais tous deux commandent l'unique formulaire posé par
        render_cart_form : le bloc signé par PayPal pèse plus de deux kilo-octets,
        le répéter alourdirait chaque page pour rien.
        """
        label = self.payment_settings["libelleVoirPanier"]
        if mobile:
            return (
                f'<button class="nav-link" type="submit" form="{self.CART_FORM_ID}">'
                f"{e(label)}</button>"
            )
        return (
            f'<button class="icon-button" type="submit" form="{self.CART_FORM_ID}" '
            f'title="{e(label)}" aria-label="{e(label)}">{icon("shopping-cart")}</button>'
        )

    def render_cart_form(self) -> str:
        """Le formulaire du panier, posé une seule fois par page, sans rien afficher.

        Les boutons du menu s'y rattachent par leur attribut « form ».
        """
        return f"""
<form class="nav-cart" id="{self.CART_FORM_ID}" action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_blank">
  <input type="hidden" name="cmd" value="_s-xclick">
  <input type="hidden" name="encrypted" value="{e(self.payment_settings['panierEncrypted'])}">
</form>"""

    def render_header(self, active: str) -> str:
        short_name = self.site_settings["nomCourt"]
        if " " in short_name:
            name_start, name_accent = short_name.rsplit(" ", 1)
        else:
            name_start, name_accent = short_name, ""
        return f"""
<header class="site-header">
  <div class="container header-inner">
    <a class="wordmark" href="/" aria-label="{e(self.site_settings['nom'])}, accueil">
      <img class="site-logo" src="/assets/images/chantdorties-logo.webp" alt="" width="245" height="241">
      <span class="wordmark__text">{e(name_start)} <span class="wordmark__accent">{e(name_accent)}</span></span>
    </a>
    <nav class="primary-nav" aria-label="Navigation principale">
      {self.render_nav(active)}
    </nav>
    <button class="icon-button menu-button" type="button" data-menu-button
      aria-expanded="false" aria-controls="navigation-mobile" aria-label="Ouvrir le menu" title="Ouvrir le menu">
      <span class="menu-button__open">{icon("menu")}</span>
      <span class="menu-button__close">{icon("x")}</span>
    </button>
  </div>
</header>
<nav class="mobile-nav" id="navigation-mobile" data-mobile-nav aria-label="Navigation mobile" hidden>
  {self.render_nav(active, mobile=True)}
</nav>
{self.render_cart_form()}""".strip()

