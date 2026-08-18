"""Les noms des auteurs et illustrateurs, et les cartes des livres à paraître.

`contributor_links` transforme une liste de fiches en énumération de liens.
`render_projects` dessine la grille des projets de la page Projets : titre, résumé,
crédits, collection et date de sortie prévue — sans couverture ni prix, puisque le
livre n'existe pas encore.

Le style correspondant est dans frontend/assets/css/site.css :
règles .project-grid, .project-card, .project-card__summary, __credits,
__collection, __release, et .contributors
"""

from __future__ import annotations

from typing import Any

from ..outils import e


class CartesProjets:
    def contributor_links(self, slugs: list[str]) -> str:
        return ", ".join(
            f'<a href="/personnes/{e(slug)}/">{e(self.people_by_slug[slug]["nom"])}</a>'
            for slug in slugs
        )

    def project_contributors(self, project: dict[str, Any], role: str) -> str:
        """Les noms d’un rôle, fiches et noms libres réunis dans une seule énumération.

        Un livre à paraître s’écrit souvent avant que ses auteurs aient une fiche : ceux
        qui en ont une deviennent des liens, les autres restent du texte.
        """
        named = [slug for slug in project[role] if slug in self.people_by_slug]
        parts = [part for part in (self.contributor_links(named),) if part]
        free = ", ".join(e(name) for name in project[f"{role}HorsFiche"])
        if free:
            parts.append(free)
        return ", ".join(parts)

    def render_projects(self) -> str:
        cards = []
        for project in self.projects:
            lines = []
            if project["description"]:
                lines.append(f'<p class="project-card__summary">{e(project["description"])}</p>')
            credits = []
            authors = self.project_contributors(project, "auteurs")
            illustrators = self.project_contributors(project, "illustrateurs")
            if authors:
                credits.append(f"écrit par {authors}")
            if illustrators:
                credits.append(f"illustré par {illustrators}")
            if credits:
                lines.append(f'<p class="project-card__credits">{", ".join(credits)}</p>')
            collection = self.collections_by_slug.get(project["collection"])
            if collection:
                lines.append(f'<p class="project-card__collection">Collection <a href="/collections/{e(collection["slug"])}/">{e(collection["titre"])}</a></p>')
            if project["sortiePrevue"]:
                lines.append(f'<p class="project-card__release">sortie prévue {e(project["sortiePrevue"])}</p>')
            cards.append(
                f"""
<article class="project-card">
  <h2>{e(project['titre'])}</h2>
  {''.join(lines)}
</article>""".strip()
            )
        if not cards:
            return ""
        return f'<section class="section section--white"><div class="container"><div class="project-grid">{"".join(cards)}</div></div></section>'
