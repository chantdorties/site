"""Les pages de texte de la maison, créées librement depuis l'administration.

Ce sont /commandes/, /soutien/, /manuscrits/, /amis/, /projets/, /offres-speciales/,
/atelier-ecriture/, /librairies-partenaires/ et /mentions-legales/. Toutes partagent
la même mise en page : titre, colonne de texte en sections, et colonne de liens à
droite. La page Projets ajoute la grille des livres à paraître
(composants/cartes_projets.py).

Le style correspondant est dans frontend/assets/css/35-pages-de-texte.css ;
la page Projets ajoute 37-projets.css.
"""

from __future__ import annotations

from typing import Any

from content_data import media_alt, media_path

from ..outils import e


class PagesEditoriales:
    def build_editorial_pages(self) -> None:
        for page_data in self.pages:
            if page_data["slug"] in {"entree", "accueil"}:
                continue
            if page_data["slug"] == "actualites":
                self.build_news_page(page_data)
                continue
            draft = bool(page_data["aVerifier"])
            if draft and not self.include_drafts:
                continue
            rendered_sections = []
            for section in page_data["sections"]:
                heading = f'<h2>{e(section["titre"])}</h2>' if section["titre"] else ""
                rendered_sections.append(
                    f'<section class="editorial-section">{heading}'
                    f'<div class="rich-text">{self.markdown_html(section["contenu"], owner=page_data["slug"])}</div></section>'
                )
            sections = "".join(rendered_sections)
            link_items = [self.editorial_link(link) for link in page_data["liens"]]
            link_items = [item for item in link_items if item]
            aside = ""
            if link_items:
                aside = f'<aside class="editorial-aside"><h2>Liens et documents</h2><ul>{"".join(f"<li>{item}</li>" for item in link_items)}</ul></aside>'
            gallery = ""
            if page_data["images"]:
                gallery_items = [
                    (
                        self.page_image_media[media_path(item)],
                        media_alt(item, f"{page_data['titre']} — image {index}"),
                    )
                    for index, item in enumerate(page_data["images"], start=1)
                    if media_path(item) in self.page_image_media
                ]
                gallery = f'<section class="section section--white"><div class="container"><h2>En images</h2>{self.render_gallery(gallery_items)}</div></section>'
            # La page Projets porte son introduction dans ses sections ; la liste des
            # projets, elle, vient de leur propre rubrique.
            projects = self.render_projects() if page_data["slug"] == "projets" else ""
            description = page_data["sections"][0]["contenu"]
            active = "actualites" if page_data["slug"] == "actualites" else "maison"
            content = f"""
<header class="page-heading"><div class="container">
  {self.render_breadcrumbs([('Accueil', '/'), (page_data['titre'], None)])}
  <p class="eyebrow">{e(page_data.get('rubrique') or self.site_settings['nom'])}</p><h1>{e(page_data['titre'])}</h1>
</div></header>
<section class="section"><div class="container editorial-layout"><article>{sections}</article>{aside}</div></section>
{projects}
{gallery}"""
            seo_title, seo_description, seo_image = self.seo_values(
                page_data,
                default_title=page_data["titre"],
                default_description=description,
            )
            page = self.render_page(
                title=seo_title,
                description=seo_description,
                route=f"/{page_data['slug']}/",
                content=content,
                active=active,
                draft=draft,
                og_image=seo_image,
            )
            self.write_route(f"/{page_data['slug']}/", page)


    def published_editorial_pages(self) -> list[dict[str, Any]]:
        return [
            page
            for page in self.pages
            if page["slug"] not in {"entree", "accueil", "actualites"}
            and (self.include_drafts or not page["aVerifier"])
        ]

