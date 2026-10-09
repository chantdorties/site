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
  <span class="house-card__summary">{e(truncate(self.texte_brut(self.visible_sections(page)[0]['contenu']), 120))}</span>
  <span class="house-card__action">{e(action)} {icon('arrow-right')}</span>
</a>""".strip()
            )
        content = f"""
{self.render_page_heading(
    [('Accueil', '/'), ('La maison', None)],
    labels['titre'],
    eyebrow=labels['rubrique'],
    introduction=self.markdown_html(labels['introduction'], owner="maison"),
)}{self.render_free_sections("maison", "avant-liste")}
<section class="section"><div class="container"><div class="house-grid">{"".join(cards)}</div></div></section>{self.render_free_sections("maison", "apres-liste")}"""
        page = self.render_page(
            title=labels["titre"],
            description=labels["descriptionSeo"],
            route="/la-maison/",
            content=content,
            active="maison",
        )
        self.write_route("/la-maison/", page)

