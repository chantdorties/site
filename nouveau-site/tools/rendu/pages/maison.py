"""La page « La maison », sommaire des pages de texte.

Une carte par page éditoriale publiée : sa rubrique, son titre, les premiers mots de
son texte, et son libellé d'action. Les couleurs des cartes alternent par groupes de
trois (voir .house-card:nth-child dans la feuille de style).

Le style correspondant est dans frontend/assets/css/24-cartes-maison.css
"""

from __future__ import annotations

from ..icones import icon
from ..outils import e, truncate


class PageMaison:
    def build_house_page(self) -> None:
        labels = self.page_settings["maison"]
        cards = []
        for page in self.published_editorial_pages():
            eyebrow = page.get("rubrique") or self.site_settings["nomCourt"]
            action = page.get("libelleAction") or f"Découvrir {page['titre']}"
            cards.append(
                f"""
<a class="house-card house-card--{e(page['slug'])}" href="/{e(page['slug'])}/">
  <span class="house-card__eyebrow">{e(eyebrow)}</span>
  <h2>{e(page['titre'])}</h2>
  <span class="house-card__summary">{e(truncate(self.texte_brut(page['sections'][0]['contenu']), 120))}</span>
  <span class="house-card__action">{e(action)} {icon('arrow-right')}</span>
</a>""".strip()
            )
        content = f"""
<header class="page-heading"><div class="container">
  {self.render_breadcrumbs([('Accueil', '/'), ('La maison', None)])}
  <p class="eyebrow">{e(labels['rubrique'])}</p><h1>{e(labels['titre'])}</h1>
  <div class="lead rich-text">{self.markdown_html(labels['introduction'], owner="maison")}</div>
</div></header>
<section class="section"><div class="container"><div class="house-grid">{"".join(cards)}</div></div></section>"""
        page = self.render_page(
            title=labels["titre"],
            description=labels["descriptionSeo"],
            route="/la-maison/",
            content=content,
            active="maison",
        )
        self.write_route("/la-maison/", page)

