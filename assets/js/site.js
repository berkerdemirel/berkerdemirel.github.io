// Shared behaviour for every page: theme toggle, card video previews,
// BibTeX copy buttons and dialogs, and the post table of contents.
(() => {
  const root = document.documentElement;
  const media = window.matchMedia('(prefers-color-scheme: dark)');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const PAPER = { light: '#f4ebd9', dark: '#13171a' };

  // ---- Theme -------------------------------------------------------------
  const current = () =>
    root.dataset.theme === 'light' || root.dataset.theme === 'dark'
      ? root.dataset.theme
      : media.matches ? 'dark' : 'light';

  const sync = () => {
    const theme = current();
    for (const meta of document.querySelectorAll('meta[name="theme-color"]')) {
      if (root.dataset.theme) meta.setAttribute('content', PAPER[theme]);
      else meta.setAttribute('content', (meta.getAttribute('media') || '').includes('dark') ? PAPER.dark : PAPER.light);
    }
    const toggle = document.getElementById('theme-toggle');
    if (toggle) toggle.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
    document.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
  };

  document.getElementById('theme-toggle')?.addEventListener('click', () => {
    const next = current() === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch {}
    sync();
  });
  media.addEventListener('change', () => { if (!root.dataset.theme) sync(); });
  sync();

  // ---- Card teaser previews: play muted on hover/focus ------------------
  for (const card of document.querySelectorAll('[data-preview]')) {
    const video = card.querySelector('video');
    if (!video) continue;
    const start = () => {
      if (reduceMotion.matches) return;
      video.play().then(() => video.classList.add('is-playing')).catch(() => {});
    };
    const stop = () => {
      video.pause();
      video.classList.remove('is-playing');
    };
    card.addEventListener('mouseenter', start);
    card.addEventListener('mouseleave', stop);
    card.addEventListener('focusin', start);
    card.addEventListener('focusout', stop);
  }

  // ---- Post teaser: autoplay only when visible and motion is welcome ----
  for (const video of document.querySelectorAll('video[data-autoplay]')) {
    if (reduceMotion.matches || !('IntersectionObserver' in window)) continue;
    const io = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) video.play().catch(() => {});
        else video.pause();
      }
    }, { threshold: 0.5 });
    io.observe(video);
  }

  // ---- Copy buttons ------------------------------------------------------
  for (const btn of document.querySelectorAll('[data-copy]')) {
    btn.addEventListener('click', async () => {
      const target = document.getElementById(btn.dataset.copy);
      if (!target) return;
      const label = btn.textContent;
      try {
        await navigator.clipboard.writeText(target.textContent.trim());
        btn.textContent = 'Copied';
      } catch {
        btn.textContent = 'Select & copy';
      }
      setTimeout(() => { btn.textContent = label; }, 1600);
    });
  }

  // ---- Table of contents for posts --------------------------------------
  const toc = document.querySelector('.post-toc ol');
  const headings = [...document.querySelectorAll('.post-body h2[id]')];
  if (toc && headings.length) {
    const links = new Map();
    for (const h of headings) {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = `#${h.id}`;
      a.textContent = h.dataset.toc || h.textContent;
      li.append(a);
      toc.append(li);
      links.set(h, a);
    }
    if ('IntersectionObserver' in window) {
      const visible = new Set();
      const io = new IntersectionObserver((entries) => {
        for (const e of entries) e.isIntersecting ? visible.add(e.target) : visible.delete(e.target);
        const first = headings.find((h) => visible.has(h));
        if (!first) return;
        for (const a of links.values()) a.classList.remove('is-active');
        links.get(first).classList.add('is-active');
      }, { rootMargin: '0px 0px -70% 0px' });
      headings.forEach((h) => io.observe(h));
    }
  }

  // ---- Collapsed technical details: open when a link points into them ---
  const reveal = () => {
    let id = '';
    try { id = decodeURIComponent(location.hash.slice(1)); } catch {}
    const target = id ? document.getElementById(id) : null;
    const details = target?.closest('details.deep-dive');
    if (details && !details.open) {
      details.open = true;
      target.scrollIntoView();
    }
  };
  window.addEventListener('hashchange', reveal);
  reveal();

  // ---- BibTeX links: show the entry in a dialog instead of downloading --
  const bibLinks = document.querySelectorAll('a[href$=".bib"]');
  if (bibLinks.length && typeof HTMLDialogElement === 'function') {
    const dialog = document.createElement('dialog');
    dialog.className = 'bib-dialog';
    dialog.setAttribute('aria-labelledby', 'bib-dialog-title');
    dialog.innerHTML = '<p class="kicker" id="bib-dialog-title">BibTeX</p><pre></pre>'
      + '<div class="bib-actions"><button class="btn" type="button" data-act="copy">Copy</button>'
      + '<button class="btn" type="button" data-act="close">Close</button></div>';
    document.body.append(dialog);
    const pre = dialog.querySelector('pre');
    const copyBtn = dialog.querySelector('[data-act="copy"]');
    const cache = new Map();

    dialog.querySelector('[data-act="close"]').addEventListener('click', () => dialog.close());
    // A click on the backdrop lands on the dialog itself, outside its box
    dialog.addEventListener('click', (e) => {
      if (e.target !== dialog) return;
      const r = dialog.getBoundingClientRect();
      if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close();
    });
    copyBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(pre.textContent);
        copyBtn.textContent = 'Copied';
      } catch {
        const range = document.createRange();
        range.selectNodeContents(pre);
        getSelection().removeAllRanges();
        getSelection().addRange(range);
        copyBtn.textContent = 'Select & copy';
      }
      setTimeout(() => { copyBtn.textContent = 'Copy'; }, 1600);
    });

    for (const link of bibLinks) {
      link.addEventListener('click', async (e) => {
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault();
        try {
          if (!cache.has(link.href)) {
            const res = await fetch(link.href);
            if (!res.ok) throw new Error(String(res.status));
            cache.set(link.href, (await res.text()).trim());
          }
        } catch {
          location.href = link.href;
          return;
        }
        pre.textContent = cache.get(link.href);
        copyBtn.textContent = 'Copy';
        dialog.showModal();
        copyBtn.focus();
      });
    }
  }
})();
