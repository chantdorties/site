// Les blocs de mise en forme proposés dans le corps des pages et des actualités :
// « Texte mis en valeur », « Encadré » et « Séparateur ».
//
// L’ancien site, écrit sous Nvu, laissait colorer, centrer ou souligner n’importe quel
// texte. L’éditeur de Decap n’a pas de marque en ligne personnalisable : la mise en forme
// s’applique donc à un paragraphe entier, choisi dans des listes, jamais saisi.
//
// Chaque bloc s’écrit dans le texte sous une forme que tools/rendu/texte.py relit :
//
//   ::: valeur centre principale souligne        ::: encadre secondaire
//   Le texte, avec gras, liens, listes…           ### Titre facultatif
//   :::                                            Le texte
//                                                  :::
//
// Les mots de la ligne d’ouverture sont tirés d’une liste blanche, la même des deux
// côtés : les couleurs sont des rôles de la palette (Réglages du site › Apparence),
// jamais des codes. Toute option ajoutée ici doit l’être aussi dans texte.py
// (OPTIONS_BLOCS) et dans content_data.py, qui refuse une option inconnue.
(() => {
  // La traduction française de Decap 3.15 oublie le bouton barré, qui s’appelait
  // « Strikethrough ». Elle se complète ici, avant que Decap ne démarre.
  const francais = CMS.getLocale && CMS.getLocale('fr');
  const boutons = francais?.editor?.editorWidgets?.markdown;
  if (boutons && !boutons.strikethrough) boutons.strikethrough = 'Barré';

  // Decap n’accepte pas le drapeau « m » : « ^ » est le début du bloc, et la clôture
  // « ::: » doit être seule sur sa ligne, suivie d’une fin de ligne ou du texte.
  const OUVERTURE = (espece) =>
    new RegExp(`^:::[ \\t]*${espece}((?:[ \\t]+[a-z-]+)*)[ \\t]*\\n([\\s\\S]*?)\\n?:::[ \\t]*(?=\\n|$)`);
  const options = (chaine) => (chaine || '').trim().split(/\s+/).filter(Boolean);
  const bloc = (entete, corps) => `::: ${entete.filter(Boolean).join(' ')}\n${(corps || '').trim()}\n:::`;

  // L’aperçu d’un texte enrichi : celui de Decap, pour montrer gras et liens sans
  // convertisseur ici. Il est rendu en chaîne par Decap, d’où un élément React simple.
  // `fields` est la liste Immutable des champs du bloc, que Decap passe à toPreview.
  const apercuTexte = (texte, getAsset, fields) => {
    const markdown = CMS.getWidget('markdown');
    const champ = fields && fields.find((f) => f.get('name') === 'texte');
    if (!markdown || !champ || !texte) return null;
    return h(markdown.preview, { value: texte, field: champ, getAsset });
  };

  const texteEnrichi = {
    label: 'Texte',
    name: 'texte',
    widget: 'markdown',
    modes: ['rich_text'],
    buttons: ['bold', 'italic', 'strikethrough', 'link', 'bulleted-list', 'numbered-list'],
    editor_components: [],
  };

  CMS.registerEditorComponent({
    id: 'valeur',
    label: 'Texte mis en valeur',
    fields: [
      texteEnrichi,
      {
        label: 'Alignement',
        name: 'alignement',
        widget: 'select',
        default: 'gauche',
        options: [
          { label: 'À gauche, comme le reste du texte', value: 'gauche' },
          { label: 'Centré', value: 'centre' },
        ],
      },
      {
        label: 'Couleur',
        name: 'couleur',
        widget: 'select',
        default: 'normale',
        hint: 'Les couleurs du site, réglées dans Réglages du site › Apparence.',
        options: [
          { label: 'Celle du texte', value: 'normale' },
          { label: 'Couleur principale', value: 'principale' },
          { label: 'Couleur secondaire', value: 'secondaire' },
          { label: 'Couleur des liens', value: 'liens' },
        ],
      },
      { label: 'Souligné', name: 'souligne', widget: 'boolean', default: false },
    ],
    pattern: OUVERTURE('valeur'),
    fromBlock: (match) => {
      const mots = options(match[1]);
      return {
        texte: match[2],
        alignement: mots.includes('centre') ? 'centre' : 'gauche',
        couleur: ['principale', 'secondaire', 'liens'].find((m) => mots.includes(m)) || 'normale',
        souligne: mots.includes('souligne'),
      };
    },
    toBlock: (data) => bloc(
      [
        'valeur',
        data.alignement === 'centre' && 'centre',
        data.couleur && data.couleur !== 'normale' && data.couleur,
        data.souligne && 'souligne',
      ],
      data.texte,
    ),
    toPreview: (data, getAsset, fields) => {
      const classes = ['rich-text__valeur'];
      if (data.alignement === 'centre') classes.push('rich-text__valeur--centre');
      if (data.couleur && data.couleur !== 'normale') classes.push(`rich-text__valeur--${data.couleur}`);
      if (data.souligne) classes.push('rich-text__valeur--souligne');
      return h('div', { className: classes.join(' ') }, apercuTexte(data.texte, getAsset, fields));
    },
  });

  CMS.registerEditorComponent({
    id: 'encadre',
    label: 'Encadré',
    fields: [
      { label: 'Titre', name: 'titre', widget: 'string', required: false },
      texteEnrichi,
      {
        label: 'Teinte du fond',
        name: 'teinte',
        widget: 'select',
        default: 'secondaire',
        options: [
          { label: 'Douce, dans la couleur secondaire', value: 'secondaire' },
          { label: 'Douce, dans la couleur principale', value: 'principale' },
        ],
      },
    ],
    pattern: OUVERTURE('encadre'),
    fromBlock: (match) => {
      const mots = options(match[1]);
      // Le titre est la première ligne du bloc quand elle est un intertitre « ### ».
      const titre = /^###[ \t]+(.*)(?:\n|$)/.exec(match[2]);
      return {
        titre: titre ? titre[1].trim() : '',
        texte: titre ? match[2].slice(titre[0].length).replace(/^\n+/, '') : match[2],
        teinte: mots.includes('principale') ? 'principale' : 'secondaire',
      };
    },
    toBlock: (data) => {
      const titre = (data.titre || '').replace(/\s+/g, ' ').trim();
      const corps = [titre && `### ${titre}`, (data.texte || '').trim()].filter(Boolean).join('\n\n');
      return bloc(['encadre', data.teinte === 'principale' ? 'principale' : 'secondaire'], corps);
    },
    toPreview: (data, getAsset, fields) => h(
      'aside',
      { className: `rich-text__encadre rich-text__encadre--${data.teinte === 'principale' ? 'principale' : 'secondaire'}` },
      data.titre ? h('h3', { className: 'rich-text__encadre-titre' }, data.titre) : null,
      apercuTexte(data.texte, getAsset, fields),
    ),
  });

  // Decap ne montre un bloc dans l’éditeur que s’il a au moins un champ : le choix du
  // dessin du séparateur en tient lieu.
  CMS.registerEditorComponent({
    id: 'separateur',
    label: 'Séparateur',
    fields: [
      {
        label: 'Dessin',
        name: 'dessin',
        widget: 'select',
        default: 'trait',
        options: [
          { label: 'Un trait fin', value: 'trait' },
          { label: 'Trois étoiles', value: 'etoiles' },
        ],
      },
    ],
    pattern: /^(-{3,}|\*{3,}|_{3,})[ \t]*(?=\n|$)/,
    fromBlock: (match) => ({ dessin: match[1][0] === '*' ? 'etoiles' : 'trait' }),
    toBlock: (data) => (data.dessin === 'etoiles' ? '***' : '---'),
    toPreview: (data) => h('hr', { className: data.dessin === 'etoiles' ? 'rich-text__filet--etoiles' : undefined }),
  });
})();
