(() => {
  const value = (entry, name, fallback = '') => entry.getIn(['data', name]) ?? fallback;
  const assetUrl = (getAsset, path) => {
    if (!path) return '';
    const asset = getAsset(path);
    return asset ? asset.toString() : '';
  };

  // L’aperçu montrait les valeurs enregistrées — « publie », « coquelicots-sauvages »,
  // « recueil-de-nouvelles » — au lieu des mots que la personne vient de choisir.
  const LIBELLES = {
    statut: { publie: 'Publié', brouillon: 'Brouillon', archive: 'Archivé' },
    role: { auteur: 'Auteur', illustrateur: 'Illustrateur', prefacier: 'Préfacier' },
    categorie: { salon: 'Salon', parution: 'Parution', rencontre: 'Rencontre', maison: 'Vie de la maison' },
    ouvrage: {
      'album': 'Album',
      'album-jeunesse': 'Album jeunesse',
      'mini-roman': 'Mini roman',
      'mini-roman-jeunesse': 'Mini roman jeunesse',
      'nouvelles': 'Nouvelles',
      'recueil-de-nouvelles': 'Recueil de nouvelles',
      'recueil-de-recits': 'Recueil de récits',
      'recueil-de-textes': 'Recueil de textes',
      'roman': 'Roman',
      'roman-jeunesse': 'Roman jeunesse',
      'texte-illustre': 'Texte illustré'
    },
    reliure: { souple: 'Souple', cartonne: 'Cartonnée' }
  };
  const libelle = (table, cle) => (cle ? LIBELLES[table][cle] || cle : '');

  // Les relations n’enregistrent qu’une adresse : faute d’accès aux autres fiches depuis
  // l’aperçu, on la rend au moins lisible — « coquelicots-sauvages » → « coquelicots
  // sauvages ».
  const lisible = (slug) => (slug ? String(slug).replace(/-/g, ' ') : '');
  const listeLisible = (valeurs) =>
    (valeurs?.map?.(lisible) ?? []).filter(Boolean).join(', ');

  const dateFr = (valeur) => {
    if (!valeur) return '';
    const [annee, mois, jour] = String(valeur).slice(0, 10).split('-');
    return jour && mois && annee ? `${jour}/${mois}/${annee}` : valeur;
  };

  const status = (entry) =>
    h('p', { className: 'content-preview__status' }, libelle('statut', value(entry, 'statut')));

  const BookPreview = createClass({
    render() {
      const { entry, getAsset, widgetFor } = this.props;
      const cover = assetUrl(getAsset, value(entry, 'couverture'));
      const price = value(entry, 'prixEuros', null);
      const age = value(entry, 'ageMinimum', null);
      return h('article', { className: 'content-preview' },
        status(entry),
        h('p', { className: 'content-preview__meta' }, lisible(value(entry, 'collection'))),
        h('h1', {}, value(entry, 'titre', 'Livre sans titre')),
        cover ? h('img', {
          src: cover,
          alt: value(entry, 'couvertureAlt') || `Couverture de ${value(entry, 'titre', 'ce livre')}`
        }) : null,
        h('div', { className: 'content-preview__lead' }, safeWidgetFor(widgetFor, 'description')),
        h('p', { className: 'content-preview__facts' },
          [
            libelle('ouvrage', value(entry, 'typeOuvrage')),
            age === null || age === '' ? '' : `Dès ${age} ans`,
            price === null || price === '' ? '' : `${price} €`,
            value(entry, 'disponible') === false ? 'Actuellement indisponible' : ''
          ].filter(Boolean).join(' · ')
        ),
        h('p', { className: 'content-preview__facts' },
          [
            listeLisible(value(entry, 'auteurs', [])) && `Écrit par ${listeLisible(value(entry, 'auteurs', []))}`,
            listeLisible(value(entry, 'illustrateurs', [])) && `Illustré par ${listeLisible(value(entry, 'illustrateurs', []))}`
          ].filter(Boolean).join(' · ')
        )
      );
    }
  });

  const PersonPreview = createClass({
    render() {
      const { entry, getAsset, widgetFor } = this.props;
      const portrait = assetUrl(getAsset, value(entry, 'imagePrincipale'));
      const roles = value(entry, 'roles');
      return h('article', { className: 'content-preview' },
        status(entry),
        h('p', { className: 'content-preview__meta' },
          (roles?.map?.((role) => libelle('role', role)) ?? []).join(' · ')),
        h('h1', {}, value(entry, 'nom', 'Personne sans nom')),
        portrait ? h('img', {
          src: portrait,
          alt: value(entry, 'imagePrincipaleAlt') || `Portrait de ${value(entry, 'nom', 'cette personne')}`
        }) : null,
        h('div', { className: 'content-preview__lead' }, safeWidgetFor(widgetFor, 'biographie'))
      );
    }
  });

  const CollectionPreview = createClass({
    render() {
      const { entry, getAsset, widgetFor } = this.props;
      const emblem = assetUrl(getAsset, value(entry, 'logo'));
      return h('article', { className: 'content-preview' },
        status(entry),
        h('p', { className: 'content-preview__meta' }, 'Collection'),
        emblem ? h('img', {
          className: 'content-preview__emblem',
          src: emblem,
          alt: value(entry, 'logoAlt') || `Emblème de ${value(entry, 'titre', 'la collection')}`
        }) : null,
        h('h1', {}, value(entry, 'titre', 'Collection sans titre')),
        h('div', { className: 'content-preview__lead' }, safeWidgetFor(widgetFor, 'description'))
      );
    }
  });

  const ProjectPreview = createClass({
    render() {
      const { entry } = this.props;
      const credits = [
        [value(entry, 'auteurs', []), value(entry, 'auteursHorsFiche', []), 'Écrit par'],
        [value(entry, 'illustrateurs', []), value(entry, 'illustrateursHorsFiche', []), 'Illustré par']
      ]
        .map(([fiches, libres, prefixe]) => {
          const noms = [listeLisible(fiches), (libres?.join?.(', ') ?? '')].filter(Boolean).join(', ');
          return noms ? `${prefixe} ${noms}` : '';
        })
        .filter(Boolean);
      const sortie = value(entry, 'sortiePrevue');
      return h('article', { className: 'content-preview' },
        status(entry),
        h('p', { className: 'content-preview__meta' }, 'Projet — livre à paraître'),
        h('h1', {}, value(entry, 'titre', 'Projet sans titre')),
        h('p', { className: 'content-preview__lead' }, value(entry, 'description')),
        h('p', { className: 'content-preview__facts' }, credits.join(' · ')),
        h('p', { className: 'content-preview__facts' },
          [
            lisible(value(entry, 'collection')) && `Collection ${lisible(value(entry, 'collection'))}`,
            sortie ? `Sortie prévue ${sortie}` : ''
          ].filter(Boolean).join(' · ')
        )
      );
    }
  });

  const NewsPreview = createClass({
    render() {
      const { entry, getAsset, widgetFor } = this.props;
      const image = assetUrl(getAsset, value(entry, 'image'));
      return h('article', { className: 'content-preview' },
        status(entry),
        h('p', { className: 'content-preview__meta' },
          [libelle('categorie', value(entry, 'type')), dateFr(value(entry, 'datePublication'))]
            .filter(Boolean).join(' · ')
        ),
        h('h1', {}, value(entry, 'titre', 'Actualité sans titre')),
        image ? h('img', { src: image, alt: value(entry, 'imageAlt') }) : null,
        h('div', { className: 'content-preview__lead' }, safeWidgetFor(widgetFor, 'resume')),
        h('div', { className: 'content-preview__corps' }, safeWidgetFor(widgetFor, 'contenu'))
      );
    }
  });

  // widgetsFor lève une exception quand le champ n’existe pas sur l’entrée,
  // ce qui vide tout le volet d’aperçu au lieu du seul bloc concerné.
  const safeWidgetsFor = (widgetsFor, name) => {
    try {
      return widgetsFor(name);
    } catch (error) {
      return null;
    }
  };

  // Même précaution pour widgetFor, qui rend un champ markdown déjà mis en forme :
  // c’est ce qui montre le gras et les listes dans l’aperçu, sans convertisseur ici.
  const safeWidgetFor = (widgetFor, name) => {
    try {
      return widgetFor(name);
    } catch (error) {
      return null;
    }
  };

  const PagePreview = createClass({
    render() {
      const { entry, widgetsFor } = this.props;
      const sections = safeWidgetsFor(widgetsFor, 'sections');
      return h('article', { className: 'content-preview' },
        status(entry),
        h('h1', {}, value(entry, 'titre', 'Page sans titre')),
        sections?.map?.((section, index) => h('section', { key: index },
          h('h2', {}, section.getIn(['data', 'titre'])),
          h('div', { className: 'content-preview__corps' }, section.getIn(['widgets', 'contenu']))
        ))
      );
    }
  });

  // L’aperçu du réglage Apparence : une miniature de site qui suit les valeurs en
  // cours de saisie, avant tout enregistrement. Il reprend le contrat de
  // docs/CONTRAT-APPARENCE.md : mêmes clés, mêmes tokens, même table de polices que
  // tools/content_data.py (APPEARANCE_FONTS) et tools/rendu/feuille_de_style.py.
  // Une valeur hors contrat — champ vidé, saisie en cours — retombe sur la valeur
  // par défaut : la miniature ne reçoit jamais de CSS arbitraire.
  //
  // Les aperçus des autres fiches ne lisent pas ce réglage (Decap ne donne pas accès
  // à une autre entrée depuis un aperçu) : ils montrent le thème par défaut de
  // preview.css. Seul cet aperçu-ci montre les changements en cours.
  const COULEURS_DU_THEME = [
    ['couleurFond', '--color-background', '#f7f7f4'],
    ['couleurSurface', '--color-surface', '#ffffff'],
    ['couleurTexte', '--color-text', '#171a18'],
    ['couleurTexteSecondaire', '--color-muted', '#626862'],
    ['couleurPrincipale', '--color-primary', '#c63f32'],
    ['couleurPrincipaleFoncee', '--color-primary-dark', '#963128'],
    ['couleurSecondaire', '--color-secondary', '#3e6b50'],
    ['couleurLiens', '--color-link', '#275c7a'],
    ['couleurBoutons', '--color-button', '#171a18']
  ];
  const POLICES_DU_THEME = [
    ['policeTitres', '--font-heading', 'serif-classique'],
    ['policeTexte', '--font-body', 'sans-serif-moderne']
  ];
  const POLICES = {
    'serif-classique': 'Georgia, "Times New Roman", serif',
    'serif-livre': '"Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif',
    'sans-serif-moderne': 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    'sans-serif-humaniste': 'Optima, Candara, "Gill Sans", "Trebuchet MS", ui-sans-serif, sans-serif'
  };
  const COULEUR = /^#[0-9A-Fa-f]{6}$/;

  const variablesDuTheme = (entry) => {
    const style = {};
    COULEURS_DU_THEME.forEach(([cle, token, defaut]) => {
      const choix = value(entry, cle);
      style[token] = typeof choix === 'string' && COULEUR.test(choix) ? choix : defaut;
    });
    POLICES_DU_THEME.forEach(([cle, token, defaut]) => {
      const choix = value(entry, cle);
      style[token] = Object.prototype.hasOwnProperty.call(POLICES, choix) ? POLICES[choix] : POLICES[defaut];
    });
    return style;
  };

  const AppearancePreview = createClass({
    render() {
      const { entry } = this.props;
      return h('div', { className: 'appearance-preview', style: variablesDuTheme(entry) },
        h('p', { className: 'appearance-preview__caption' }, 'Aperçu du thème'),
        h('header', { className: 'appearance-preview__header' },
          h('span', { className: 'appearance-preview__wordmark' },
            'Chant ', h('span', { className: 'appearance-preview__accent' }, 'd’orties')),
          h('nav', { className: 'appearance-preview__nav' },
            h('span', { className: 'appearance-preview__nav-active' }, 'Catalogue'),
            h('span', {}, 'Collections'),
            h('a', { href: '#', onClick: (event) => event.preventDefault() }, 'Actualités'))
        ),
        h('section', { className: 'appearance-preview__hero' },
          h('p', { className: 'appearance-preview__eyebrow' }, 'Maison d’édition jeunesse'),
          h('h1', {}, 'Des histoires qui grattent'),
          h('p', {}, 'Le texte courant s’affiche dans la police des textes, avec ',
            h('a', { href: '#', onClick: (event) => event.preventDefault() }, 'un lien'),
            ' au fil de la phrase.'),
          h('p', { className: 'appearance-preview__actions' },
            h('span', { className: 'appearance-preview__button' }, 'Explorer le catalogue'),
            h('span', { className: 'appearance-preview__button appearance-preview__button--secondary' }, 'Voir les collections'))
        ),
        h('div', { className: 'appearance-preview__grid' },
          h('article', { className: 'appearance-preview__card' },
            h('h2', {}, 'Une carte'),
            h('p', { className: 'appearance-preview__muted' }, 'Texte secondaire · Dès 9 ans'),
            h('p', { className: 'appearance-preview__available' }, 'Disponible')),
          h('article', { className: 'appearance-preview__card appearance-preview__card--secondary' },
            h('h2', {}, 'Bloc secondaire'),
            h('blockquote', {}, 'Une citation bordée de la couleur secondaire.'))
        )
      );
    }
  });

  // Les aperçus des Réglages du site : chacun montre, dans une maquette réduite du
  // site, l’endroit exact où apparaissent les textes du réglage en cours. Ils
  // utilisent le thème par défaut de preview.css ; les textes viennent de la saisie.
  const blocMarkdown = (widgetFor, name, className = 'site-preview__text') =>
    h('div', { className }, safeWidgetFor(widgetFor, name));
  const cadre = (legende, ...enfants) =>
    h('div', { className: 'site-preview' },
      h('p', { className: 'site-preview__caption' }, legende),
      ...enfants);
  const zone = (numero, titre, ...enfants) =>
    h('section', { className: 'site-preview__zone' },
      h('p', { className: 'site-preview__zone-label' },
        numero ? h('span', { className: 'site-preview__number' }, numero) : null, titre),
      ...enfants);
  const marque = () =>
    h('span', { className: 'site-preview__wordmark' },
      'Chant ', h('span', { className: 'site-preview__accent' }, 'd’orties'));
  const bouton = (texte, secondaire = false) =>
    texte ? h('span', {
      className: secondaire ? 'site-preview__button site-preview__button--secondary' : 'site-preview__button'
    }, texte) : null;
  // Le jeton {nombre} est remplacé par le compte réel à la génération.
  const avecNombre = (texte) => String(texte || '').replace(/\{nombre\}/g, '64');
  const liste = (entry, name) => {
    const valeurs = entry.getIn(['data', name]);
    return valeurs?.toJS ? valeurs.toJS() : [];
  };

  const SitePreview = createClass({
    render() {
      const { entry, widgetFor } = this.props;
      // Comme l’en-tête du site : le dernier mot du nom court passe en couleur.
      const nomCourt = String(value(entry, 'nomCourt'));
      const coupure = nomCourt.lastIndexOf(' ');
      return cadre('Identité de la maison',
        zone(null, 'En-tête, à côté du logo',
          h('header', { className: 'site-preview__header' },
            h('span', { className: 'site-preview__wordmark' },
              coupure > 0 ? nomCourt.slice(0, coupure + 1) : nomCourt,
              h('span', { className: 'site-preview__accent' }, coupure > 0 ? nomCourt.slice(coupure + 1) : '')))),
        zone(null, 'Pied de page et titre des onglets',
          h('h1', {}, value(entry, 'nom', 'Nom de la maison')),
          h('p', { className: 'site-preview__muted' }, `Onglet d’une page : « Catalogue | ${value(entry, 'nom')} »`)),
        zone(null, 'Moteurs de recherche, page d’accueil',
          blocMarkdown(widgetFor, 'description')),
        zone(null, 'Contact',
          h('p', {}, h('a', { href: '#' }, value(entry, 'courriel'))),
          h('p', {}, h('a', { href: '#' }, 'Facebook'), ' · ', value(entry, 'facebook')),
          h('p', { className: 'site-preview__muted' }, `Adresse publique du site : ${value(entry, 'domaine')}`)));
    }
  });

  const NavigationPreview = createClass({
    render() {
      const { entry } = this.props;
      const liens = liste(entry, 'liens');
      const visibles = liens.filter((lien) => lien.visible !== false);
      const masques = liens.filter((lien) => lien.visible === false);
      const recherche = value(entry, 'recherche')?.toJS?.() || {};
      return cadre('Menu principal',
        zone(null, 'En-tête, sur ordinateur',
          h('header', { className: 'site-preview__header' },
            marque(),
            h('nav', { className: 'site-preview__nav' },
              visibles.map((lien, index) => h('span', {
                key: index,
                className: index === 0 ? 'site-preview__nav-active' : null,
                title: lien.url
              }, lien.libelle)),
              h('span', { className: 'site-preview__icon', title: recherche.libelle }, '⌕')))),
        zone(null, 'Menu sur téléphone',
          h('ul', { className: 'site-preview__mobile-menu' },
            visibles.map((lien, index) => h('li', { key: index }, lien.libelle, h('small', {}, lien.url))),
            recherche.libelle ? h('li', {}, recherche.libelle, h('small', {}, recherche.url)) : null)),
        masques.length ? zone(null, 'Masqués, absents du site',
          h('p', { className: 'site-preview__muted' },
            masques.map((lien) => lien.libelle).join(' · '))) : null);
    }
  });

  const FooterPreview = createClass({
    render() {
      const { entry, widgetFor } = this.props;
      const liens = liste(entry, 'liensNavigation');
      return cadre('Pied de page, en bas de chaque page',
        h('footer', { className: 'site-preview__footer' },
          h('div', {},
            h('p', { className: 'site-preview__footer-brand' }, 'Éditions Chant d’orties'),
            blocMarkdown(widgetFor, 'presentation', 'site-preview__footer-text')),
          h('div', {},
            h('p', { className: 'site-preview__footer-title' }, value(entry, 'titreNavigation')),
            h('ul', {}, liens.map((lien, index) => h('li', { key: index, title: lien.url }, lien.libelle)))),
          h('div', {},
            h('p', { className: 'site-preview__footer-title' }, value(entry, 'titreInformations')),
            h('ul', {},
              h('li', {}, 'adresse courriel'),
              h('li', {}, value(entry, 'libelleFacebook')),
              h('li', {}, value(entry, 'libelleManuscrits')),
              h('li', {}, value(entry, 'libellePlan')),
              h('li', {}, value(entry, 'libelleMentions'))))));
    }
  });

  const HomeTextsPreview = createClass({
    render() {
      const { entry, widgetFor } = this.props;
      return cadre('Page d’accueil — les numéros suivent ceux du formulaire',
        zone('1', 'Bandeau',
          h('p', { className: 'site-preview__eyebrow' }, value(entry, 'heroRubrique')),
          h('h1', {}, value(entry, 'heroTitre'), ' ',
            h('span', { className: 'site-preview__accent' }, value(entry, 'heroAccent'))),
          blocMarkdown(widgetFor, 'heroAccroche'),
          h('p', { className: 'site-preview__actions' },
            bouton(value(entry, 'boutonCatalogue')), bouton(value(entry, 'boutonCollections'), true))),
        zone('2', 'Bloc information',
          h('h2', {}, value(entry, 'titreInformation')),
          h('p', { className: 'site-preview__muted' }, 'Le texte du bloc se règle dans Pages principales › Accueil.')),
        zone('3', 'Collections',
          h('p', { className: 'site-preview__eyebrow' }, value(entry, 'collectionsRubrique')),
          h('h2', {}, value(entry, 'collectionsTitre')),
          h('div', { className: 'site-preview__placeholder' }, 'Les six cartes des collections')),
        h('section', { className: 'site-preview__zone site-preview__zone--dark' },
          h('p', { className: 'site-preview__zone-label' },
            h('span', { className: 'site-preview__number' }, '4'), 'Suivre la maison'),
          h('p', { className: 'site-preview__eyebrow' }, value(entry, 'suivreRubrique')),
          h('h2', {}, value(entry, 'suivreTitre')),
          h('div', { className: 'site-preview__split' },
            h('div', {},
              h('p', { className: 'site-preview__eyebrow' }, value(entry, 'actualitesRubrique')),
              h('h3', {}, value(entry, 'actualitesTitre')),
              h('p', {}, `${value(entry, 'actualitesAction')} →`)),
            h('div', {},
              h('p', { className: 'site-preview__eyebrow' }, value(entry, 'manuscritsRubrique')),
              h('h3', {}, value(entry, 'manuscritsTitre')),
              h('p', {}, `${value(entry, 'manuscritsAction')} →`)))));
    }
  });

  const PAGES_ENGENDREES = [
    ['catalogue', 'Catalogue — /catalogue/'],
    ['personnes', 'Auteurs et illustrateurs — /personnes/'],
    ['collections', 'Collections — /collections/'],
    ['actualites', 'Actualités — /actualites/'],
    ['maison', 'La maison — /la-maison/']
  ];
  const PageIntrosPreview = createClass({
    render() {
      const { entry, widgetsFor } = this.props;
      return cadre('En-têtes des pages engendrées ({nombre} devient le nombre réel)',
        PAGES_ENGENDREES.map(([cle, legende]) => {
          const bloc = safeWidgetsFor(widgetsFor, cle);
          const donnee = (champ) => bloc?.getIn?.(['data', champ]) || '';
          const texte = (champ) => bloc?.getIn?.(['widgets', champ]) || null;
          return h('div', { key: cle },
            zone(null, legende,
              h('p', { className: 'site-preview__eyebrow' }, avecNombre(donnee('rubrique'))),
              h('h1', {}, donnee('titre')),
              h('div', { className: 'site-preview__text' }, texte('introduction'))),
            cle === 'actualites' ? h('section', { className: 'site-preview__zone site-preview__zone--soft' },
              h('p', { className: 'site-preview__zone-label' }, 'Actualités — bloc Facebook, en bas de page'),
              h('p', { className: 'site-preview__eyebrow' }, donnee('appelRubrique')),
              h('h2', {}, donnee('appelTitre')),
              h('div', { className: 'site-preview__text' }, texte('appelTexte')),
              h('p', { className: 'site-preview__actions' }, bouton(donnee('boutonFacebook')))) : null);
        }));
    }
  });

  const PaymentPreview = createClass({
    render() {
      const { entry } = this.props;
      return cadre('Parcours d’achat',
        zone(null, 'Page d’un livre disponible',
          h('p', { className: 'site-preview__price' }, '7 € ',
            h('span', { className: 'site-preview__available' }, value(entry, 'libelleDisponible'))),
          h('p', { className: 'site-preview__actions' },
            bouton(value(entry, 'libellePanier')), bouton(value(entry, 'libelleVoirPanier'), true)),
          h('p', {}, h('a', { href: '#' }, value(entry, 'libelleExtrait')))),
        zone(null, 'Page d’un livre indisponible',
          h('p', { className: 'site-preview__muted' }, value(entry, 'libelleIndisponible')),
          h('p', { className: 'site-preview__actions' }, bouton(value(entry, 'libelleContact'), true))),
        zone(null, 'Accueil, bloc soutien et commandes',
          h('p', { className: 'site-preview__actions' },
            bouton(`♡ ${value(entry, 'libelleDon')}`), bouton(value(entry, 'libelleOffres'), true))));
    }
  });

  // La description de référencement doit tenir en 160 caractères. La limite est déjà
  // vérifiée par le motif déclaré dans config.yml, mais elle ne se manifestait qu’au
  // moment d’enregistrer : ce compteur la rend visible pendant la frappe.
  //
  // Le champ garde le comportement du markdown ordinaire : on enveloppe le contrôle
  // natif sans toucher à sa validation. Volontairement, isValid n’est PAS redirigé vers
  // le contrôle interne : « required » et le motif sont vérifiés par Decap au-dessus du
  // contrôle, pas par lui, et une redirection par ref serait fragile pour rien.
  const LIMITE_SEO = 160;
  const widgetMarkdown = CMS.getWidget('markdown');
  const DescriptionSeo = createClass({
    render() {
      const texte = this.props.value || '';
      const reste = LIMITE_SEO - texte.length;
      return h('div', { className: 'compteur' },
        h(widgetMarkdown.control, this.props),
        h('p', {
          className: reste < 0 ? 'compteur__ligne compteur__ligne--trop' : 'compteur__ligne'
        }, reste < 0
          ? `${texte.length} caractères — ${-reste} de trop, la publication sera refusée`
          : `${texte.length} / ${LIMITE_SEO} caractères`)
      );
    }
  });
  CMS.registerWidget('description-seo', DescriptionSeo, widgetMarkdown.preview, widgetMarkdown.schema);

  // La feuille est injectée dans le cadre d’aperçu, dont l’adresse de base n’est pas
  // celle de cette page : l’URL est donc résolue ici, à partir de l’administration
  // elle-même. Servie à la racine du sous-domaine chez OVH, sous /admin/ en local.
  CMS.registerPreviewStyle(new URL('preview.css', document.baseURI).href);
  CMS.registerPreviewTemplate('livres', BookPreview);
  CMS.registerPreviewTemplate('personnes', PersonPreview);
  CMS.registerPreviewTemplate('collections', CollectionPreview);
  CMS.registerPreviewTemplate('actualites', NewsPreview);
  CMS.registerPreviewTemplate('projets', ProjectPreview);
  CMS.registerPreviewTemplate('pages', PagePreview);
  CMS.registerPreviewTemplate('pages_fixes', PagePreview);
  // Nom du fichier de réglages : seule l’entrée Réglages › Apparence le porte.
  CMS.registerPreviewTemplate('apparence', AppearancePreview);
  // Les autres fichiers de réglages, chacun avec la maquette de sa zone du site. Les
  // noms sont ceux des entrées de config.yml : « introductions » et non « pages »,
  // qui désignerait aussi la rubrique Pages de la maison.
  CMS.registerPreviewTemplate('site', SitePreview);
  CMS.registerPreviewTemplate('navigation', NavigationPreview);
  CMS.registerPreviewTemplate('footer', FooterPreview);
  CMS.registerPreviewTemplate('accueil', HomeTextsPreview);
  CMS.registerPreviewTemplate('introductions', PageIntrosPreview);
  CMS.registerPreviewTemplate('paiement', PaymentPreview);
})();
