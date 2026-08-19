"""Le traitement des textes libres saisis dans l'administration.

`markdown_html` convertit en HTML le balisage produit par l'éditeur enrichi de Decap.
`markdown_inline` fait de même pour les textes qui vivent déjà dans un paragraphe ou
dans un lien, et n'admet donc aucun bloc. `texte_brut` fait l'inverse : il retire le
balisage pour les endroits qui exigent du texte nu — description de référencement,
données structurées, résumé posé à l'intérieur d'un lien.

`editorial_link` fabrique le lien d'un bouton ou d'une entrée de liste, selon qu'il
pointe vers un document, un livre, une page ou un site externe.

RÈGLE DE SÛRETÉ, à ne jamais inverser : le texte est échappé par `e()` AVANT que la
moindre balise ne soit fabriquée, et le HTML n'est ensuite introduit que par les règles
explicites de ce fichier. Un « < » saisi par la rédaction est donc devenu « &lt; » avant
la première règle : aucune balise ne peut venir du contenu, et les contournements par
entité — « &#x6a;avascript: » — sont du texte littéral par construction. C'est aussi
pourquoi ce fichier n'utilise pas de bibliothèque markdown : toutes fabriquent le HTML
depuis la source et échappent en interne, ce qui est exactement l'ordre inverse.
"""

from __future__ import annotations

import re
from typing import Any

from .icones import icon
from .outils import e

# Les seuls schémas qu'un lien saisi peut porter. Une liste blanche, parce qu'une liste
# noire de « javascript: » se contourne par encodage.
SCHEMAS_AUTORISES = re.compile(r"^(?:https?://|mailto:|/|#)")

# Les titres saisis dans un texte commencent à <h3> : la page porte déjà son <h1> et les
# sections leur <h2>.
NIVEAU_TITRE_MIN = 3

_RE_TITRE = re.compile(r"^(#{1,6})[ \t]+(.*)$")
_RE_FILET = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})[ \t]*$")
_RE_PUCE = re.compile(r"^[-*+][ \t]+(.*)$")
_RE_NUMERO = re.compile(r"^\d{1,9}[.)][ \t]+(.*)$")
_RE_CITATION = re.compile(r"^>[ \t]?(.*)$")
_RE_CLOTURE = re.compile(r"^(?:```|~~~)[ \t]*[\w+-]*[ \t]*$")

# Motifs appliqués sur du texte DÉJÀ ÉCHAPPÉ : le guillemet d'un titre de lien y est
# devenu « &quot; », l'esperluette « &amp; ».
_RE_CODE = re.compile(r"`([^`]+)`")
_RE_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:[ \t]+&quot;(.*?)&quot;)?\)")
_RE_LIEN = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:[ \t]+&quot;(.*?)&quot;)?\)")
_RE_URL_NUE = re.compile(r"(?<![\w@])(https?://[^\s]+)")
_RE_COURRIEL = re.compile(r"(?<![\w@])([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})")
_RE_FORT = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", re.DOTALL)
_RE_BARRE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~", re.DOTALL)
_RE_ITALIQUE_ETOILE = re.compile(r"(?<![\w*])\*(?=\S)([^*]+?)(?<=\S)\*(?![\w*])")
_RE_ITALIQUE_TIRET = re.compile(r"(?<![\w_])_(?=\S)([^_]+?)(?<=\S)_(?![\w_])")

# Sur le texte brut, celle-là : une image seule dans son paragraphe devient une figure,
# alors qu'au fil d'une phrase elle doit rester une simple image en ligne — un <figure>
# posé dans un <p> le romprait, et le navigateur réécrirait la page en silence.
_RE_IMAGE_SEULE = re.compile(r'^!\[([^\]]*)\]\(([^)\s]+)(?:[ \t]+"(.*?)")?\)$')

_RE_JETON = re.compile(r"\x00(\d+)\x00")
# Ponctuation qu'une adresse écrite au fil du texte ne prend presque jamais, mais que la
# phrase qui la porte, elle, pose juste après.
_RE_PONCTUATION_FINALE = re.compile(r"(?:[.,;:!?]|&quot;|&#x27;|&gt;|&lt;)+$")


