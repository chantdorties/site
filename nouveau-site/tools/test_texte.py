#!/usr/bin/env python3
"""Les tests du convertisseur de textes libres.

Le premier groupe est le plus important : il vérifie que rien de ce qu'une personne
peut saisir ne devient une balise. Tant qu'il ne passe pas, le convertisseur ne doit
être branché nulle part.
"""

import unittest

from tools.rendu.texte import OutilsTexte


class Convertisseur(OutilsTexte):
    """Le convertisseur seul, avec les tables que le constructeur lui fournit d'ordinaire."""

    def __init__(self, inline_media=None, dimensions=None):
        self.inline_media = inline_media or {}
        self.inline_media_dimensions = dimensions or {}
        self.liens_refuses = []


class SuretéTest(unittest.TestCase):
    def setUp(self):
        self.t = Convertisseur()

    def test_le_html_saisi_reste_du_texte(self):
        rendu = self.t.markdown_html("Bonjour <script>alert(1)</script> et <b>gras</b>")
        self.assertNotIn("<script>", rendu)
        self.assertNotIn("<b>", rendu)
        self.assertIn("&lt;script&gt;", rendu)

    def test_un_lien_javascript_est_refuse(self):
        rendu = self.t.markdown_html("[cliquer](javascript:alert(1))")
        self.assertNotIn("<a", rendu)
        self.assertIn("javascript", rendu)
        self.assertEqual(self.t.liens_refuses, [("", "javascript:alert(1")])

    def test_un_lien_javascript_deguise_par_la_casse_est_refuse(self):
        self.assertNotIn("<a", self.t.markdown_html("[x](JaVaScRiPt:alert(1))"))

    def test_un_lien_data_est_refuse(self):
        self.assertNotIn("<a", self.t.markdown_html("[x](data:text/html;base64,PHNjcmlwdD4=)"))

    def test_une_entite_ne_reconstitue_pas_un_schema(self):
        # Sans l'échappement préalable, « &#x6a;avascript: » redeviendrait « javascript: »
        # au moment où le navigateur lit l'attribut.
        rendu = self.t.markdown_html("[x](&#x6a;avascript:alert(1))")
        self.assertNotIn("<a", rendu)
        self.assertIn("&amp;#x6a;", rendu)

    def test_un_guillemet_dans_un_libelle_ne_casse_pas_l_attribut(self):
        rendu = self.t.markdown_html('[dis "bonjour"](https://exemple.fr/)')
        self.assertIn("&quot;", rendu)
        self.assertIn('<a href="https://exemple.fr/"', rendu)

    def test_une_esperluette_survit_dans_une_adresse(self):
        rendu = self.t.markdown_html("[voir](https://exemple.fr/?a=1&b=2)")
        self.assertIn('href="https://exemple.fr/?a=1&amp;b=2"', rendu)

    def test_les_liens_externes_portent_leur_garde(self):
        rendu = self.t.markdown_html("[voir](https://exemple.fr/)")
        self.assertIn('rel="noopener noreferrer"', rendu)
        self.assertIn('target="_blank"', rendu)

    def test_un_lien_interne_ne_s_ouvre_pas_dans_un_onglet(self):
        rendu = self.t.markdown_html("[la maison](/maison/)")
        self.assertIn('<a href="/maison/">', rendu)
        self.assertNotIn("target", rendu)

    def test_un_caractere_de_controle_ne_se_fait_pas_passer_pour_un_jeton(self):
        rendu = self.t.markdown_html("avant \x000\x00 après **gras**")
        self.assertIn("<strong>gras</strong>", rendu)
        self.assertNotIn("\x00", rendu)


