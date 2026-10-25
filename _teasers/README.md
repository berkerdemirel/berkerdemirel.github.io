# Teaser videos

Source for the 30–40 s paper teasers embedded in the blog posts. The underscore
prefix keeps this folder out of the published GitHub Pages site.

- `teaser_style.py`: shared look (black background, Computer Modern type,
  per-paper hue, bottom captions, title card with QR codes).
- `<slug>.py`: one `Teaser` scene per paper. The λ-JEPA and MorphGen teasers
  predate this folder, so their sources are not here.

Text and math are typeset with matplotlib's mathtext (`fontset="cm"`), so no
LaTeX installation is needed.

## Setup

```bash
uv venv --python 3.12 .manim
# pycairo needs pkg-config and cairo (brew install cairo pkgconf)
uv pip install --python .manim/bin/python manim matplotlib segno "pillow<11"
```

`pillow<11` matters: manim 0.22's `ImageMobject` breaks on newer Pillow.

## Render

```bash
.manim/bin/manim -qh --media_dir /tmp/teaser-media _teasers/ora.py Teaser
ffmpeg -i /tmp/teaser-media/videos/ora/1080p60/Teaser.mp4 -c copy -movflags +faststart blog/ora/teaser.mp4
ffmpeg -ss 12 -i blog/ora/teaser.mp4 -frames:v 1 -vf scale=1280:-2 -q:v 3 blog/ora/poster.jpg
```

Use `-ql` for quick previews. `TEASER_CACHE=<dir>` changes where typeset
strings and QR codes are cached (default: the system temp dir).
