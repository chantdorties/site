const grid = document.querySelector('[data-book-grid]');
const status = document.querySelector('[data-results-status]');
const searchInput = document.querySelector('#book-search');
const collectionSelect = document.querySelector('#book-collection');
const typeSelect = document.querySelector('#book-type');
const availabilitySelect = document.querySelector('#book-availability');
const sortSelect = document.querySelector('#book-sort');

const state = {
  books: [],
  collections: new Map(),
};

const normalize = (value = '') => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLocaleLowerCase('fr');

const formatLabel = (value = '') => value
  .replaceAll('-', ' ')
  .replace(/^./, (letter) => letter.toLocaleUpperCase('fr'));

const formatPrice = (cents) => {
  if (!Number.isInteger(cents)) return '';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: cents % 100 === 0 ? 0 : 2,
  }).format(cents / 100);
};

function createBookCard(book) {
  const article = document.createElement('article');
  article.className = 'book-card';

  const coverLink = document.createElement('a');
  coverLink.className = 'book-card__cover-link';
  coverLink.href = `/livres/${book.slug}/`;

  const image = document.createElement('img');
  image.className = 'book-card__cover';
  image.src = book.couverture;
  image.alt = `Couverture de ${book.titre}`;
  image.loading = 'lazy';
  image.width = 480;
  image.height = 720;
  coverLink.append(image);

  const collection = document.createElement('p');
  collection.className = 'book-card__collection';
  collection.textContent = state.collections.get(book.collection)?.titre || book.collection;

  const title = document.createElement('h3');
  const titleLink = document.createElement('a');
  titleLink.href = coverLink.href;
  titleLink.textContent = book.titre;
  title.append(titleLink);

  const meta = document.createElement('p');
  meta.className = 'book-card__meta';
  const details = [];
  if (book.typeOuvrage) details.push(formatLabel(book.typeOuvrage));
  if (book.ageMinimum) details.push(`Dès ${book.ageMinimum} ans`);
  if (book.prixCentimes !== null) details.push(formatPrice(book.prixCentimes));
  meta.textContent = details.join(' · ');

  article.append(coverLink, collection, title, meta);
  return article;
}

function updateFilters() {
  const query = normalize(searchInput.value.trim());
  const collection = collectionSelect.value;
  const type = typeSelect.value;
  const availability = availabilitySelect.value;

  const filtered = state.books.filter((book) => {
    const haystack = normalize([
      book.titre,
      book.auteurNoms.join(' '),
      book.illustrateurNoms.join(' '),
    ].join(' '));

    return (!query || haystack.includes(query))
      && (!collection || book.collection === collection)
      && (!type || book.typeOuvrage === type)
      && (!availability || String(book.disponible) === availability);
  });

  const collator = new Intl.Collator('fr', { sensitivity: 'base' });
  filtered.sort((left, right) => {
    if (sortSelect.value === 'price-asc') {
      return (left.prixCentimes ?? Number.MAX_SAFE_INTEGER)
        - (right.prixCentimes ?? Number.MAX_SAFE_INTEGER);
    }
    if (sortSelect.value === 'price-desc') {
      return (right.prixCentimes ?? -1) - (left.prixCentimes ?? -1);
    }
    return collator.compare(left.titre, right.titre);
  });

  grid.replaceChildren();
  if (!filtered.length) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = 'Aucun livre ne correspond à ces critères.';
    grid.append(empty);
  } else {
    grid.append(...filtered.map(createBookCard));
  }

  grid.setAttribute('aria-busy', 'false');
  status.textContent = `${filtered.length} ${filtered.length > 1 ? 'livres' : 'livre'}`;
}

function fillSelect(select, values, getLabel = formatLabel) {
  values.forEach((value) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = getLabel(value);
    select.append(option);
  });
}

async function loadCatalogue() {
  try {
    const [booksResponse, collectionsResponse] = await Promise.all([
      fetch('/data/livres.json'),
      fetch('/data/collections.json'),
    ]);
    if (!booksResponse.ok || !collectionsResponse.ok) {
      throw new Error('Réponse HTTP incorrecte');
    }

    const [books, collections] = await Promise.all([
      booksResponse.json(),
      collectionsResponse.json(),
    ]);

    state.books = books;
    state.collections = new Map(collections.map((item) => [item.slug, item]));
    fillSelect(collectionSelect, collections.map((item) => item.slug), (slug) => state.collections.get(slug).titre);
    fillSelect(typeSelect, [...new Set(books.map((book) => book.typeOuvrage).filter(Boolean))].sort());

    [searchInput, collectionSelect, typeSelect, availabilitySelect, sortSelect]
      .forEach((control) => control.addEventListener('input', updateFilters));

    updateFilters();
  } catch (error) {
    grid.replaceChildren();
    const message = document.createElement('p');
    message.className = 'error-state';
    message.textContent = 'Le catalogue ne peut pas être chargé pour le moment. Veuillez réessayer.';
    grid.append(message);
    grid.setAttribute('aria-busy', 'false');
    status.textContent = 'Chargement impossible';
    console.error(error);
  }
}

loadCatalogue();
