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

Les pages principales (accueil, catalogue, actualités…) reçoivent les mêmes sections,
ajoutées dans leur fiche à un emplacement choisi : render_free_sections les place.

Le style correspondant est dans frontend/assets/css/35-pages-de-texte.css ;
la page Projets ajoute 37-projets.css.
"""

from __future__ import annotations

from typing import Any

from content_data import media_alt, media_path, section_images

from ..outils import e


class PagesEditoriales:
    def build_editorial_pages(self) -> None:
        for page_data in self.pages:
            if page_data["slug"] == "entree":
                continue
            draft = bool(page_data["aVerifier"])
            if draft and not self.include_drafts:
                continue
            sections = self.render_sections(page_data["sections"], owner=page_data["slug"])
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
            # Ses sections ajoutées se placent avant la liste (à la suite de l’introduction)
            # ou après.
            projects = ""
            if page_data["slug"] == "projets":
                sections += self.render_sections(self.free_sections("projets", "avant-liste"), owner="projets")
                projects = self.render_projects() + self.render_free_sections("projets", "apres-liste")
            description = self.summary_text(page_data)
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


    def render_sections(self, sections: list[dict[str, Any]], *, owner: str) -> str:
        """Les sections visibles, l’une après l’autre : intertitre, texte, livres et
        boutons d’achat. Une section masquée garde ses textes sans paraître.

        Trois sortes ont leur propre mise en page : le texte et l’image côte à côte,
        la galerie de photos, la citation en grand (35-pages-de-texte.css)."""
        rendered = []
        for section in sections:
            if section["masquee"]:
                continue
            heading = f'<h2>{e(section["titre"])}</h2>' if section.get("titre") else ""
            special = self.render_special_section(section, heading, owner=owner)
            if special is not None:
                rendered.append(special)
                continue
            rendered.append(
                f'<section class="editorial-section">{heading}'
                f'<div class="rich-text">{self.markdown_html(section["contenu"], owner=owner)}</div>'
                f'{self.render_section_books(section["livres"])}'
                f'{self.render_paypal_buttons(section["boutonsPaypal"])}</section>'
            )
        return "".join(rendered)

    def render_special_section(self, section: dict[str, Any], heading: str, *, owner: str) -> str | None:
        """Une section côte à côte, une galerie ou une citation ; None pour les autres.

        Les images viennent de la même préparation que celles posées dans un texte
        (optimize_inline_images) : allégées, et jamais publiées dans leur taille
        d’origine.
        """
        kind = section.get("type")
        body = self.markdown_html(section["contenu"], owner=owner) if section["contenu"].strip() else ""
        if kind == "colonnes":
            # L’image vient en premier dans la page : sur téléphone, où les colonnes
            # s’empilent, elle précède le texte. Sur ordinateur, « droite » l’y range.
            image = self._balise_image(e(section["alt"]), section["image"], owner)
            return (
                f'<section class="editorial-section editorial-columns editorial-columns--{e(section["cote"])}">'
                f'{heading}<div class="editorial-columns__grid">'
                f'<figure class="editorial-columns__image">{image}</figure>'
                f'<div class="rich-text">{body}</div></div></section>'
            )
        if kind == "galerie":
            photos = [
                (self.inline_media[path], alt)
                for path, alt in section_images(section)
                if path in self.inline_media
            ]
            text = f'<div class="rich-text">{body}</div>' if body else ""
            return f'<section class="editorial-section editorial-gallery">{heading}{text}{self.render_gallery(photos)}</section>'
        if kind == "citation":
            source = section.get("source") or ""
            caption = f"<figcaption>{e(source.strip())}</figcaption>" if source.strip() else ""
            return (
                f'<section class="editorial-section">{heading}'
                f'<figure class="editorial-quote"><blockquote class="rich-text">{body}</blockquote>{caption}</figure></section>'
            )
        return None

    def free_sections(self, page: str, placement: str) -> list[dict[str, Any]]:
        """Les sections ajoutées à une page principale pour un emplacement donné."""
        record = self.home_settings if page == "accueil" else self.page_settings[page]
        return [section for section in record["sectionsLibres"] if section["emplacement"] == placement]

    def render_free_sections(self, page: str, placement: str) -> str:
        """Les sections ajoutées d’une page principale à un emplacement, dans une bande
        à largeur de lecture ; rien si aucune n’y est visible."""
        body = self.render_sections(self.free_sections(page, placement), owner=page)
        if not body:
            return ""
        return f'\n<section class="section"><div class="container"><div class="free-sections">{body}</div></div></section>'

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

    @classmethod
    def summary_text(cls, page: dict[str, Any]) -> str:
        """Le texte qui résume la page sur « La maison » et pour les moteurs de
        recherche : celui de la première section visible qui en a un. Une galerie
        sans texte, en tête de page, ne laisse donc pas le résumé vide."""
        return next(
            (section["contenu"] for section in cls.visible_sections(page) if section["contenu"].strip()),
            "",
        )

    def published_editorial_pages(self) -> list[dict[str, Any]]:
        return [
            page
            for page in self.pages
            if page["slug"] != "entree"
            and (self.include_drafts or not page["aVerifier"])
        ]

