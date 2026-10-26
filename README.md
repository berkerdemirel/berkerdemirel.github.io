# berkerdemirel.github.io

Static personal site: plain HTML, one stylesheet, a little vanilla JS. No build step.

```
index.html              About
research/index.html     Research themes with interactive sketches
publications/index.html Full publication list
blog/index.html         Post index
blog/<slug>/            One post per paper: index.html, teaser.mp4, poster.jpg, fig-*.png
cv/index.html           CV summary (cv/00_Berker_Demirel_CV.pdf is the full CV)
assets/css/site.css     Design tokens (light/dark), layout, components
assets/js/site.js       Theme toggle, card video previews, BibTeX copy and dialogs, post TOC
assets/js/research-viz.js  The three interactive sketches
legacy.html             The previous single-page site, unchanged
_templates/post.html    Starting point for a new post
_teasers/               manim sources for the teaser videos (see _teasers/README.md)
_sources/               Local paper PDFs and original video exports (gitignored)
```

Folders starting with `_` are not published by GitHub Pages.

## Preview locally

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

Pages link to folders (`research/`), so open them through a server rather than as files.

## Common edits

- **New paper:** add an entry to `publications/index.html`; if it belongs to a research area,
  add a card to that area's "Our work" list in `research/index.html` (a list with a single
  card uses `class="card-grid is-single"`); optionally add it to "Selected publications" on
  `index.html`. Each area's color comes from the `--t-rep`, `--t-gen` and `--t-gnr` tokens in
  `site.css`.
- **New post:** copy `_templates/post.html` to `blog/<slug>/index.html`, fill in the TODOs,
  and add a card to `blog/index.html`. Posts share one column width (`--post-width` in
  `site.css`) for text, figures, tables, and the teaser.
- **Theme colors:** edit the tokens at the top of `assets/css/site.css` (light block, then the
  two dark blocks, which must stay identical).
- **Revert to the old site:** `cp legacy.html index.html` restores the previous page as the
  homepage; it only depends on `style.css`, `photos/`, `refs/`, and `cv/`, which are untouched.