class BlocsTest(unittest.TestCase):
    def setUp(self):
        self.t = Convertisseur()

    def test_une_ligne_vide_separe_deux_paragraphes(self):
        self.assertEqual(self.t.markdown_html("Un.\n\nDeux."), "<p>Un.</p><p>Deux.</p>")

    def test_un_retour_simple_ne_separe_pas(self):
        self.assertEqual(self.t.markdown_html("Un\ndeux"), "<p>Un\ndeux</p>")

    def test_un_retour_force_passe_a_la_ligne_sans_nouveau_paragraphe(self):
        # Maj+Entrée dans Decap écrit une barre oblique inverse en fin de ligne : une
        # adresse postale garde une ligne par information.
        self.assertEqual(
            self.t.markdown_html("Publico\\\n145 rue Amelot  \n75011 Paris"),
            "<p>Publico<br>145 rue Amelot<br>75011 Paris</p>",
        )

    def test_le_retour_force_disparait_du_texte_brut(self):
        self.assertEqual(self.t.texte_brut("Publico\\\n145 rue Amelot"), "Publico 145 rue Amelot")
        self.assertEqual(self.t.markdown_inline("Publico\\\n145 rue Amelot"), "Publico 145 rue Amelot")

    def test_les_titres_commencent_au_troisieme_niveau(self):
        self.assertEqual(self.t.markdown_html("# Titre"), "<h3>Titre</h3>")
        self.assertEqual(self.t.markdown_html("### Titre"), "<h5>Titre</h5>")

    def test_les_titres_ne_depassent_pas_le_sixieme_niveau(self):
        self.assertEqual(self.t.markdown_html("###### Titre"), "<h6>Titre</h6>")

    def test_une_liste_a_puces(self):
        self.assertEqual(
            self.t.markdown_html("- un\n- deux"), "<ul><li>un</li><li>deux</li></ul>"
        )

    def test_une_liste_numerotee(self):
        self.assertEqual(
            self.t.markdown_html("1. un\n2. deux"), "<ol><li>un</li><li>deux</li></ol>"
        )

    def test_une_liste_imbriquee(self):
        rendu = self.t.markdown_html("- un\n  - un a\n- deux")
        self.assertEqual(rendu, "<ul><li>un<ul><li>un a</li></ul></li><li>deux</li></ul>")

    def test_une_citation(self):
        self.assertEqual(
            self.t.markdown_html("> une phrase"), "<blockquote><p>une phrase</p></blockquote>"
        )

    def test_un_bloc_de_code_n_est_pas_reinterprete(self):
        rendu = self.t.markdown_html("```\n**pas gras** <b>\n```")
        self.assertEqual(rendu, "<pre><code>**pas gras** &lt;b&gt;</code></pre>")

    def test_un_filet(self):
        self.assertEqual(self.t.markdown_html("---"), "<hr>")

    def test_un_filet_trois_etoiles(self):
        self.assertEqual(self.t.markdown_html("***"), '<hr class="rich-text__filet--etoiles">')

    def test_une_liste_interrompt_le_paragraphe(self):
        rendu = self.t.markdown_html("Voici :\n- un")
        self.assertEqual(rendu, "<p>Voici :</p><ul><li>un</li></ul>")


class EnLigneTest(unittest.TestCase):
    def setUp(self):
        self.t = Convertisseur()

    def test_gras_et_italique(self):
        self.assertEqual(
            self.t.markdown_html("**gras** et *italique*"),
            "<p><strong>gras</strong> et <em>italique</em></p>",
        )

    def test_italique_par_le_souligne(self):
        self.assertEqual(self.t.markdown_html("_ainsi_"), "<p><em>ainsi</em></p>")

    def test_un_souligne_au_milieu_d_un_mot_ne_met_rien_en_italique(self):
        self.assertEqual(
            self.t.markdown_html("nom_de_fichier_long"), "<p>nom_de_fichier_long</p>"
        )

    def test_barre_et_code(self):
        self.assertEqual(
            self.t.markdown_html("~~ancien~~ et `code`"),
            "<p><del>ancien</del> et <code>code</code></p>",
        )

    def test_markdown_inline_n_admet_aucun_bloc(self):
        rendu = self.t.markdown_inline("- un\n- deux")
        self.assertNotIn("<ul>", rendu)
        self.assertNotIn("<p>", rendu)

    def test_markdown_inline_garde_la_mise_en_forme(self):
        self.assertEqual(self.t.markdown_inline("un **mot**"), "un <strong>mot</strong>")


