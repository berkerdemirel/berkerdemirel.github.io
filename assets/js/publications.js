// Publications page: search box plus year and venue filters.
// Entries carry data-year and data-venue; chips are built from whatever entries exist,
// so a new paper only needs those two attributes. Filters are mirrored in the URL
// (?q=…&year=…&venue=…) so a filtered view can be shared.
(() => {
  const root = document.querySelector('.pub-filters');
  if (!root) return;
  const input = root.querySelector('input[type="search"]');
  const count = root.querySelector('.pub-count');
  const empty = document.querySelector('.pub-empty');
  const sections = [...document.querySelectorAll('.pub-year')];
  const items = [...document.querySelectorAll('.pub-year li[data-venue]')];

  const fold = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  for (const li of items) {
    const art = li.querySelector('.pub');
    const parts = [
      art.querySelector('h3')?.textContent,
      art.querySelector('.authors')?.textContent,
      art.querySelector('.venue')?.textContent,
      li.dataset.venue,
      li.dataset.year,
    ];
    li.dataset.haystack = fold(parts.filter(Boolean).join(' '));
  }

  const VENUE_ORDER = ['NeurIPS', 'ICIP', 'SIU', 'Preprint', 'Project'];
  const years = [...new Set(items.map((li) => li.dataset.year).filter(Boolean))].sort((a, b) => b - a);
  const venues = [...new Set(items.map((li) => li.dataset.venue))]
    .sort((a, b) => (VENUE_ORDER.indexOf(a) + 1 || 99) - (VENUE_ORDER.indexOf(b) + 1 || 99));

  const params = new URLSearchParams(location.search);
  const state = {
    q: params.get('q') || '',
    year: years.includes(params.get('year')) ? params.get('year') : 'all',
    venue: venues.includes(params.get('venue')) ? params.get('venue') : 'all',
  };
  input.value = state.q;

  function chips(group, values, allLabel, key) {
    const row = root.querySelector(`[data-filter="${group}"]`);
    for (const v of ['all', ...values]) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'chip';
      b.dataset.value = v;
      b.textContent = v === 'all' ? allLabel : v === 'Project' ? 'Projects' : v;
      b.setAttribute('aria-pressed', String(state[key] === v));
      b.addEventListener('click', () => {
        state[key] = v;
        for (const x of row.children) x.setAttribute('aria-pressed', String(x === b));
        apply();
      });
      row.append(b);
    }
  }
  chips('year', years, 'All years', 'year');
  chips('venue', venues, 'All venues', 'venue');

  function apply() {
    const tokens = fold(state.q).split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const li of items) {
      const ok = (state.year === 'all' || li.dataset.year === state.year)
        && (state.venue === 'all' || li.dataset.venue === state.venue)
        && tokens.every((t) => li.dataset.haystack.includes(t));
      li.hidden = !ok;
      if (ok) shown++;
    }
    for (const sec of sections) sec.hidden = !sec.querySelector('li[data-venue]:not([hidden])');
    count.textContent = shown === items.length ? `${items.length} entries` : `Showing ${shown} of ${items.length}`;
    if (empty) empty.hidden = shown > 0;

    const p = new URLSearchParams();
    if (state.q) p.set('q', state.q);
    if (state.year !== 'all') p.set('year', state.year);
    if (state.venue !== 'all') p.set('venue', state.venue);
    const qs = p.toString();
    history.replaceState(null, '', qs ? `?${qs}` : location.pathname);
  }

  input.addEventListener('input', () => { state.q = input.value; apply(); });
  apply();
})();
