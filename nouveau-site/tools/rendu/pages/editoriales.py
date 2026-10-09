"""Les pages de texte de la maison, créées librement depuis l'administration.

Ce sont /commandes/, /soutien/, /manuscrits/, /amis/, /projets/, /offres-speciales/,
/atelier-ecriture/, /librairies-partenaires/ et /mentions-legales/. Toutes partagent
la même mise en page : titre, colonne de texte en sections, et colonne de liens à
droite. La page Projets ajoute la grille des livres à paraître
(composants/cartes_projets.py).

Une section peut désigner des livres du catalogue, affichés en cartes sous son texte,
et porter des boutons d'achat PayPal, saisis dans sa fiche : les offres
groupées, l'adhésion et le don, les titres soldés. Comme pour les livres, leur
identifiant vient toujours de la saisie et ne se fabrique jamais ici.

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
            if page_data["slug"] == "entree":
                continue
            draft = bool(page_data["aVerifier"])
            if draft and not self.include_drafts:
                continue
            rendered_sections = []
            for section in self.visible_sections(page_data):
                heading = f'<h2>{e(section["titre"])}</h2>' if section["titre"] else ""
                rendered_sections.append(
                    f'<section class="editorial-section">{heading}'
                    f'<div class="rich-text">{self.markdown_html(section["contenu"], owner=page_data["slug"])}</div>'
                    f'{self.render_section_books(section["livres"])}'
                    f'{self.render_paypal_buttons(section["boutonsPaypal"])}</section>'
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
            description = self.visible_sections(page_data)[0]["contenu"]
            content = f"""
{self.render_page_heading(
    [('Accueil', '/'), (page_data['titre'], None)],
    page_data['titre'],
    eyebrow=page_data.get('rubrique') or self.site_settings['nom'],
)}
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
                active="maison",
                draft=draft,
                og_image=seo_image,
            )
            self.write_route(f"/{page_data['slug']}/", page)


    def render_section_books(self, slugs: list[str]) -> str:
        """Les livres choisis dans une section, en cartes comme dans le catalogue.

        Une offre groupée montre ainsi les couvertures, les auteurs et les prix tirés
        des fiches : rien n'est à recopier dans la page, ni à mettre à jour deux fois.
        """
        books = [self.books_by_slug[slug] for slug in slugs if slug in self.books_by_slug]
        if not books:
            return ""
        cards = "".join(self.render_book_card(book) for book in books)
        return f'<div class="book-grid book-grid--section">{cards}</div>'

    def render_paypal_buttons(self, buttons: list[dict[str, Any]]) -> str:
        """Les boutons d’achat d’une section, au format exact des fiches livres.

        Le formulaire est celui des fiches livres (composants/panier.py).
        L’identifiant vient toujours de la saisie, jamais d’un calcul,
        sous peine d’envoyer l’argent au mauvais article.
        """
        if not buttons:
            return ""
        # Pas de « voir mon panier » ici : il est dans le menu, donc à portée de
        # toutes les pages. Le répéter sous chaque offre l'encombrerait.
        forms = "".join(
            self.render_paypal_form(hosted_button_id=button["hostedButtonId"], label=button["libelle"])
            for button in buttons
        )
        return f'<div class="section-actions">{forms}</div>'

    @staticmethod
    def visible_sections(page: dict[str, Any]) -> list[dict[str, Any]]:
        """Les sections que montre le site : une section masquée garde ses textes dans
        l'administration sans paraître. Le chargement garantit qu'il en reste une."""
        return [section for section in page["sections"] if not section["masquee"]]

    def published_editorial_pages(self) -> list[dict[str, Any]]:
        return [
            page
            for page in self.pages
            if page["slug"] != "entree"
            and (self.include_drafts or not page["aVerifier"])
        ]

