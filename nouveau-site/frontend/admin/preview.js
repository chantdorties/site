(() => {
  const value = (entry, name, fallback = '') => entry.getIn(['data', name]) ?? fallback;
  const assetUrl = (getAsset, path) => {
    if (!path) return '';
    const asset = getAsset(path);
    return asset ? asset.toString() : '';
  };
  const status = (entry) => h('p', { className: 'content-preview__status' }, value(entry, 'statut'));

  const BookPreview = createClass({
    render() {
      const { entry, getAsset } = this.props;
      const cover = assetUrl(getAsset, value(entry, 'couverture'));
      const price = value(entry, 'prixEuros', null);
      return h('article', { className: 'content-preview' },
        status(entry),
        h('p', { className: 'content-preview__meta' }, value(entry, 'collection')),
        h('h1', {}, value(entry, 'titre', 'Livre sans titre')),
        cover ? h('img', { src: cover, alt: '' }) : null,
        h('p', { className: 'content-preview__lead' }, value(entry, 'description')),
        h('p', { className: 'content-preview__facts' },
          [value(entry, 'typeOuvrage'), price === null ? '' : `${price} €`].filter(Boolean).join(' · ')
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
        h('p', { className: 'content-preview__meta' }, roles?.join?.(' · ') || ''),
        h('h1', {}, value(entry, 'nom', 'Personne sans nom')),
        portrait ? h('img', { src: portrait, alt: '' }) : null,
        h('p', { className: 'content-preview__lead' }, value(entry, 'biographie'))
      );
    }
  });

  const CollectionPreview = createClass({
    render() {
      const { entry } = this.props;
      return h('article', { className: 'content-preview' },
        status(entry),
        h('p', { className: 'content-preview__meta' }, 'Collection'),
        h('h1', {}, value(entry, 'titre', 'Collection sans titre')),
        h('p', { className: 'content-preview__lead' }, value(entry, 'description'))
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
          `${value(entry, 'type')} · ${value(entry, 'datePublication')}`
        ),
        h('h1', {}, value(entry, 'titre', 'Actualité sans titre')),
        image ? h('img', { src: image, alt: value(entry, 'imageAlt') }) : null,
        h('p', { className: 'content-preview__lead' }, value(entry, 'resume')),
        h('p', {}, value(entry, 'contenu'))
      );
    }
  });

  const PagePreview = createClass({
    render() {
      const { entry, widgetsFor } = this.props;
      const sections = widgetsFor('sections');
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

  CMS.registerPreviewStyle('/admin/preview.css');
  CMS.registerPreviewTemplate('livres', BookPreview);
  CMS.registerPreviewTemplate('personnes', PersonPreview);
  CMS.registerPreviewTemplate('collections', CollectionPreview);
  CMS.registerPreviewTemplate('actualites', NewsPreview);
  CMS.registerPreviewTemplate('pages', PagePreview);
})();
