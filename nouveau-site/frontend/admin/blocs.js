// Les blocs de mise en forme proposés dans le corps des pages et des actualités :
// « Texte mis en valeur », « Encadré », « Séparateur », « Image placée », « Bouton »,
// « Tableau » et « Vidéo ».
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
//   ::: image droite                              ::: bouton plein livre
//   ![Texte alternatif](chemin "Légende")          [Commander](/livres/le-livre/)
//   :::                                            :::
//
//   ::: tableau entete                            ::: video
//   Format | Prix                                  https://www.youtube.com/watch?v=…
//   A4 | 12,50 €                                   Titre de la vidéo
//   :::                                            :::
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

  // Une ligne de texte sûre dans un lien ou une image : ni crochet fermant, ni
  // guillemet droit (il fermerait la légende), ni retour à la ligne.
  const uneLigne = (texte) => (texte || '').replace(/\s+/g, ' ').trim();
  const sansCrochet = (texte) => uneLigne(texte).replace(/[\[\]]/g, '');
  const IMAGE_SEULE = /^!\[([^\]]*)\]\((\S*?)(?:[ \t]+"(.*?)")?\)$/;
  const LIEN_SEUL = /^\[([^\]]*)\]\((\S*)\)$/;

  const PLACES = ['gauche', 'droite', 'centre', 'large'];
  CMS.registerEditorComponent({
    id: 'illustration',
    label: 'Image placée',
    fields: [
      { label: 'Image', name: 'image', widget: 'image', media_library: { config: { max_file_size: 20971520 } } },
      {
        label: 'Texte alternatif',
        name: 'alt',
        widget: 'string',
        hint: 'Une courte description de l’image, lue par les personnes qui ne la voient pas. Obligatoire.',
      },
      { label: 'Légende', name: 'legende', widget: 'string', required: false, hint: 'Affichée en petit sous l’image. Facultative.' },
      {
        label: 'Place',
        name: 'place',
        widget: 'select',
        default: 'droite',
        hint: 'Sur téléphone, l’image prend toujours toute la largeur.',
        options: [
          { label: 'Petite, à gauche du texte qui suit', value: 'gauche' },
          { label: 'Petite, à droite du texte qui suit', value: 'droite' },
          { label: 'Centrée', value: 'centre' },
          { label: 'Toute la largeur', value: 'large' },
        ],
      },
    ],
    pattern: OUVERTURE('image'),
    fromBlock: (match) => {
      const image = IMAGE_SEULE.exec(match[2].trim()) || [];
      return {
        image: image[2] || '',
        alt: image[1] || '',
        legende: image[3] || '',
        place: PLACES.find((place) => options(match[1]).includes(place)) || 'droite',
      };
    },
    toBlock: (data) => {
      const legende = uneLigne(data.legende).replace(/"/g, '”');
      const titre = legende ? ` "${legende}"` : '';
      const place = PLACES.includes(data.place) ? data.place : 'droite';
      return bloc(['image', place], `![${sansCrochet(data.alt)}](${uneLigne(data.image)}${titre})`);
    },
    toPreview: (data, getAsset, fields) => {
      // Comme le bloc « Image » de Decap : l’objet rendu par getAsset sert tel quel
      // d’adresse (une image tout juste déposée n’a pas encore d’adresse en texte).
      const champ = fields && fields.find((f) => f.get('name') === 'image');
      const source = data.image ? getAsset(data.image, champ) : null;
      const place = PLACES.includes(data.place) ? data.place : 'droite';
      return h(
        'figure',
        { className: `rich-text__image rich-text__image--${place}` },
        source ? h('img', { src: source, alt: data.alt || '' }) : null,
        data.legende ? h('figcaption', {}, data.legende) : null,
      );
    },
  });

  // Le bouton : une destination parmi cinq. Decap n’affiche pas un champ selon un
  // choix fait plus haut : les cinq champs « Vers… » sont donc visibles, et le
  // premier rempli l’emporte. Sa sorte est notée dans le bloc (« ::: bouton plein
  // livre ») pour que l’éditeur rouvre le bon champ.
  const CIBLES = ['page', 'livre', 'document', 'courriel', 'adresse'];
  const adresseDe = {
    page: (valeur) => (valeur === 'accueil' ? '/' : `/${valeur}/`),
    livre: (valeur) => `/livres/${valeur}/`,
    document: (valeur) => valeur,
    courriel: (valeur) => `mailto:${valeur}`,
    // « www.exemple.fr » tapé sans « https:// » serait refusé par le site.
    adresse: (valeur) => (/^(https?:\/\/|mailto:|\/|#)/.test(valeur) ? valeur : `https://${valeur}`),
  };
  const valeurDe = {
    page: (href) => (href === '/' ? 'accueil' : href.replace(/^\/|\/$/g, '')),
    livre: (href) => href.replace(/^\/livres\/|\/$/g, ''),
    document: (href) => href,
    courriel: (href) => href.replace(/^mailto:/, ''),
    adresse: (href) => href,
  };
  const RELATION = { widget: 'relation', required: false, search_fields: ['titre'], display_fields: ['titre'] };
  CMS.registerEditorComponent({
    id: 'bouton',
    label: 'Bouton',
    fields: [
      { label: 'Texte du bouton', name: 'texte', widget: 'string', hint: 'Court et actif : « Commander », « Nous écrire », « Lire l’extrait ».' },
      {
        label: 'Style',
        name: 'style',
        widget: 'select',
        default: 'plein',
        options: [
          { label: 'Plein, dans la couleur des boutons du site', value: 'plein' },
          { label: 'Discret, en simple contour', value: 'discret' },
        ],
      },
      { ...RELATION, label: 'Vers une page de « Mes pages »', name: 'page', collection: 'pages', value_field: '{{slug}}', hint: 'Remplir un seul des champs « Vers… ».' },
      { ...RELATION, label: 'Vers un livre du catalogue', name: 'livre', collection: 'livres', value_field: 'slug' },
      { label: 'Vers un document PDF', name: 'document', widget: 'file', required: false, media_library: { config: { max_file_size: 20971520 } }, hint: 'Déposer le PDF ici : le bouton le propose au téléchargement.' },
      { label: 'Vers une adresse courriel', name: 'courriel', widget: 'string', required: false, hint: 'Par exemple contact@exemple.fr. Un clic ouvre la messagerie du visiteur.' },
      { label: 'Vers une autre adresse', name: 'adresse', widget: 'string', required: false, hint: 'Un autre site (https://…), ou une page principale du site : /catalogue/, /actualites/…' },
    ],
    pattern: OUVERTURE('bouton'),
    fromBlock: (match) => {
      const mots = options(match[1]);
      const lien = LIEN_SEUL.exec(match[2].trim()) || [];
      const href = lien[2] || '';
      const cible = CIBLES.find((sorte) => mots.includes(sorte)) || 'adresse';
      return {
        texte: lien[1] || '',
        style: mots.includes('discret') ? 'discret' : 'plein',
        ...(href ? { [cible]: valeurDe[cible](href) } : {}),
      };
    },
    toBlock: (data) => {
      const cible = CIBLES.find((sorte) => uneLigne(data[sorte]));
      const href = cible ? adresseDe[cible](uneLigne(data[cible])).replace(/\s/g, '') : '';
      return bloc(
        ['bouton', data.style === 'discret' ? 'discret' : 'plein', cible],
        `[${sansCrochet(data.texte) || 'En savoir plus'}](${href})`,
      );
    },
    toPreview: (data) => {
      const pret = CIBLES.some((sorte) => uneLigne(data[sorte]));
      return h(
        'p',
        { className: 'rich-text__bouton' },
        h('span', { className: data.style === 'discret' ? 'button button--secondary' : 'button' }, data.texte || 'En savoir plus'),
        pret ? null : h('em', {}, ' — sans destination, ce bouton ne s’affichera pas'),
      );
    },
  });

  // Le tableau : Decap n’en a pas dans son éditeur. Chaque ligne a quatre cases au
  // plus ; les colonnes laissées vides partout, à droite, sont retirées. Un « | »
  // saisi dans une case est écrit « \| » pour ne pas couper la case en deux.
  const CASES = ['c1', 'c2', 'c3', 'c4'];
  const SEPARATEUR = /\s*(?<!\\)\|\s*/;
  const rangeesDu = (lignes) => {
    const rangees = (lignes || [])
      .map((ligne) => CASES.map((c) => uneLigne(ligne && ligne[c])))
      .filter((rangee) => rangee.some(Boolean));
    let largeur = CASES.length;
    while (largeur > 1 && !rangees.some((rangee) => rangee[largeur - 1])) largeur -= 1;
    return rangees.map((rangee) => rangee.slice(0, largeur));
  };
  // Dans l’aperçu, une case montre son gras, son italique et le texte de ses liens.
  const MARQUES = /(\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]*\))/;
  const caseEnLigne = (texte) => texte.split(MARQUES).filter(Boolean).map((morceau) => {
    if (/^\*\*.+\*\*$/.test(morceau)) return h('strong', {}, morceau.slice(2, -2));
    if (/^(\*|_).+\1$/.test(morceau)) return h('em', {}, morceau.slice(1, -1));
    const lien = /^\[([^\]]+)\]\(/.exec(morceau);
    return lien ? h('u', {}, lien[1]) : morceau;
  });
  CMS.registerEditorComponent({
    id: 'tableau',
    label: 'Tableau',
    fields: [
      { label: 'La première ligne donne les titres des colonnes', name: 'entete', widget: 'boolean', default: true },
      {
        label: 'Lignes',
        name: 'lignes',
        label_singular: 'ligne',
        widget: 'list',
        summary: '{{fields.c1}}',
        hint: 'Quatre colonnes au plus. Laissez vides les cases inutiles. Sur téléphone, le tableau défile de côté.',
        fields: [
          { label: 'Colonne 1', name: 'c1', widget: 'string', required: false },
          { label: 'Colonne 2', name: 'c2', widget: 'string', required: false },
          { label: 'Colonne 3', name: 'c3', widget: 'string', required: false },
          { label: 'Colonne 4', name: 'c4', widget: 'string', required: false },
        ],
      },
    ],
    pattern: OUVERTURE('tableau'),
    fromBlock: (match) => ({
      entete: options(match[1]).includes('entete'),
      lignes: match[2]
        .split('\n')
        .filter((ligne) => ligne.trim())
        .map((ligne) => {
          const cases = ligne.split(SEPARATEUR).map((c) => c.trim().replace(/\\\|/g, '|'));
          return Object.fromEntries(CASES.map((c, rang) => [c, cases[rang] || '']));
        }),
    }),
    toBlock: (data) => bloc(
      ['tableau', data.entete && 'entete'],
      rangeesDu(data.lignes)
        .map((rangee) => rangee.map((c) => c.replace(/\|/g, '\\|')).join(' | '))
        .join('\n'),
    ),
    toPreview: (data) => {
      const rangees = rangeesDu(data.lignes);
      if (!rangees.length) return h('p', {}, h('em', {}, 'Tableau vide : il ne s’affichera pas.'));
      const titres = data.entete ? rangees[0] : null;
      const corps = data.entete ? rangees.slice(1) : rangees;
      return h(
        'div',
        { className: 'rich-text__tableau' },
        h(
          'table',
          {},
          titres ? h('thead', {}, h('tr', {}, ...titres.map((c) => h('th', { scope: 'col' }, ...caseEnLigne(c))))) : null,
          h('tbody', {}, ...corps.map((rangee) => h('tr', {}, ...rangee.map((c) => h('td', {}, ...caseEnLigne(c)))))),
        ),
      );
    },
  });

  // La vidéo : seules les adresses YouTube et Vimeo sont reconnues, avec les mêmes
  // règles que tools/rendu/texte.py. Sur le site, rien n’est chargé avant le clic du
  // visiteur ; l’aperçu ne montre donc que le bouton de lecture.
  const ID_YOUTUBE = '([A-Za-z0-9_-]{11})';
  const VIDEOS = [
    ['YouTube', new RegExp(`^https?://(?:www\\.|m\\.)?youtube\\.com/watch\\?(?:[^#\\s]*&)?v=${ID_YOUTUBE}(?:[&#]\\S*)?$`)],
    ['YouTube', new RegExp(`^https?://(?:www\\.|m\\.)?youtube\\.com/(?:shorts|embed|live)/${ID_YOUTUBE}(?:[/?#]\\S*)?$`)],
    ['YouTube', new RegExp(`^https?://youtu\\.be/${ID_YOUTUBE}(?:[/?#]\\S*)?$`)],
    ['Vimeo', /^https?:\/\/(?:www\.)?vimeo\.com\/(\d{1,12})(?:\/([0-9a-f]{6,20}))?\/?(?:[?#]\S*)?$/],
    ['Vimeo', /^https?:\/\/player\.vimeo\.com\/video\/(\d{1,12})\/?(?:\?(?:[^#\s]*&)?h=([0-9a-f]{6,20}))?(?:[&#]\S*)?$/],
  ];
  const siteDe = (adresse) => (VIDEOS.find(([, motif]) => motif.test(adresse)) || [])[0];
  CMS.registerEditorComponent({
    id: 'video',
    label: 'Vidéo',
    fields: [
      {
        label: 'Adresse de la vidéo',
        name: 'adresse',
        widget: 'string',
        hint: 'Copiez l’adresse de la vidéo sur YouTube ou Vimeo, par exemple https://www.youtube.com/watch?v=…',
      },
      {
        label: 'Titre de la vidéo',
        name: 'titre',
        widget: 'string',
        hint: 'Affiché sur le bouton de lecture, et lu par les personnes qui ne voient pas l’écran. Obligatoire.',
      },
    ],
    pattern: OUVERTURE('video'),
    fromBlock: (match) => {
      const [adresse = '', ...titre] = match[2].split('\n').map((ligne) => ligne.trim()).filter(Boolean);
      return { adresse, titre: titre.join(' ') };
    },
    // Sans adresse, le bloc reste vide : le site n’affiche rien, et rien n’est refusé.
    toBlock: (data) => {
      const adresse = uneLigne(data.adresse).replace(/\s/g, '');
      return bloc(['video'], adresse ? `${adresse}\n${uneLigne(data.titre)}` : '');
    },
    toPreview: (data) => {
      const adresse = uneLigne(data.adresse).replace(/\s/g, '');
      const site = siteDe(adresse);
      return h(
        'div',
        { className: 'rich-text__video' },
        h(
          'span',
          { className: 'video-facade' },
          h('span', { className: 'video-facade__lecture', 'aria-hidden': 'true' }, '▶'),
          h('span', { className: 'video-facade__titre' }, uneLigne(data.titre) || 'Vidéo'),
          h(
            'span',
            { className: 'video-facade__mention' },
            site
              ? `Lecture sur ${site} : ce service peut déposer des cookies.`
              : adresse
                ? 'Adresse non reconnue : copiez celle d’une vidéo YouTube ou Vimeo.'
                : 'Sans adresse, cette vidéo ne s’affichera pas.',
          ),
        ),
      );
    },
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