def _normaliser(texte: str) -> str:
    """Uniformise les fins de ligne et évacue les caractères de contrôle.

    Les retirer n'est pas cosmétique : c'est ce qui garantit qu'un « \\x00 » saisi ne
    puisse jamais se faire passer pour un jeton de substitution.
    """
    texte = texte.replace("\r\n", "\n").replace("\r", "\n")
    texte = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", texte)
    return texte.expandtabs(4)


def _indentation(ligne: str) -> int:
    return len(ligne) - len(ligne.lstrip(" "))


def _ouvre_un_bloc(nu: str) -> bool:
    return bool(
        _RE_TITRE.match(nu)
        or _RE_FILET.match(nu)
        or _RE_CITATION.match(nu)
        or _RE_PUCE.match(nu)
        or _RE_NUMERO.match(nu)
        or _RE_CLOTURE.match(nu)
    )


def _decouper_blocs(texte: str) -> list[tuple[str, Any]]:
    """Découpe le texte BRUT en blocs, avant tout échappement.

    Avant, et non après : le « > » d'une citation serait devenu « &gt; » et ne se
    reconnaîtrait plus. Les marqueurs sont retirés ici, jamais réémis plus loin.
    """
    lignes = _normaliser(texte).split("\n")
    blocs: list[tuple[str, Any]] = []
    i = 0
    while i < len(lignes):
        ligne = lignes[i]
        if not ligne.strip():
            i += 1
            continue
        nu = ligne.lstrip(" ")

        cloture = _RE_CLOTURE.match(nu)
        if cloture:
            i += 1
            corps = []
            while i < len(lignes) and not _RE_CLOTURE.match(lignes[i].lstrip(" ")):
                corps.append(lignes[i])
                i += 1
            i += 1  # la clôture fermante
            blocs.append(("code", "\n".join(corps)))
            continue

        if _RE_FILET.match(nu):
            blocs.append(("filet", None))
            i += 1
            continue

        titre = _RE_TITRE.match(nu)
        if titre:
            blocs.append(("titre", (len(titre.group(1)), titre.group(2).strip())))
            i += 1
            continue

        if _RE_CITATION.match(nu):
            interieur = []
            while i < len(lignes):
                citation = _RE_CITATION.match(lignes[i].lstrip(" "))
                if not citation:
                    if lignes[i].strip():
                        break
                    # Une ligne vide clôt la citation, sauf si elle est elle-même citée.
                    break
                interieur.append(citation.group(1))
                i += 1
            blocs.append(("citation", "\n".join(interieur)))
            continue

        if _RE_PUCE.match(nu) or _RE_NUMERO.match(nu):
            bloc, i = _parser_liste(lignes, i)
            blocs.append(bloc)
            continue

        paragraphe = []
        while i < len(lignes) and lignes[i].strip():
            suivante = lignes[i].lstrip(" ")
            if paragraphe and _ouvre_un_bloc(suivante):
                break
            paragraphe.append(suivante)
            i += 1
        blocs.append(("paragraphe", "\n".join(paragraphe)))
    return blocs


def _parser_liste(lignes: list[str], depart: int) -> tuple[tuple[str, Any], int]:
    """Lit une liste et ses éventuelles sous-listes.

    Le contenu de chaque entrée est réinjecté dans `_decouper_blocs` : l'imbrication
    est donc gérée par la récursion, sans règle particulière.
    """
    indent = _indentation(lignes[depart])
    ordonnee = bool(_RE_NUMERO.match(lignes[depart].lstrip(" ")))
    motif = _RE_NUMERO if ordonnee else _RE_PUCE
    entrees: list[str] = []
    i = depart
    while i < len(lignes):
        ligne = lignes[i]
        if not ligne.strip():
            # Une ligne vide ne clôt la liste que si la suivante n'en fait plus partie.
            suite = i + 1
            while suite < len(lignes) and not lignes[suite].strip():
                suite += 1
            if suite >= len(lignes) or _indentation(lignes[suite]) < indent:
                break
            if _indentation(lignes[suite]) == indent and not motif.match(lignes[suite].lstrip(" ")):
                break
            i = suite
            continue
        if _indentation(ligne) < indent:
            break
        nu = ligne.lstrip(" ")
        entree = motif.match(nu) if _indentation(ligne) == indent else None
        if entree:
            corps = [entree.group(1)]
            i += 1
            while i < len(lignes):
                if not lignes[i].strip():
                    suite = i + 1
                    while suite < len(lignes) and not lignes[suite].strip():
                        suite += 1
                    if suite >= len(lignes) or _indentation(lignes[suite]) <= indent:
                        break
                    corps.append("")
                    i = suite
                    continue
                if _indentation(lignes[i]) <= indent:
                    break
                corps.append(lignes[i])
                i += 1
            entrees.append(_desindenter(corps))
            continue
        if _indentation(ligne) == indent:
            break  # un marqueur de l'autre espèce : c'est une nouvelle liste
        break
    return ("liste_ordonnee" if ordonnee else "liste", entrees), i


