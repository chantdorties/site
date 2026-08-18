"""La page affichée quand une adresse n'existe pas.

Elle reste volontairement courte : le code 404, une explication d'une phrase, et un
bouton qui ramène au catalogue.

Le style correspondant est dans frontend/assets/css/42-page-404.css. La page pose
aussi la classe « not-found-page » sur le <body>, prête à servir, mais aucune
règle ne s'en sert aujourd'hui.
"""

from __future__ import annotations


class Page404:
    def build_404(self) -> None:
        content = """
<section class="error-page"><div><p class="error-code">404</p><h1>Page introuvable</h1><p>Cette page a peut-être changé d’adresse.</p><a class="button" href="/catalogue/">Revenir au catalogue</a></div></section>"""
        page = self.render_page(
            title="Page introuvable",
            description="La page demandée est introuvable.",
            route="/404.html",
            content=content,
            active="",
            body_class="not-found-page",
        )
        self.write_route("/404.html", page)

