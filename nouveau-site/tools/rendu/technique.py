"""Les fichiers destinés aux machines, jamais lus par un visiteur.

Les redirections .htaccess conduisent les anciennes adresses du site précédent vers
les nouvelles ; sitemap.xml et robots.txt renseignent les moteurs de recherche.
"""

from __future__ import annotations

from typing import Any

from .outils import absolute_url, e, write_text


class FichiersTechniques:
    def build_redirects(self) -> None:
        redirects: dict[str, str] = {}

        def add_old_addresses(record: dict[str, Any], target: str) -> None:
            for source in record.get("anciensSlugs", []):
                normalized = "/" + source.strip().lstrip("/")
                if normalized != target:
                    redirects[normalized] = target

        # Les redirections sont construites sur le contenu brut : un contenu
        # retiré du site (brouillon ou archivé) doit continuer à rediriger ses
        # anciennes adresses, vers sa rubrique parente à défaut de sa page.
        published = {
            "books": {book["slug"] for book in self.books},
            "people": {person["slug"] for person in self.people},
            "collections": {item["slug"] for item in self.collections},
            "pages": {
                page["slug"]
                for page in self.pages
                if not (page["aVerifier"] and not self.include_drafts)
            },
        }

        for book in self.raw["books"]:
            slug = book["slug"]
            target = f"/livres/{slug}/" if slug in published["books"] else "/catalogue/"
            source = self.legacy["livres"].get(slug)
            if source and source.lower() != "index.html":
                redirects[f"/{source}"] = target
            add_old_addresses(book, target)
        for person in self.raw["people"]:
            slug = person["slug"]
            target = f"/personnes/{slug}/" if slug in published["people"] else "/personnes/"
            add_old_addresses(person, target)
        for collection in self.raw["collections"]:
            slug = collection["slug"]
            target = (
                f"/collections/{slug}/" if slug in published["collections"] else "/collections/"
            )
            source = self.legacy["collections"].get(slug)
            if source:
                redirects[f"/{source}"] = target
            add_old_addresses(collection, target)
        for page in self.raw["pages"]:
            slug = page["slug"]
            if slug in {"entree", "accueil"}:
                continue
            target = f"/{slug}/" if slug in published["pages"] else "/la-maison/"
            source = self.legacy["pages"].get(slug)
            if source:
                redirects[f"/{source}"] = target
            add_old_addresses(page, target)
        for item in self.raw["news"]:
            add_old_addresses(item, "/actualites/")
        redirects.update(
            {
                "/auteurs.html": "/personnes/",
                "/illustrateurs.html": "/personnes/",
                "/accueil.html": "/",
                "/accueil-1.html": "/",
                "/accueil-2.html": "/",
                "/accueil-3.html": "/",
                "/accueil-juillet2026.html": "/",
            }
        )
        # Hébergement Free : le .htaccess est bien lu, mais seules certaines
        # directives sont acceptées. mod_rewrite est absent : ne jamais ajouter
        # de RewriteRule ici. Les types MIME sont déclarés car le serveur ne
        # connaît pas toujours le WebP, et un module JavaScript est refusé par
        # le navigateur si son type est incorrect.
        lines = [
            "# Fichier produit par tools/build-site.py : ne pas modifier à la main.",
            "Options -Indexes -ExecCGI -Includes",
            "ErrorDocument 404 /404.html",
            "",
            "AddType image/webp .webp",
            "AddType application/json .json",
            "AddType application/pdf .pdf",
            "AddType text/javascript .js",
            "",
        ]
        for source, target in sorted(redirects.items(), key=lambda item: item[0].lower()):
            lines.append(f'Redirect 301 "{source}" "{target}"')
        write_text(self.temp_output / ".htaccess", "\n".join(lines) + "\n")

    def build_machine_files(self) -> None:
        routes = sorted(set(self.generated_routes))
        entries = "".join(
            f"  <url><loc>{e(absolute_url(self.base_url, route))}</loc></url>\n"
            for route in routes
        )
        sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}</urlset>\n'
        write_text(self.temp_output / "sitemap.xml", sitemap)
        write_text(
            self.temp_output / "robots.txt",
            f"User-agent: *\nAllow: /\n\nSitemap: {self.base_url}/sitemap.xml\n",
        )

