"""La page Actualités.

Les entrées sont regroupées par catégorie (salon, parution, rencontre, vie de la
maison). Chaque entrée porte sa date, son titre, son texte, éventuellement une image
et un lien.

Elle n'est pas une page de texte : tous ses réglages, référencement et anciennes
adresses compris, sont dans content/pages-du-site/actualites.json.

Le style correspondant est dans frontend/assets/css/36-actualites.css pour les
cartes, et 38-encart-actualites.css pour l'encart de tête et les catégories.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..icones import icon
from ..libelles import NEWS_TYPE_LABELS
from ..outils import e


class PageActualites:
    def build_news_page(self) -> None:
        labels = self.page_settings["actualites"]
        seo = labels.get("seo") or {}
        news_items = []
        for item in self.news:
            image_html = ""
            if item["slug"] in self.news_image_media:
                image_html = (
                    f'<img src="{self.news_image_media[item["slug"]]}" '
                    f'alt="{e(item.get("imageAlt") or item["titre"])}" loading="lazy" width="1200" height="900">'
                )
            date = datetime.strptime(item["datePublication"], "%Y-%m-%d")
            body = self.markdown_html(item["contenu"], owner=item["slug"])
            actions = []
            if item.get("lienExterne"):
                actions.append(
                    f'<a href="{e(item["lienExterne"])}" target="_blank" rel="noopener noreferrer">'
                    f'En savoir plus {icon("external")}</a>'
                )
            if item.get("document") and item["document"] in self.document_media:
                actions.append(
                    f'<a href="{self.document_media[item["document"]]}" target="_blank">'
                    f'{icon("file")} Télécharger le document</a>'
                )
            actions_html = f'<div class="news-card__actions">{"".join(actions)}</div>' if actions else ""
            news_items.append(
                f"""
<article class="news-card">
  {image_html}
  <div class="news-card__content">
    <p class="news-card__meta"><span>{e(NEWS_TYPE_LABELS[item['type']])}</span><time datetime="{item['datePublication']}">{date.strftime('%d/%m/%Y')}</time></p>
    <h2>{e(item['titre'])}</h2>
    <p class="news-card__summary">{self.markdown_inline(item['resume'], owner=item['slug'])}</p>
    <div class="news-card__body rich-text">{body}</div>
    {actions_html}
  </div>
</article>""".strip()
            )
        # Les catégories annoncées sont celles qui figurent vraiment sur la page : écrites
        # à la main, elles promettaient des rencontres même quand il n’y en avait aucune.
        published_types = [
            NEWS_TYPE_LABELS[key]
            for key in NEWS_TYPE_LABELS
            if any(item["type"] == key for item in self.news)
        ]
        topics = ""
        if published_types:
            topics = (
                '<div class="news-topics" aria-label="Catégories publiées">'
                + "".join(f"<span>{e(label)}</span>" for label in published_types)
                + "</div>"
            )
        news_listing = ""
        if news_items:
            news_listing = (
                '<section class="section"><div class="container">'
                '<div class="news-grid">' + "".join(news_items) + "</div></div></section>"
            )
        content = f"""
{self.render_page_heading(
    [('Accueil', '/'), ('Actualités', None)],
    labels['titre'],
    eyebrow=labels['rubrique'],
    introduction=self.markdown_html(labels['introduction'], owner="actualites"),
)}
{self.render_free_sections("actualites", "avant-liste")}{news_listing}{self.render_free_sections("actualites", "apres-liste")}{self.render_news_facebook(labels, topics)}"""
        page = self.render_page(
            title=seo.get("titre") or labels["titre"],
            description=labels["descriptionSeo"],
            route="/actualites/",
            content=content,
            active="actualites",
            og_image=self.seo_image_media.get(seo.get("image")),
        )
        self.write_route("/actualites/", page)

    def render_news_facebook(self, labels: dict[str, Any], topics: str) -> str:
        """Le bloc Facebook du bas de la page, ou rien s'il est masqué.

        Affiché, il garde son titre et son bouton (la validation y veille) ; la petite
        ligne et le texte peuvent rester vides et disparaissent alors.
        """
        if labels["masquerFacebook"]:
            return ""
        rubrique = (labels.get("appelRubrique") or "").strip()
        texte = (labels.get("appelTexte") or "").strip()
        rubrique_html = f'\n    <p class="eyebrow">{e(rubrique)}</p>' if rubrique else ""
        texte_html = (
            f'\n    <div class="lead rich-text">{self.markdown_html(texte, owner="actualites")}</div>'
            if texte else ""
        )
        return f"""
<section class="section news-section"><div class="container">
  <div class="news-callout">{rubrique_html}
    <h2>{e(labels['appelTitre'])}</h2>{texte_html}
    {topics}
    <a class="button" href="{e(self.site_settings['facebook'])}" target="_blank" rel="noopener noreferrer">{e(labels['boutonFacebook'])} {icon('external')}</a>
  </div>
</div></section>"""