def _desindenter(corps: list[str]) -> str:
    """Retire aux lignes de continuation le décalage du marqueur qui les portait."""
    suite = [ligne for ligne in corps[1:] if ligne.strip()]
    if suite:
        retrait = min(_indentation(ligne) for ligne in suite)
        corps = [corps[0]] + [ligne[retrait:] if ligne.strip() else "" for ligne in corps[1:]]
    return "\n".join(corps)


class OutilsTexte:
    # ------------------------------------------------------------------ markdown

    def markdown_html(
        self,
        value: Any,
        *,
        internal_links: dict[str, str] | None = None,
        niveau_min: int = NIVEAU_TITRE_MIN,
        owner: str = "",
    ) -> str:
        """Convertit en HTML le balisage saisi dans l'administration.

        Voir la règle de sûreté en tête de fichier : on échappe d'abord, on balise
        ensuite. Ce qui n'est pas reconnu reste du texte, jamais une erreur silencieuse.
        """
        blocs = _decouper_blocs(str(value or ""))
        return "".join(
            self._rendre_bloc(bloc, internal_links=internal_links, niveau_min=niveau_min, owner=owner)
            for bloc in blocs
        )

    def markdown_inline(
        self,
        value: Any,
        *,
        internal_links: dict[str, str] | None = None,
        owner: str = "",
    ) -> str:
        """La mise en forme au fil du texte, sans aucun bloc.

        Pour les textes déjà posés dans un <p> ou dans un <a> : un <ul> ou un <a> y
        seraient imbriqués dans un élément qui ne les admet pas, et le navigateur
        réécrirait la page en silence.
        """
        texte = re.sub(r"\s*\n\s*", " ", _normaliser(str(value or ""))).strip()
        return self._inline(texte, internal_links=internal_links, owner=owner)

    def texte_brut(self, value: Any) -> str:
        """Retire le balisage, sans rien échapper ni fabriquer de HTML.

        Ses appelants gardent leur `e()`, leur `truncate()` ou leur `json.dumps` : cette
        fonction s'insère avant eux, elle ne les remplace pas.
        """
        texte = _normaliser(str(value or ""))
        texte = re.sub(r"^(?:```|~~~)[ \t]*[\w+-]*[ \t]*$", "", texte, flags=re.MULTILINE)
        texte = re.sub(r"^[ \t]*>[ \t]?", "", texte, flags=re.MULTILINE)
        texte = re.sub(r"^[ \t]*#{1,6}[ \t]+", "", texte, flags=re.MULTILINE)
        texte = re.sub(r"^[ \t]*(?:-{3,}|\*{3,}|_{3,})[ \t]*$", "", texte, flags=re.MULTILINE)
        texte = re.sub(r"^[ \t]*[-*+][ \t]+", "", texte, flags=re.MULTILINE)
        texte = re.sub(r"^[ \t]*\d{1,9}[.)][ \t]+", "", texte, flags=re.MULTILINE)
        texte = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", texte)
        texte = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texte)
        texte = re.sub(r"`([^`]+)`", r"\1", texte)
        # Les marqueurs d'emphase ne sont retirés que par paires : ainsi un astérisque
        # ou un souligné isolé, qui appartient à la prose, est laissé tel quel.
        texte = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"\1", texte, flags=re.DOTALL)
        texte = re.sub(r"~~(?=\S)(.+?)(?<=\S)~~", r"\1", texte, flags=re.DOTALL)
        texte = re.sub(r"(?<![\w*])\*(?=\S)([^*]+?)(?<=\S)\*(?![\w*])", r"\1", texte)
        texte = re.sub(r"(?<![\w_])_(?=\S)([^_]+?)(?<=\S)_(?![\w_])", r"\1", texte)
        return re.sub(r"\s+", " ", texte).strip()

    # ------------------------------------------------------------------ interne

    def _rendre_bloc(
        self,
        bloc: tuple[str, Any],
        *,
        internal_links: dict[str, str] | None,
        niveau_min: int,
        owner: str,
    ) -> str:
        espece, charge = bloc
        enligne = lambda texte: self._inline(texte, internal_links=internal_links, owner=owner)

        if espece == "paragraphe":
            seule = _RE_IMAGE_SEULE.match(charge.strip())
            if seule:
                return self._figure_html(seule.group(1), seule.group(2), seule.group(3), owner)
            rendu = enligne(charge)
            return f"<p>{rendu}</p>" if rendu else ""
        if espece == "titre":
            niveau, texte = charge
            balise = f"h{min(niveau + niveau_min - 1, 6)}"
            return f"<{balise}>{enligne(texte)}</{balise}>"
        if espece == "filet":
            return "<hr>"
        if espece == "code":
            return f"<pre><code>{e(charge)}</code></pre>"
        if espece == "citation":
            interieur = self.markdown_html(
                charge, internal_links=internal_links, niveau_min=niveau_min, owner=owner
            )
            return f"<blockquote>{interieur}</blockquote>"
        if espece in {"liste", "liste_ordonnee"}:
            balise = "ol" if espece == "liste_ordonnee" else "ul"
            entrees = []
            for entree in charge:
                blocs = _decouper_blocs(entree)
                if len(blocs) == 1 and blocs[0][0] == "paragraphe":
                    entrees.append(f"<li>{enligne(blocs[0][1])}</li>")
                else:
                    # Le texte qui ouvre l'entrée reste nu : l'envelopper dans un <p>
                    # écarterait la sous-liste de la ligne à laquelle elle se rapporte.
                    morceaux = []
                    for rang, sous in enumerate(blocs):
                        if rang == 0 and sous[0] == "paragraphe":
                            morceaux.append(enligne(sous[1]))
                            continue
                        morceaux.append(
                            self._rendre_bloc(
                                sous, internal_links=internal_links, niveau_min=niveau_min, owner=owner
                            )
                        )
                    entrees.append(f"<li>{''.join(morceaux)}</li>")
            return f"<{balise}>{''.join(entrees)}</{balise}>" if entrees else ""
        raise ValueError(f"espèce de bloc inconnue : {espece}")

    def _inline(
        self,
        texte: str,
        *,
        internal_links: dict[str, str] | None = None,
        owner: str = "",
    ) -> str:
        """Applique les règles au fil du texte, sur du texte échappé.

        Chaque fragment de HTML fabriqué est aussitôt remplacé par un jeton, pour
        qu'aucune règle suivante ne puisse le rouvrir — l'autolieur, notamment, ne doit
        pas retraiter l'adresse d'un lien qu'on vient d'écrire.
        """
        if not texte:
            return ""
        jetons: list[str] = []

        def jeton(html: str) -> str:
            jetons.append(html)
            return f"\x00{len(jetons) - 1}\x00"

        escaped = e(texte)
        escaped = _RE_CODE.sub(lambda m: jeton(f"<code>{m.group(1)}</code>"), escaped)
        escaped = _RE_IMAGE.sub(lambda m: jeton(self._image_html(m, owner)), escaped)
        escaped = _RE_LIEN.sub(lambda m: self._lien_html(m, jeton, owner), escaped)
        escaped = _RE_URL_NUE.sub(lambda m: self._autolien(m, jeton), escaped)
        escaped = _RE_COURRIEL.sub(
            lambda m: jeton(f'<a href="mailto:{m.group(1)}">{m.group(1)}</a>'), escaped
        )
        for label, href in (internal_links or {}).items():
            cible = e(label)
            if cible and cible in escaped:
                escaped = escaped.replace(cible, jeton(f'<a href="{e(href)}">{cible}</a>'))
        escaped = _RE_FORT.sub(lambda m: f"<strong>{m.group(1)}</strong>", escaped)
        escaped = _RE_BARRE.sub(lambda m: f"<del>{m.group(1)}</del>", escaped)
        escaped = _RE_ITALIQUE_ETOILE.sub(lambda m: f"<em>{m.group(1)}</em>", escaped)
        escaped = _RE_ITALIQUE_TIRET.sub(lambda m: f"<em>{m.group(1)}</em>", escaped)
        return _RE_JETON.sub(lambda m: jetons[int(m.group(1))], escaped)

    def _image_html(self, match: re.Match[str], owner: str) -> str:
        """L'image au fil d'une phrase : une balise seule, sans figure ni légende."""
        return self._balise_image(match.group(1), match.group(2), owner)

    def _figure_html(self, alt: str, chemin: str, titre: str | None, owner: str) -> str:
        """L'image qui occupe seule son paragraphe, avec sa légende s'il y en a une."""
        balise = self._balise_image(e(alt), chemin, owner)
        legende = f"<figcaption>{e(titre)}</figcaption>" if titre else ""
        return f'<figure class="rich-text__figure">{balise}{legende}</figure>'

    def _balise_image(self, alt: str, chemin: str, owner: str) -> str:
        """La balise elle-même. `alt` arrive déjà échappé, `chemin` vient de nos tables."""
        source = getattr(self, "inline_media", {}).get(chemin)
        if not source:
            # La validation garantit que le fichier existe : une absence ici signale une
            # image citée par une fiche que la génération n'a pas parcourue.
            raise ValueError(f"{owner or 'texte'} : image au fil du texte non préparée — {chemin}")
        dimensions = getattr(self, "inline_media_dimensions", {}).get(chemin)
        taille = f' width="{dimensions[0]}" height="{dimensions[1]}"' if dimensions else ""
        return f'<img src="{source}" alt="{alt}" loading="lazy"{taille}>'


    def _lien_html(self, match: re.Match[str], jeton, owner: str) -> str:
        libelle, href, titre = match.group(1), match.group(2), match.group(3)
        if not SCHEMAS_AUTORISES.match(href):
            # Ni erreur ni lien : le texte reste tel qu'il a été saisi, et la génération
            # le signale pour qu'on puisse le corriger.
            self.signaler_lien_refuse(href, owner)
            return match.group(0)
        attributs = f' title="{titre}"' if titre else ""
        if href.startswith("http"):
            attributs += ' target="_blank" rel="noopener noreferrer"'
        return jeton(f'<a href="{href}"{attributs}>{libelle}</a>')

    def _autolien(self, match: re.Match[str], jeton) -> str:
        adresse = match.group(1)
        # La phrase qui porte l'adresse pose sa ponctuation juste après elle ; et la
        # parenthèse fermante n'appartient à l'adresse que si elle en ouvre une.
        fin = ""
        while True:
            coupe = _RE_PONCTUATION_FINALE.search(adresse)
            if coupe:
                fin = adresse[coupe.start():] + fin
                adresse = adresse[: coupe.start()]
                continue
            if adresse.endswith(")") and adresse.count("(") < adresse.count(")"):
                fin = ")" + fin
                adresse = adresse[:-1]
                continue
            break
        if not adresse:
            return match.group(0)
        lien = f'<a href="{adresse}" target="_blank" rel="noopener noreferrer">{adresse}</a>'
        return jeton(lien) + fin

    def signaler_lien_refuse(self, href: str, owner: str) -> None:
        """Consigne un lien dont le schéma n'est pas autorisé.

        Redéfinie par le constructeur, qui tient le journal de génération ; définie ici
        pour que le convertisseur reste utilisable seul, notamment par les tests.
        """
        liens = getattr(self, "liens_refuses", None)
        if liens is not None:
            liens.append((owner, href))

    # ------------------------------------------------------------------ liens éditoriaux

    def editorial_link(self, link: dict[str, Any]) -> str | None:
        link_type = link["type"]
        label = link.get("texte") or "Consulter le lien"
        if link_type == "document":
            href = self.document_media.get(link["href"])
            if not href:
                return None
            return f'<a href="{href}" target="_blank">{icon("file")} {e(label)}</a>'
        if link_type == "livre":
            return f'<a href="/livres/{e(link["slug"])}/">{e(label)}</a>'
        if link_type == "page":
            href = "/" if link["slug"] == "accueil" else f'/{link["slug"]}/'
            return f'<a href="{href}">{e(label)}</a>'
        href = link.get("href")
        if not href:
            return None
        if link_type == "externe":
            display = link.get("texte") or re.sub(r"^https?://(?:www\.)?", "", href).rstrip("/")
            return f'<a href="{e(href)}" target="_blank" rel="noopener noreferrer">{e(display)} {icon("external")}</a>'
        return f'<a href="{e(href)}">{e(label)}</a>'