class AutolienTest(unittest.TestCase):
    def setUp(self):
        self.t = Convertisseur()

    def test_une_adresse_n_est_plus_tronquee(self):
        # Le motif excluait « & », « l », « t » et « ; » : cette adresse s'arrêtait à
        # « http://www. » sur le site en ligne.
        rendu = self.t.markdown_html("Voir http://www.librairie-publico.com/ ici")
        self.assertIn('href="http://www.librairie-publico.com/"', rendu)

    def test_la_ponctuation_finale_reste_hors_du_lien(self):
        rendu = self.t.markdown_html("Voir https://exemple.fr/page.")
        self.assertIn('href="https://exemple.fr/page"', rendu)
        self.assertTrue(rendu.endswith(".</p>"))

    def test_une_adresse_entre_parentheses(self):
        rendu = self.t.markdown_html("Voir (https://exemple.fr/page)")
        self.assertIn('href="https://exemple.fr/page"', rendu)

    def test_un_courriel(self):
        self.assertIn('href="mailto:bonjour@exemple.fr"', self.t.markdown_html("bonjour@exemple.fr"))

    def test_l_adresse_d_un_lien_ecrit_n_est_pas_retraitee(self):
        rendu = self.t.markdown_html("[le site](https://exemple.fr/)")
        self.assertEqual(rendu.count("<a "), 1)

    def test_les_liens_internes_nommes(self):
        rendu = self.t.markdown_html(
            "voir la page de soutien", internal_links={"page de soutien": "/soutien/"}
        )
        self.assertIn('<a href="/soutien/">page de soutien</a>', rendu)


class ImageTest(unittest.TestCase):
    def setUp(self):
        self.t = Convertisseur(
            {"content/media/uploads/salon.jpg": "/assets/media/texte/salon-abc1234567.webp"},
            {"content/media/uploads/salon.jpg": (1400, 900)},
        )

    def test_une_image_seule_devient_une_figure(self):
        rendu = self.t.markdown_html("![Un salon du livre](content/media/uploads/salon.jpg)")
        self.assertIn("<figure", rendu)
        self.assertIn('src="/assets/media/texte/salon-abc1234567.webp"', rendu)
        self.assertIn('alt="Un salon du livre"', rendu)
        self.assertIn('width="1400" height="900"', rendu)

    def test_un_titre_devient_une_legende(self):
        rendu = self.t.markdown_html('![Salon](content/media/uploads/salon.jpg "En 2024")')
        self.assertIn("<figcaption>En 2024</figcaption>", rendu)

    def test_une_image_au_fil_d_une_phrase_reste_en_ligne(self):
        # Un <figure> dans un <p> romprait le paragraphe : le navigateur fermerait le <p>
        # avant la figure, et la fin de la phrase se retrouverait dans un paragraphe à part.
        rendu = self.t.markdown_html("Avant ![vignette](content/media/uploads/salon.jpg) après")
        self.assertNotIn("<figure", rendu)
        self.assertEqual(rendu.count("<p>"), 1)
        self.assertIn("<img src=", rendu)

    def test_une_image_non_preparee_arrete_la_generation(self):
        with self.assertRaises(ValueError):
            self.t.markdown_html("![x](content/media/uploads/absente.jpg)")


class TexteBrutTest(unittest.TestCase):
    def setUp(self):
        self.t = Convertisseur()

    def test_un_texte_sans_balisage_est_rendu_tel_quel(self):
        phrase = "Une maison d’édition associative, née en 2005 à Bédarieux."
        self.assertEqual(self.t.texte_brut(phrase), phrase)

    def test_le_balisage_est_retire(self):
        self.assertEqual(
            self.t.texte_brut("# Titre\n\nUn **mot** et un [lien](https://exemple.fr/)."),
            "Titre Un mot et un lien.",
        )

    def test_les_puces_et_les_citations_sont_retirees(self):
        self.assertEqual(self.t.texte_brut("> cité\n\n- un\n- deux"), "cité un deux")

    def test_une_image_laisse_son_texte_alternatif(self):
        self.assertEqual(self.t.texte_brut("![Un salon](x.jpg) suite"), "Un salon suite")

    def test_aucun_balisage_markdown_ne_produit_de_balise(self):
        for entree in ("# T", "**g**", "[l](https://e.fr)", "> c", "`c`", "- x", "---"):
            self.assertNotIn("<", self.t.texte_brut(entree))

    def test_le_html_saisi_traverse_sans_etre_interprete(self):
        # texte_brut n'échappe pas : c'est le rôle de ses appelants, qui l'entourent tous
        # d'un e(), d'un truncate() ou d'un json.dumps. Elle ne doit donc ni échapper ni
        # supprimer — seulement rendre le texte tel qu'il est, sans marqueurs markdown.
        self.assertEqual(self.t.texte_brut("<b>x</b>"), "<b>x</b>")

    def test_un_asterisque_isole_appartient_a_la_prose(self):
        self.assertEqual(self.t.texte_brut("2 * 3 = 6"), "2 * 3 = 6")



