"""Le pied de page, présent en bas de chaque page.

Trois colonnes : le logo avec la présentation de la maison, une liste de liens de
navigation, puis les informations de contact. Dessous, l'année et le bouton de retour
en haut de page.

Les textes et les liens viennent de content/reglages/pied-de-page.json et
content/reglages/site.json ; ils se modifient depuis l'administration.

Le style correspondant est dans frontend/assets/css/site.css :
règles .site-footer, .footer-grid, .footer-identity, .footer-links, .footer-bottom
"""

from __future__ import annotations

from datetime import datetime

from ..icones import icon
from ..outils import e


class PiedDePage:
    def render_footer(self) -> str:
        legal_link = ""
        legal_page = self.pages_by_slug.get("mentions-legales")
        if legal_page and (self.include_drafts or not legal_page["aVerifier"]):
            legal_link = (
                '<li><a href="/mentions-legales/">'
                f'{e(self.footer_settings["libelleMentions"])}</a></li>'
            )
        navigation_links = "".join(
            f'<li><a href="{e(item["url"])}">{e(item["libelle"])}</a></li>'
            for item in sorted(
                self.footer_settings["liensNavigation"],
                key=lambda item: (item["ordre"], item["url"]),
            )
        )
        email = self.site_settings["courriel"]
        facebook = self.site_settings["facebook"]
        return f"""
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-identity">
        <img class="footer-logo" src="/assets/images/chantdorties-logo.webp" alt="" width="245" height="241" loading="lazy">
        <div>
          <p class="footer-brand">{e(self.site_settings['nom'])}</p>
          <p class="footer-intro">{e(self.footer_settings['presentation'])}</p>
        </div>
      </div>
      <div>
        <h2 class="footer-title">{e(self.footer_settings['titreNavigation'])}</h2>
        <ul class="footer-links">
          {navigation_links}
        </ul>
      </div>
      <div>
        <h2 class="footer-title">{e(self.footer_settings['titreInformations'])}</h2>
        <ul class="footer-links">
          <li><a href="mailto:{e(email)}">{e(email)}</a></li>
          <li><a href="{e(facebook)}" target="_blank" rel="noopener noreferrer">{e(self.footer_settings['libelleFacebook'])} {icon("external")}</a></li>
          <li><a href="/manuscrits/">{e(self.footer_settings['libelleManuscrits'])}</a></li>
          <li><a href="/plan-du-site/">{e(self.footer_settings['libellePlan'])}</a></li>
          {legal_link}
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© {datetime.now().year} {e(self.site_settings['nom'])}</span>
      <button class="icon-button back-to-top" type="button" data-back-to-top hidden title="Revenir en haut">
        {icon("arrow-up", label="Revenir en haut")}
      </button>
    </div>
  </div>
</footer>""".strip()

