"""La page d'accueil.

Quatre bandeaux, dans l'ordre :
  1. la bannière : rubrique, titre, accroche, deux boutons, et le ruban de couvertures
     des livres mis en avant ;
  2. le bandeau commercial : information de la maison, libraires, particuliers,
     soutien, bouton de don PayPal ;
  3. les collections, via la vitrine partagée (composants/vitrine_collections.py) ;
  4. le bandeau sombre « Nous suivre » : actualités et manuscrits.

Tous les textes viennent de content/pages-du-site/accueil.json, rangés dans l'ordre des
bandeaux ; seul l'identifiant du bouton de don reste dans les réglages de paiement.
Les livres mis en avant sont cochés dans chaque fiche livre.

Le style correspondant est réparti en trois fichiers, dans l'ordre des bandeaux :
frontend/assets/css/20-accueil-banniere.css, 22-accueil-commercial.css et
41-accueil-suivre.css. Les collections passent par 25-vitrine-collections.css.
"""

from __future__ import annotations

from typing import Any

from ..icones import icon
from ..outils import e


class PageAccueil:
    def featured_books(self) -> list[dict[str, Any]]:
        selected = [
            book
            for book in self.books
            if book["miseEnAvantAccueil"] and book["disponible"]
        ]
        return sorted(selected, key=lambda book: (book["ordreAccueil"], book["ordre"], book["slug"]))

    def home_cover_books(self) -> list[dict[str, Any]]:
        """Les couvertures du bandeau : les premiers livres mis en avant, autant que
        le réglage « nombreCouvertures » en demande. Les autres restent cochés."""
        return self.featured_books()[: self.home_settings["nombreCouvertures"]]

    def build_home(self) -> None:
        labels = self.home_settings
        featured = self.home_cover_books()
        covers = "".join(
            f"""
<a href="/livres/{e(book['slug'])}/" aria-label="Découvrir {e(book['titre'])}">
  <img src="{self.cover_media[book['slug']]['small']}"
    srcset="{self.cover_media[book['slug']]['small']} 480w, {self.cover_media[book['slug']]['large']} 900w"
    sizes="(max-width: 760px) 30vw, 15vw" alt="{e(book.get('couvertureAlt') or f'Couverture de {book["titre"]}')}"
    loading="{'eager' if index < 3 else 'lazy'}" width="480" height="720">
</a>""".strip()
            for index, book in enumerate(featured)
        )
        texte = lambda champ: (labels.get(champ) or "").strip()
        md = lambda champ, **options: self.markdown_html(texte(champ), owner="accueil", **options)

        # 1. Le bandeau : seul le titre est obligatoire, le reste disparaît s'il est vide.
        rubrique = f'\n      <p class="eyebrow">{e(texte("heroRubrique"))}</p>' if texte("heroRubrique") else ""
        accent = f' <span>{e(texte("heroAccent"))}</span>' if texte("heroAccent") else ""
        accroche = (
            f'\n      <p class="lead">{self.markdown_inline(texte("heroAccroche"), owner="accueil")}</p>'
            if texte("heroAccroche") else ""
        )
        boutons = "".join(
            filter(None, (
                f'\n        <a class="button" href="/catalogue/">{e(texte("boutonCatalogue"))} <span aria-hidden="true">→</span></a>'
                if texte("boutonCatalogue") else "",
                f'\n        <a class="button button--secondary" href="/collections/">{e(texte("boutonCollections"))}</a>'
                if texte("boutonCollections") else "",
            ))
        )
        actions = f'\n      <div class="hero-actions">{boutons}\n      </div>' if boutons else ""
        hero = f"""
<section class="hero">
  <div class="container">
    <div class="hero-copy">{rubrique}
      <h1>{e(texte('heroTitre'))}{accent}</h1>{accroche}{actions}
    </div>
    <div class="cover-ribbon">{covers}</div>
  </div>
</section>"""

        content = hero + self.render_home_information(labels, texte, md)
        if not labels["masquerCollections"]:
            content += self.render_home_collections(texte, md)
        if not labels["masquerSuivre"]:
            content += self.render_home_follow(texte)
        seo_title, seo_description, seo_image = self.seo_values(
            labels,
            default_title=self.site_settings["nom"],
            default_description=self.site_settings["description"],
        )
        page = self.render_page(
            title=seo_title,
            description=seo_description,
            route="/",
            content=content,
            active="home",
            body_class="home-page",
            og_image=seo_image,
        )
        self.write_route("/", page)

    def render_home_information(self, labels: dict[str, Any], texte, md) -> str:
        """2. Le bloc d'information, ou rien s'il est masqué ou entièrement vide.

        Chaque élément vide disparaît avec sa balise : un encadré sans titre ni texte,
        un bouton sans libellé. Une colonne vide laisse l'autre occuper toute la largeur.
        """
        if labels["masquerInformation"]:
            return ""
        situation = "".join(filter(None, (
            f'\n      <p class="eyebrow">{e(texte("informationRubrique"))}</p>' if texte("informationRubrique") else "",
            f'\n      <h2>{e(texte("titreInformation"))}</h2>' if texte("titreInformation") else "",
            f'\n      <div class="lead rich-text">{md("informationTexte")}</div>' if texte("informationTexte") else "",
        )))
        publics = []
        for titre, corps in (("librairesTitre", "librairesTexte"), ("particuliersTitre", "particuliersTexte")):
            if not (texte(titre) or texte(corps)):
                continue
            interieur = ""
            if texte(titre):
                interieur += f"\n          <h4>{e(texte(titre))}</h4>"
            if texte(corps):
                interieur += f'\n          <div class="rich-text">{md(corps)}</div>'
            publics.append(f'\n        <section class="commercial-audience">{interieur}\n        </section>')
        boutons = "".join(filter(None, (
            f"""
        <form class="paypal-form donation-form" action="https://www.paypal.com/donate" method="post" target="_blank">
          <input type="hidden" name="hosted_button_id" value="{e(self.payment_settings['donationHostedButtonId'])}">
          <button class="button" type="submit">{icon('heart')} {e(texte('libelleDon'))}</button>
        </form>""" if texte("libelleDon") else "",
            f'\n        <a class="button button--secondary" href="/offres-speciales/">{e(texte("libelleOffres"))}</a>'
            if texte("libelleOffres") else "",
        )))
        seul = " commercial-audiences--seul" if len(publics) == 1 else ""
        details = "".join(filter(None, (
            f'\n      <h3>{e(texte("commandesTitre"))}</h3>' if texte("commandesTitre") else "",
            f'\n      <div class="rich-text">{md("commandesTexte")}</div>' if texte("commandesTexte") else "",
            f'\n      <div class="commercial-audiences{seul}">{"".join(publics)}\n      </div>' if publics else "",
            f'\n      <div class="commercial-support rich-text">{md("soutienTexte", internal_links={"page de soutien": "/soutien/"})}</div>'
            if texte("soutienTexte") else "",
            f'\n      <div class="hero-actions">{boutons}\n      </div>' if boutons else "",
        )))
        if not (situation or details):
            return ""
        colonnes = []
        if situation:
            colonnes.append(f"\n    <div>{situation}\n    </div>")
        if details:
            colonnes.append(f'\n    <div class="home-commercial__details">{details}\n    </div>')
        une_colonne = "" if len(colonnes) == 2 else " home-commercial__layout--seul"
        return f"""
<section class="section home-commercial">
  <div class="container home-commercial__layout{une_colonne}">{"".join(colonnes)}
  </div>
</section>"""

    def render_home_collections(self, texte, md) -> str:
        """3. Les collections : les six cartes restent, leur titre et leur texte sont facultatifs."""
        titre = "".join(filter(None, (
            f'<p class="eyebrow">{e(texte("collectionsRubrique"))}</p>' if texte("collectionsRubrique") else "",
            f'<h2>{e(texte("collectionsTitre"))}</h2>' if texte("collectionsTitre") else "",
        )))
        presentation = f'<div class="rich-text">{md("collectionsTexte")}</div>' if texte("collectionsTexte") else ""
        entete = (
            f"""
    <div class="section-heading">
      <div>{titre}</div>
      {presentation}
    </div>""" if titre or presentation else ""
        )
        return f"""
<section class="section">
  <div class="container">{entete}
    {self.render_collection_showcase(heading_level=3)}
  </div>
</section>"""

    def render_home_follow(self, texte) -> str:
        """4. « Suivre la maison » : une carte sans titre disparaît, le bandeau sans carte aussi."""
        cartes = []
        for cle, adresse in (("actualites", "/actualites/"), ("manuscrits", "/manuscrits/")):
            if not texte(f"{cle}Titre"):
                continue
            rubrique = f'<p class="eyebrow">{e(texte(f"{cle}Rubrique"))}</p>' if texte(f"{cle}Rubrique") else ""
            action = (
                f'<span>{e(texte(f"{cle}Action"))} <span aria-hidden="true">→</span></span>'
                if texte(f"{cle}Action") else ""
            )
            cartes.append(f'<a href="{adresse}">{rubrique}<h3>{e(texte(f"{cle}Titre"))}</h3>{action}</a>')
        if not cartes:
            return ""
        titre = "".join(filter(None, (
            f'<p class="eyebrow">{e(texte("suivreRubrique"))}</p>' if texte("suivreRubrique") else "",
            f'<h2>{e(texte("suivreTitre"))}</h2>' if texte("suivreTitre") else "",
        )))
        entete = f"""
    <div class="section-heading">
      <div>{titre}</div>
    </div>""" if titre else ""
        seule = " split-callout--seule" if len(cartes) == 1 else ""
        joined = "\n      ".join(cartes)
        return f"""
<section class="section section--ink">
  <div class="container">{entete}
    <div class="split-callout{seule}">
      {joined}
    </div>
  </div>
</section>"""
