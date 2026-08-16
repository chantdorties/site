const grid = document.querySelector('[data-person-grid]');
const status = document.querySelector('[data-results-status]');
const searchInput = document.querySelector('#person-search');
const roleSelect = document.querySelector('#person-role');
let people = [];

const roleLabels = {
  auteur: 'Auteur',
  illustrateur: 'Illustrateur',
  prefacier: 'Préfacier',
};

const normalize = (value = '') => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLocaleLowerCase('fr');

function createPersonCard(person) {
  const article = document.createElement('article');
  article.className = 'person-card';

  const visual = document.createElement('a');
  visual.className = 'person-card__visual';
  visual.href = `/personnes/${person.slug}/`;
  visual.setAttribute('aria-label', `Voir la fiche de ${person.nom}`);

  if (person.imagePrincipale) {
    const image = document.createElement('img');
    image.src = person.imagePrincipale;
    image.alt = person.imagePrincipaleAlt || `Portrait de ${person.nom}`;
    image.loading = 'lazy';
    image.width = 480;
    image.height = 480;
    visual.append(image);
  } else {
    const monogram = document.createElement('span');
    monogram.className = 'monogram';
    monogram.setAttribute('aria-hidden', 'true');
    monogram.textContent = person.monogram;
    visual.append(monogram);
  }

  const roles = document.createElement('p');
  roles.className = 'person-card__roles';
  roles.textContent = person.roles.map((role) => roleLabels[role] || role).join(' · ');

  const title = document.createElement('h3');
  const link = document.createElement('a');
  link.href = visual.href;
  link.textContent = person.nom;
  title.append(link);

  const meta = document.createElement('p');
  meta.className = 'book-card__meta';
  meta.textContent = `${person.nombreLivres} ${person.nombreLivres > 1 ? 'livres' : 'livre'}`;

  article.append(visual, roles, title, meta);
  return article;
}

function updatePeople() {
  const query = normalize(searchInput.value.trim());
  const role = roleSelect.value;
  const filtered = people.filter((person) => (
    (!query || normalize(person.nom).includes(query))
    && (!role || person.roles.includes(role))
  ));

  grid.replaceChildren();
  if (!filtered.length) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = 'Aucune personne ne correspond à ces critères.';
    grid.append(empty);
  } else {
    grid.append(...filtered.map(createPersonCard));
  }
  grid.setAttribute('aria-busy', 'false');
  status.textContent = `${filtered.length} ${filtered.length > 1 ? 'personnes' : 'personne'}`;
}

async function loadPeople() {
  try {
    const response = await fetch('/data/personnes.json');
    if (!response.ok) throw new Error(`Réponse HTTP ${response.status}`);
    people = await response.json();
    searchInput.addEventListener('input', updatePeople);
    roleSelect.addEventListener('input', updatePeople);
    updatePeople();
  } catch (error) {
    grid.replaceChildren();
    const message = document.createElement('p');
    message.className = 'error-state';
    message.textContent = 'L’annuaire ne peut pas être chargé pour le moment. Veuillez réessayer.';
    grid.append(message);
    grid.setAttribute('aria-busy', 'false');
    status.textContent = 'Chargement impossible';
    console.error(error);
  }
}

loadPeople();
