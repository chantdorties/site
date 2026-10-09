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

const cookieBanner = document.querySelector('[data-cookie-banner]');
const cookieChoiceKey = 'chantdorties-cookie-choice-v1';

if (cookieBanner) {
  let savedChoice = null;
  try {
    savedChoice = window.localStorage.getItem(cookieChoiceKey);
  } catch {
    // La bannière reste utilisable même si la mémoire locale est bloquée.
  }

  if (!savedChoice) cookieBanner.hidden = false;

  cookieBanner.querySelectorAll('[data-cookie-choice]').forEach((button) => {
    button.addEventListener('click', () => {
      try {
        window.localStorage.setItem(cookieChoiceKey, button.dataset.cookieChoice);
      } catch {
        // Le choix est tout de même appliqué pour cette visite.
      }
      cookieBanner.hidden = true;
    });
  });
}

if (window.location.hash === '#recherche') {
  window.addEventListener('load', () => {
    document.querySelector('#recherche input')?.focus();
  });
}

// La vidéo d'un texte : le lecteur de YouTube ou de Vimeo n'est demandé qu'au clic du
// visiteur, et seul l'identifiant vient de la page (tools/rendu/texte.py).
const lecteurs = {
  youtube: (id) => `https://www.youtube-nocookie.com/embed/${id}?autoplay=1`,
  vimeo: (id, hash) => `https://player.vimeo.com/video/${id}?${hash ? `h=${hash}&` : ''}dnt=1&autoplay=1`,
};
document.querySelectorAll('.video-facade[data-video-site]').forEach((bouton) => {
  bouton.addEventListener('click', () => {
    const { videoSite, videoId, videoHash, videoTitle } = bouton.dataset;
    const adresse = lecteurs[videoSite];
    if (!adresse || !/^[\w-]+$/.test(videoId) || (videoHash && !/^[0-9a-f]+$/.test(videoHash))) return;
    const lecteur = document.createElement('iframe');
    lecteur.src = adresse(videoId, videoHash);
    lecteur.title = videoTitle || 'Vidéo';
    lecteur.allow = 'autoplay; fullscreen; picture-in-picture';
    lecteur.allowFullscreen = true;
    lecteur.referrerPolicy = 'strict-origin-when-cross-origin';
    bouton.replaceWith(lecteur);
    lecteur.focus();
  });
});
