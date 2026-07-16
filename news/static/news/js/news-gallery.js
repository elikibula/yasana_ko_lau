(() => {
  const gallery = document.querySelector('[data-news-gallery]');
  const lightbox = document.querySelector('[data-news-lightbox]');

  if (gallery && lightbox) {
    const links = [...gallery.querySelectorAll('[data-gallery-index]')];
    const image = lightbox.querySelector('[data-gallery-image]');
    const caption = lightbox.querySelector('[data-gallery-caption]');
    const counter = lightbox.querySelector('[data-gallery-counter]');
    const closeButton = lightbox.querySelector('[data-gallery-close]');
    const previousButton = lightbox.querySelector('[data-gallery-previous]');
    const nextButton = lightbox.querySelector('[data-gallery-next]');
    let currentIndex = 0;
    let returnFocus = null;
    let touchStartX = null;

    const render = (index) => {
      currentIndex = (index + links.length) % links.length;
      const link = links[currentIndex];
      const thumbnail = link.querySelector('img');
      image.src = link.href;
      image.alt = thumbnail.alt || `Photo ${currentIndex + 1} from the news gallery`;
      caption.textContent = link.dataset.caption || '';
      caption.hidden = !link.dataset.caption;
      counter.textContent = `${currentIndex + 1} of ${links.length}`;
      [previousButton, nextButton].forEach((button) => { button.hidden = links.length < 2; });
      if (links.length > 1) {
        [links[(currentIndex - 1 + links.length) % links.length], links[(currentIndex + 1) % links.length]].forEach((item) => {
          const preload = new Image();
          preload.src = item.href;
        });
      }
    };

    const move = (amount) => render(currentIndex + amount);
    const close = () => lightbox.close();

    links.forEach((link, index) => link.addEventListener('click', (event) => {
      event.preventDefault();
      returnFocus = link;
      render(index);
      lightbox.showModal();
      document.body.style.overflow = 'hidden';
      closeButton.focus();
    }));
    previousButton.addEventListener('click', () => move(-1));
    nextButton.addEventListener('click', () => move(1));
    closeButton.addEventListener('click', close);
    lightbox.addEventListener('click', (event) => {
      if (event.target === lightbox || event.target.matches('[data-gallery-backdrop]')) close();
    });
    image.addEventListener('error', () => {
      image.alt = 'This gallery photo could not be loaded.';
      caption.textContent = 'This photo could not be loaded.';
      caption.hidden = false;
    });
    lightbox.addEventListener('close', () => {
      document.body.style.overflow = '';
      image.removeAttribute('src');
      returnFocus?.focus();
    });
    lightbox.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft') { event.preventDefault(); move(-1); }
      if (event.key === 'ArrowRight') { event.preventDefault(); move(1); }
      if (event.key === 'Escape') { event.preventDefault(); close(); }
      if (event.key === 'Tab') {
        const controls = [closeButton, previousButton, nextButton].filter((button) => !button.hidden);
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    });
    lightbox.addEventListener('touchstart', (event) => { touchStartX = event.changedTouches[0].clientX; }, { passive: true });
    lightbox.addEventListener('touchend', (event) => {
      if (touchStartX === null) return;
      const distance = event.changedTouches[0].clientX - touchStartX;
      if (Math.abs(distance) > 50 && links.length > 1) move(distance < 0 ? 1 : -1);
      touchStartX = null;
    }, { passive: true });
  }

  const share = document.querySelector('[data-news-share]');
  if (!share) return;
  const url = share.dataset.shareUrl;
  const title = share.dataset.shareTitle;
  const feedback = share.querySelector('[data-share-feedback]');
  const nativeButton = share.querySelector('[data-native-share]');

  const copy = async (message) => {
    try {
      if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(url);
      else {
        const input = document.createElement('textarea');
        input.value = url;
        input.setAttribute('readonly', '');
        input.style.position = 'fixed';
        input.style.opacity = '0';
        document.body.appendChild(input);
        input.select();
        if (!document.execCommand('copy')) throw new Error('Copy failed');
        input.remove();
      }
      feedback.textContent = message;
      return true;
    } catch (error) {
      feedback.textContent = 'Copy failed. Please copy the address from your browser.';
      return false;
    }
  };

  if (navigator.share) {
    nativeButton.hidden = false;
    nativeButton.addEventListener('click', async () => {
      try { await navigator.share({ title, text: title, url }); } catch (error) { if (error.name !== 'AbortError') feedback.textContent = 'Sharing is unavailable right now.'; }
    });
  }
  share.querySelector('[data-copy-link]').addEventListener('click', async (event) => {
    const label = event.currentTarget.querySelector('span');
    if (await copy('Link copied.')) {
      label.textContent = 'Link copied';
      window.setTimeout(() => { label.textContent = 'Copy link'; feedback.textContent = ''; }, 2500);
    }
  });
  share.querySelector('[data-instagram-share]').addEventListener('click', () => copy('Link copied. Open Instagram and paste it into your story, message, or bio.'));
})();
