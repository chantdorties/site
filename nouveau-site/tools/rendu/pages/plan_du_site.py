"""Le plan du site : toutes les adresses publiques réunies en trois listes.

Livres et personnes, collections, puis la maison. Il sert aux visiteurs comme aux
moteurs de recherche.

Le style correspondant est dans frontend/assets/css/site.css :
règles .editorial-layout, .editorial-section
"""

from __future__ import annotations

from ..outils import e


class PagePlanDuSite:
    def build_site_map_page(self) -> None:
        editorial = self.published_editorial_pages()
        editorial_links = "".join(f'<li><a href="/{page["slug"]}/">{e(page["titre"])}</a></li>' for page in editorial)
        collection_links = "".join(f'<li><a href="/collections/{item["slug"]}/">{e(item["titre"])}</a></li>' for item in self.collections)
        content = f"""
<header class="page-heading"><div class="container">{self.render_breadcrumbs([('Accueil', '/'), ('Plan du site', None)])}<h1>Plan du site</h1></div></header>
<section class="section"><div class="container editorial-layout"><div>
  <section class="editorial-section"><h2>Livres et personnes</h2><ul><li><a href="/catalogue/">Catalogue</a></li><li><a href="/personnes/">Auteurs & illustrateurs</a></li></ul></section>
  <section class="editorial-section"><h2>Collections</h2><ul>{collection_links}</ul></section>
  <section class="editorial-section"><h2>La maison</h2><ul><li><a href="/actualites/">Actualités</a></li>{editorial_links}</ul></section>
</div></div></section>"""
        page = self.render_page(
            title="Plan du site",
            description="Plan du site des Éditions Chant d’orties.",
            route="/plan-du-site/",
            content=content,
            active="",
        )
        self.write_route("/plan-du-site/", page)

