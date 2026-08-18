"""La page d'accueil.

Quatre bandeaux, dans l'ordre :
  1. la bannière : rubrique, titre, accroche, deux boutons, et le ruban de couvertures
     des livres mis en avant ;
  2. le bandeau commercial : information de la maison, libraires, particuliers,
     soutien, bouton de don PayPal ;
  3. les collections, via la vitrine partagée (composants/vitrine_collections.py) ;
  4. le bandeau sombre « Nous suivre » : actualités et manuscrits.

Les textes viennent de content/reglages/accueil.json et de la page « accueil » ;
les livres mis en avant sont cochés dans chaque fiche livre.

Le style correspondant est dans frontend/assets/css/site.css :
règles .hero, .cover-ribbon, .home-commercial, .commercial-audience,
.section-heading, .split-callout
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

    def build_home(self) -> None:
        home_sections = self.pages_by_slug["accueil"]["sections"]
        sections_by_id = {section.get("id"): section for section in home_sections}
        intro = sections_by_id["presentation"]["contenu"]
        house_update = sections_by_id["information"]
        commercial_info = sections_by_id["soutien-commandes"]
        booksellers_info = sections_by_id["libraires"]
        individuals_info = sections_by_id["particuliers"]
        support_info = sections_by_id["soutien"]
        labels = self.home_settings
        featured = self.featured_books()
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
        content = f"""
<section class="hero">
  <div class="container">
    <div class="hero-copy">
      <p class="eyebrow">{e(labels['heroRubrique'])}</p>
      <h1>{e(labels['heroTitre'])} <span>{e(labels['heroAccent'])}</span></h1>
      <p class="lead">{e(labels['heroAccroche'])}</p>
      <div class="hero-actions">
        <a class="button" href="/catalogue/">{e(labels['boutonCatalogue'])} <span aria-hidden="true">→</span></a>
        <a class="button button--secondary" href="/collections/">{e(labels['boutonCollections'])}</a>
      </div>
    </div>
    <div class="cover-ribbon">{covers}</div>
  </div>
</section>
<section class="section home-commercial">
  <div class="container home-commercial__layout">
    <div>
      <p class="eyebrow">{e(house_update['titre'])}</p>
      <h2>{e(labels['titreInformation'])}</h2>
      <p class="lead">{e(house_update['contenu'])}</p>
    </div>
    <div class="home-commercial__details">
      <h3>{e(commercial_info['titre'])}</h3>
      <p>{self.linkify_text(commercial_info['contenu'])}</p>
      <div class="commercial-audiences">
        <section class="commercial-audience">
          <h4>{e(booksellers_info['titre'])}</h4>
          <p>{self.linkify_text(booksellers_info['contenu'])}</p>
        </section>
        <section class="commercial-audience">
          <h4>{e(individuals_info['titre'])}</h4>
          <p>{self.linkify_text(individuals_info['contenu'])}</p>
        </section>
      </div>
      <p class="commercial-support">{self.linkify_text(support_info['contenu'], internal_links={'page de soutien': '/soutien/'})}</p>
      <div class="hero-actions">
        <form class="paypal-form donation-form" action="https://www.paypal.com/donate" method="post" target="_blank">
          <input type="hidden" name="hosted_button_id" value="{e(self.payment_settings['donationHostedButtonId'])}">
          <button class="button" type="submit">{icon('heart')} {e(self.payment_settings['libelleDon'])}</button>
        </form>
        <a class="button button--secondary" href="/offres-speciales/">{e(self.payment_settings['libelleOffres'])}</a>
      </div>
    </div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="section-heading">
      <div><p class="eyebrow">{e(labels['collectionsRubrique'])}</p><h2>{e(labels['collectionsTitre'])}</h2></div>
      <p>{e(intro)}</p>
    </div>
    {self.render_collection_showcase(heading_level=3)}
  </div>
</section>
<section class="section section--ink">
  <div class="container">
    <div class="section-heading">
      <div><p class="eyebrow">{e(labels['suivreRubrique'])}</p><h2>{e(labels['suivreTitre'])}</h2></div>
    </div>
    <div class="split-callout">
      <a href="/actualites/"><p class="eyebrow">{e(labels['actualitesRubrique'])}</p><h3>{e(labels['actualitesTitre'])}</h3><span>{e(labels['actualitesAction'])} <span aria-hidden="true">→</span></span></a>
      <a href="/manuscrits/"><p class="eyebrow">{e(labels['manuscritsRubrique'])}</p><h3>{e(labels['manuscritsTitre'])}</h3><span>{e(labels['manuscritsAction'])} <span aria-hidden="true">→</span></span></a>
    </div>
  </div>
</section>"""
        seo_title, seo_description, seo_image = self.seo_values(
            self.pages_by_slug["accueil"],
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

