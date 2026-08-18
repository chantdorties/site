"""Les mots affichés à la place des codes enregistrés dans le contenu.

Le contenu stocke « album-jeunesse » ; le site écrit « Album jeunesse ». Changer un
libellé ici change le mot partout où il apparaît sur le site.
"""

from __future__ import annotations

ROLE_LABELS = {
    "auteur": "Auteur",
    "illustrateur": "Illustrateur",
    "prefacier": "Préfacier",
}

TYPE_LABELS = {
    "album": "Album",
    "album-jeunesse": "Album jeunesse",
    "mini-roman": "Mini roman",
    "mini-roman-jeunesse": "Mini roman jeunesse",
    "nouvelles": "Nouvelles",
    "recueil-de-nouvelles": "Recueil de nouvelles",
    "recueil-de-recits": "Recueil de récits",
    "recueil-de-textes": "Recueil de textes",
    "roman": "Roman",
    "roman-jeunesse": "Roman jeunesse",
    "texte-illustre": "Texte illustré",
}

BINDING_LABELS = {
    "souple": "Souple",
    "cartonne": "Cartonnée",
}

NEWS_TYPE_LABELS = {
    "salon": "Salon",
    "parution": "Parution",
    "rencontre": "Rencontre",
    "maison": "Vie de la maison",
}