class LienEditorialTest(unittest.TestCase):
    def setUp(self):
        self.t = Convertisseur()

    def test_la_page_choisie_dans_la_liste_fait_le_lien(self):
        lien = {"type": "page", "pageCible": "soutien", "texte": "Nous soutenir"}
        self.assertEqual(self.t.editorial_link(lien), '<a href="/soutien/">Nous soutenir</a>')

    def test_l_ancienne_forme_tapee_reste_acceptee(self):
        lien = {"type": "page", "slug": "accueil", "texte": "Accueil"}
        self.assertEqual(self.t.editorial_link(lien), '<a href="/">Accueil</a>')


class BlocsDeMiseEnFormeTest(unittest.TestCase):
    """Les blocs « ::: » posés par l'éditeur (frontend/admin/blocs.js)."""

    def setUp(self):
        self.t = Convertisseur()

    def test_texte_mis_en_valeur(self):
        self.assertEqual(
            self.t.markdown_html("::: valeur centre\nUn **mot**.\n:::"),
            '<div class="rich-text__valeur rich-text__valeur--centre"><p>Un <strong>mot</strong>.</p></div>',
        )

    def test_les_classes_suivent_la_liste_blanche_et_non_la_saisie(self):
        rendu = self.t.markdown_html("::: valeur souligne liens centre\nx\n:::")
        self.assertIn(
            'class="rich-text__valeur rich-text__valeur--centre rich-text__valeur--liens '
            'rich-text__valeur--souligne"',
            rendu,
        )

    def test_une_option_inconnue_est_ignoree(self):
        # Le chargement la refuse ; le convertisseur, lui, ne la recopie jamais.
        rendu = self.t.markdown_html("::: valeur rouge centre\nx\n:::")
        self.assertNotIn("rouge", rendu)
        self.assertIn("rich-text__valeur--centre", rendu)

    def test_un_bloc_inconnu_reste_du_texte(self):
        self.assertEqual(self.t.markdown_html("::: cadre\nx\n:::"), "<p>::: cadre\nx\n:::</p>")

    def test_plusieurs_paragraphes_et_un_lien_dans_un_bloc(self):
        rendu = self.t.markdown_html("::: valeur principale\nUn.\n\nDeux [l](https://e.fr).\n:::\n\nAprès.")
        self.assertTrue(rendu.startswith('<div class="rich-text__valeur rich-text__valeur--principale"><p>Un.</p><p>Deux <a '))
        self.assertTrue(rendu.endswith("</div><p>Après.</p>"))

    def test_l_encadre_et_son_titre(self):
        self.assertEqual(
            self.t.markdown_html("::: encadre principale\n### À noter\n\nSalon.\n:::"),
            '<aside class="rich-text__encadre rich-text__encadre--principale">'
            '<h3 class="rich-text__encadre-titre">À noter</h3><p>Salon.</p></aside>',
        )

    def test_l_encadre_sans_titre(self):
        self.assertEqual(
            self.t.markdown_html("::: encadre secondaire\nSalon.\n:::"),
            '<aside class="rich-text__encadre rich-text__encadre--secondaire"><p>Salon.</p></aside>',
        )

    def test_un_bloc_vide_ne_dessine_rien(self):
        self.assertEqual(self.t.markdown_html("::: encadre secondaire\n\n:::"), "")

    def test_un_bloc_non_ferme_court_jusqu_a_la_fin(self):
        self.assertEqual(
            self.t.markdown_html("::: valeur centre\nx"),
            '<div class="rich-text__valeur rich-text__valeur--centre"><p>x</p></div>',
        )

    def test_un_bloc_interrompt_le_paragraphe(self):
        rendu = self.t.markdown_html("Avant\n::: valeur centre\nx\n:::")
        self.assertTrue(rendu.startswith("<p>Avant</p><div"))

    def test_rien_de_saisi_n_atteint_un_attribut(self):
        rendu = self.t.markdown_html('::: valeur centre" onmouseover="x\n<script>\n:::')
        # La ligne reste du texte : le guillemet saisi est échappé, aucun bloc n'est ouvert.
        self.assertNotIn('onmouseover="', rendu)
        self.assertIn("&quot;", rendu)
        self.assertNotIn("<script>", rendu)
        self.assertNotIn("<div", rendu)

    def test_le_texte_brut_perd_les_marqueurs(self):
        self.assertEqual(
            self.t.texte_brut("::: valeur centre\nUn **mot**.\n:::\n\n::: encadre secondaire\n### Titre\n\nSuite\n:::"),
            "Un mot. Titre Suite",
        )


if __name__ == "__main__":
    unittest.main()
