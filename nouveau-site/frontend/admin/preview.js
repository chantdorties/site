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
      const { entry, getAsset } = this.props;
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
        h('p', { className: 'content-preview__lead' }, value(entry, 'description')),
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
      const { entry, getAsset } = this.props;
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
        h('p', { className: 'content-preview__lead' }, value(entry, 'biographie'))
      );
    }
  });

  const CollectionPreview = createClass({
    render() {
      const { entry, getAsset } = this.props;
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
        h('p', { className: 'content-preview__lead' }, value(entry, 'description'))
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
      const { entry, getAsset } = this.props;
      const image = assetUrl(getAsset, value(entry, 'image'));
      return h('article', { className: 'content-preview' },
        status(entry),
        h('p', { className: 'content-preview__meta' },
          [libelle('categorie', value(entry, 'type')), dateFr(value(entry, 'datePublication'))]
            .filter(Boolean).join(' · ')
        ),
        h('h1', {}, value(entry, 'titre', 'Actualité sans titre')),
        image ? h('img', { src: image, alt: value(entry, 'imageAlt') }) : null,
        h('p', { className: 'content-preview__lead' }, value(entry, 'resume')),
        h('p', {}, value(entry, 'contenu'))
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

  const PagePreview = createClass({
    render() {
      const { entry, widgetsFor } = this.props;
      const sections = safeWidgetsFor(widgetsFor, 'sections');
      return h('article', { className: 'content-preview' },
        status(entry),
        h('h1', {}, value(entry, 'titre', 'Page sans titre')),
        sections?.map?.((section, index) => h('section', { key: index },
          h('h2', {}, section.getIn(['data', 'titre'])),
          h('p', {}, section.getIn(['data', 'contenu']))
        ))
      );
    }
  });

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
})();
