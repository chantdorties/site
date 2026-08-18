"""L'annuaire des auteurs et illustrateurs, et la fiche de chaque personne.

`build_people_index` dessine la page /personnes/ : titre, champ de recherche, filtre
par rôle, puis une grille vide — les personnes sont déposées par
frontend/assets/js/people.js, qui lit /data/personnes.json.

`build_person_pages` dessine une page par personne : portrait ou monogramme,
biographie, liens, galerie, et la liste de ses livres regroupés par rôle.

Le style correspondant est dans frontend/assets/css/site.css :
règles .person-grid, .person-card, .person-card__visual, .monogram,
.person-detail, .person-detail__visual, .filter-grid--people
"""

from __future__ import annotations


from content_data import media_alt, media_path

from ..icones import icon
from ..libelles import ROLE_LABELS
from ..outils import absolute_url, e, monogram


class PagesPersonnes:
    def build_people_index(self) -> None:
        labels = self.page_settings["personnes"]
        content = f"""
<header class="page-heading">
  <div class="container">
    {self.render_breadcrumbs([('Accueil', '/'), ('Auteurs & illustrateurs', None)])}
    <p class="eyebrow">{e(labels['rubrique'])}</p>
    <h1>{e(labels['titre'])}</h1>
    <p class="lead">{e(labels['introduction'])}</p>
  </div>
</header>
<section class="filter-panel" id="recherche" aria-label="Filtres de l’annuaire">
  <div class="container filter-grid filter-grid--people">
    <div class="field"><label for="person-search">Rechercher un nom</label><input id="person-search" type="search" placeholder="Rechercher…" autocomplete="off"></div>
    <div class="field"><label for="person-role">Rôle</label><select id="person-role"><option value="">Tous les rôles</option><option value="auteur">Auteurs</option><option value="illustrateur">Illustrateurs</option><option value="prefacier">Préfaciers</option></select></div>
  </div>
</section>
<section class="section">
  <div class="container">
    <div class="results-bar"><p class="results-status" data-results-status aria-live="polite">Chargement de l’annuaire…</p></div>
    <div class="person-grid" data-person-grid aria-busy="true"><p class="loading-state">Chargement des personnes…</p></div>
  </div>
</section>"""
        page = self.render_page(
            title=labels["titre"],
            description=labels["descriptionSeo"],
            route="/personnes/",
            content=content,
            active="people",
            scripts=["/assets/js/people.js"],
        )
        self.write_route("/personnes/", page)


    def build_person_pages(self) -> None:
        for person in self.people:
            related_slugs = []
            for role_books in person["livres"].values():
                for slug in role_books:
                    if slug not in related_slugs:
                        related_slugs.append(slug)
            cards = "".join(self.render_book_card(self.books_by_slug[slug]) for slug in related_slugs)
            media = self.person_media.get(person["slug"])
            if media:
                portrait_alt = person.get("imagePrincipaleAlt") or f"Portrait de {person['nom']}"
                visual = f'<img src="{media["large"]}" srcset="{media["small"]} 480w, {media["large"]} 900w" sizes="(max-width: 760px) 90vw, 330px" alt="{e(portrait_alt)}" width="900" height="900">'
                og_image = media["large"]
            else:
                visual = f'<span class="monogram" aria-hidden="true">{e(monogram(person["nom"]))}</span>'
                og_image = None
            roles = " · ".join(ROLE_LABELS.get(role, role.title()) for role in person["roles"])
            biography = person["biographie"] or "Cette personne a contribué aux ouvrages présentés ci-dessous."
            gallery_items = [
                (
                    self.person_gallery_media[media_path(item)],
                    media_alt(item, f"{person['nom']} — image {index}"),
                )
                for index, item in enumerate(person["images"], start=1)
                if media_path(item) in self.person_gallery_media
            ]
            gallery = ""
            if gallery_items:
                gallery = (
                    '<section class="section section--white"><div class="container">'
                    '<div class="section-heading"><div><p class="eyebrow">En images</p>'
                    f'<h2>{e(person["nom"])}</h2></div></div>{self.render_gallery(gallery_items)}'
                    '</div></section>'
                )
            external = ""
            if person["liensExternes"]:
                links = "".join(
                    f'<li><a class="button button--secondary button--small" href="{e(url)}" target="_blank" rel="noopener noreferrer">Site personnel {icon("external")}</a></li>'
                    for url in person["liensExternes"]
                )
                external = f'<ul class="link-list">{links}</ul>'
            content = f"""
<section class="section section--white"><div class="container">
  {self.render_breadcrumbs([('Accueil', '/'), ('Auteurs & illustrateurs', '/personnes/'), (person['nom'], None)])}
  <article class="person-detail">
    <div class="person-detail__visual">{visual}</div>
    <div><p class="eyebrow">{e(roles)}</p><h1>{e(person['nom'])}</h1><p class="lead">{e(biography)}</p>{external}</div>
  </article>
</div></section>
{gallery}
<section class="section"><div class="container"><div class="section-heading"><div><p class="eyebrow">Bibliographie</p><h2>{len(related_slugs)} {'livres associés' if len(related_slugs) > 1 else 'livre associé'}</h2></div></div><div class="book-grid">{cards}</div></div></section>"""
            structured = {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": person["nom"],
                "description": person["biographie"],
                "url": absolute_url(self.base_url, f"/personnes/{person['slug']}/"),
            }
            seo_title, seo_description, seo_image = self.seo_values(
                person,
                default_title=person["nom"],
                default_description=person["biographie"] or f"Découvrez les livres auxquels {person['nom']} a contribué.",
                default_image=og_image,
            )
            page = self.render_page(
                title=seo_title,
                description=seo_description,
                route=f"/personnes/{person['slug']}/",
                content=content,
                active="people",
                og_image=seo_image,
                structured_data=structured,
            )
            self.write_route(f"/personnes/{person['slug']}/", page)

