const menuButton = document.querySelector('[data-menu-button]');
const mobileNav = document.querySelector('[data-mobile-nav]');

function closeMenu({ restoreFocus = false } = {}) {
  if (!menuButton || !mobileNav) return;
  mobileNav.hidden = true;
  menuButton.setAttribute('aria-expanded', 'false');
  menuButton.setAttribute('aria-label', 'Ouvrir le menu');
  menuButton.title = 'Ouvrir le menu';
  document.body.classList.remove('menu-open');
  if (restoreFocus) menuButton.focus();
}

if (menuButton && mobileNav) {
  menuButton.addEventListener('click', () => {
    const willOpen = mobileNav.hidden;
    mobileNav.hidden = !willOpen;
    menuButton.setAttribute('aria-expanded', String(willOpen));
    menuButton.setAttribute('aria-label', willOpen ? 'Fermer le menu' : 'Ouvrir le menu');
    menuButton.title = willOpen ? 'Fermer le menu' : 'Ouvrir le menu';
    document.body.classList.toggle('menu-open', willOpen);
    if (willOpen) mobileNav.querySelector('a')?.focus();
  });

  mobileNav.addEventListener('click', (event) => {
    if (event.target.closest('a')) closeMenu();
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && !mobileNav.hidden) {
      closeMenu({ restoreFocus: true });
    }
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 1020) closeMenu();
  });
}

const backToTop = document.querySelector('[data-back-to-top]');
if (backToTop) {
  const updateBackToTop = () => {
    backToTop.hidden = window.scrollY < 500;
  };

  updateBackToTop();
  window.addEventListener('scroll', updateBackToTop, { passive: true });
  backToTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

const galleryDialog = document.querySelector('[data-gallery-dialog]');
if (galleryDialog) {
  const dialogImage = galleryDialog.querySelector('img');
  const closeButton = galleryDialog.querySelector('[data-dialog-close]');

  document.querySelectorAll('[data-gallery-src]').forEach((button) => {
    button.addEventListener('click', () => {
      dialogImage.src = button.dataset.gallerySrc;
      dialogImage.alt = button.dataset.galleryAlt || '';
      galleryDialog.showModal();
    });
  });

  closeButton?.addEventListener('click', () => galleryDialog.close());
  galleryDialog.addEventListener('click', (event) => {
    if (event.target === galleryDialog) galleryDialog.close();
  });
}

if (window.location.hash === '#recherche') {
  window.addEventListener('load', () => {
    document.querySelector('#recherche input')?.focus();
  });
}
