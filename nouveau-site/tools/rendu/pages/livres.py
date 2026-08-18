"""La page de chaque livre.

De haut en bas : fil d'Ariane, couverture, titre, auteurs et illustrateurs, résumé,
le tableau des caractéristiques (type, collection, âge, pages, format, reliure, ISBN),
la ligne d'achat avec le bouton PayPal d'origine, les extraits en PDF, les liens, puis
la galerie d'illustrations.

Le bouton PayPal de chaque livre est celui saisi dans sa fiche : il ne doit jamais
être fabriqué ici, sous peine d'envoyer l'argent au mauvais endroit. Le bouton
« voir mon panier » qui l'accompagne vient de composants/panier.py.

Le style correspondant est dans frontend/assets/css/32-page-livre.css ;
la galerie d'illustrations suit 33-galerie.css.
"""

from __future__ import annotations

from urllib.parse import quote

from content_data import media_alt, media_path

from ..icones import icon
from ..libelles import BINDING_LABELS, TYPE_LABELS
from ..outils import absolute_url, e, format_price


class PagesLivres:
    def build_book_pages(self) -> None:
        for book in self.books:
            collection = self.collections_by_slug[book["collection"]]
            contributors = []
            if book["auteurs"]:
                contributors.append(f"Écrit par {self.contributor_links(book['auteurs'])}")
            if book["illustrateurs"]:
                contributors.append(f"Illustré par {self.contributor_links(book['illustrateurs'])}")
            if book["prefaciers"]:
                contributors.append(f"Préfacé par {self.contributor_links(book['prefaciers'])}")

            facts: list[tuple[str, str]] = []
            if book["typeOuvrage"]:
                facts.append(("Type", TYPE_LABELS.get(book["typeOuvrage"], book["typeOuvrage"].replace("-", " ").title())))
            if book["ageMinimum"]:
                facts.append(("Âge", f"À partir de {book['ageMinimum']} ans"))
            if book["nombrePages"]:
                facts.append(("Pages", str(book["nombrePages"])))
            if book["format"]:
                facts.append(("Format", book["format"]))
            if book["reliure"]:
                # La valeur enregistrée est un mot-clé : la page affichait « cartonne ».
                facts.append(("Reliure", BINDING_LABELS.get(book["reliure"], book["reliure"])))
            if book["isbn"] and book["isbnValide"]:
                facts.append(("ISBN", book["isbn"]))
            facts_html = "".join(f"<div><dt>{e(label)}</dt><dd>{e(value)}</dd></div>" for label, value in facts)

            price = format_price(book["prixCentimes"])
            price_html = f'<span class="price">{e(price)}</span>' if price else ""
            availability_class = "" if book["disponible"] else " availability--unavailable"
            availability_label = (
                self.payment_settings["libelleDisponible"]
                if book["disponible"]
                else self.payment_settings["libelleIndisponible"]
            )
            subject = quote(f"Question — {book['titre']}")
            if book["disponible"]:
                purchase_action = f"""
<form class="paypal-form" action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_blank">
  <input type="hidden" name="cmd" value="_s-xclick">
  <input type="hidden" name="hosted_button_id" value="{e(book['paypalHostedButtonId'])}">
  <button class="button" type="submit">{icon('shopping-cart')} {e(self.payment_settings['libellePanier'])}</button>
</form>{self.render_cart_link()}"""
            else:
                purchase_action = f'<a class="button" href="mailto:{e(self.site_settings["courriel"])}?subject={subject}">{icon("mail")} {e(self.payment_settings["libelleContact"])}</a>'
            purchase = f"""
<div class="purchase-line">
  {price_html}<span class="availability{availability_class}">{availability_label}</span>
  {purchase_action}
</div>"""

            excerpts = ""
            valid_excerpts = [path for path in book["extraits"] if path in self.document_media]
            if valid_excerpts:
                excerpt_links = "".join(
                    f'<li><a class="button button--secondary button--small" href="{self.document_media[path]}" target="_blank">{icon("file")} {e(self.payment_settings["libelleExtrait"])} {index if len(valid_excerpts) > 1 else ""}</a></li>'
                    for index, path in enumerate(valid_excerpts, start=1)
                )
                excerpts = f'<div><h2>Extraits</h2><ul class="link-list">{excerpt_links}</ul></div>'

            gallery = ""
            if book["illustrations"]:
                gallery_items = [
                    (
                        self.illustration_media[media_path(item)],
                        media_alt(item, f"Illustration intérieure de {book['titre']} — {index}"),
                    )
                    for index, item in enumerate(book["illustrations"], start=1)
                    if media_path(item) in self.illustration_media
                ]
                gallery = f'<section class="section section--white"><div class="container"><div class="section-heading"><div><p class="eyebrow">À l’intérieur</p><h2>Quelques illustrations</h2></div></div>{self.render_gallery(gallery_items)}</div></section>'

            related_slugs = book.get("aDecouvrir")
            if related_slugs is None:
                related_slugs = [slug for slug in collection["livres"] if slug != book["slug"]][:4]
            related = [self.books_by_slug[slug] for slug in related_slugs if slug in self.books_by_slug]
            related_html = "".join(self.render_book_card(item) for item in related)
            related_section = ""
            if related_html:
                related_section = f'<section class="section"><div class="container"><div class="section-heading"><div><p class="eyebrow">Dans la même collection</p><h2>À découvrir aussi</h2></div><a href="/collections/{e(collection["slug"])}/">Toute la collection</a></div><div class="book-grid">{related_html}</div></div></section>'
            content = f"""
<section class="section section--white">
  <div class="container">
    {self.render_breadcrumbs([('Accueil', '/'), ('Catalogue', '/catalogue/'), (collection['titre'], f"/collections/{collection['slug']}/"), (book['titre'], None)])}
    <article class="book-detail">
      <div><img class="book-detail__cover" src="{self.cover_media[book['slug']]['large']}" srcset="{self.cover_media[book['slug']]['small']} 480w, {self.cover_media[book['slug']]['large']} 900w" sizes="(max-width: 760px) 90vw, 390px" alt="{e(book.get('couvertureAlt') or f'Couverture de {book["titre"]}')}" width="900" height="1350"></div>
      <div class="book-detail__content">
        <p class="eyebrow"><a href="/collections/{e(collection['slug'])}/">{e(collection['titre'])}</a></p>
        <h1>{e(book['titre'])}</h1>
        <p class="contributors">{'<br>'.join(contributors)}</p>
        <p class="book-description">{e(book['description'] or 'Description à venir.')}</p>
        <dl class="book-facts">{facts_html}</dl>
        {excerpts}
        {purchase}
      </div>
    </article>
  </div>
</section>
{gallery}
{related_section}"""

            structured = {
                "@context": "https://schema.org",
                "@type": "Book",
                "name": book["titre"],
                "author": [
                    {"@type": "Person", "name": self.people_by_slug[slug]["nom"]}
                    for slug in book["auteurs"]
                ],
                "image": absolute_url(self.base_url, self.cover_media[book["slug"]]["large"]),
                "description": book["description"],
            }
            if book["isbn"] and book["isbnValide"]:
                structured["isbn"] = book["isbn"]
            seo_title, seo_description, seo_image = self.seo_values(
                book,
                default_title=book["titre"],
                default_description=book["description"] or f"Découvrez {book['titre']}.",
                default_image=self.cover_media[book["slug"]]["large"],
            )
            page = self.render_page(
                title=seo_title,
                description=seo_description,
                route=f"/livres/{book['slug']}/",
                content=content,
                active="catalogue",
                body_class="book-page",
                og_type="book",
                og_image=seo_image,
                structured_data=structured,
            )
            self.write_route(f"/livres/{book['slug']}/", page)

