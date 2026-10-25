"""Shared look for the paper teaser videos.

Matches the existing lambda-JEPA / MorphGen teasers: black background, Computer
Modern type, one accent hue per paper, a caption line at the bottom of the frame,
and a title card with QR codes at the end.

Text and math are typeset by matplotlib's mathtext (fontset "cm"), exported as
SVG paths and loaded as manim mobjects, so no LaTeX installation is needed.

Render (from the repo root):
    manim -qh --media_dir /tmp/teaser-media _teasers/<paper>.py Teaser
"""

import hashlib
import os
import re
import tempfile

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from manim import (  # noqa: E402
    DOWN,
    UP,
    FadeIn,
    FadeOut,
    Group,
    ImageMobject,
    RoundedRectangle,
    SVGMobject,
    VGroup,
    Write,
    config,
)

matplotlib.rcParams.update(
    {
        "mathtext.fontset": "cm",
        "font.family": "serif",
        "font.serif": ["cmr10"],
        "axes.unicode_minus": False,
        "axes.formatter.use_mathtext": True,
        "svg.fonttype": "path",
    }
)

config.background_color = "#000000"

# One hue per paper (manim's default palette, as in the existing teasers).
HUES = {
    "lambda-jepa": "#58C4DD",
    "morphgen": "#5CD0B3",
    "sample-quality": "#CFA3E8",
    "ora": "#F0AC5F",
    "adrmx": "#83C167",
    "decompl": "#FC6255",
}

INK = "#FFFFFF"
SOFT = "#D9DCDF"
GREY = "#8E949A"
DIM = "#3C4046"
PANEL = "#0B1416"
WARM = "#E4703C"
GOLD = "#F0C05F"

CAPTION_Y = -3.35
_CACHE = os.environ.get("TEASER_CACHE", os.path.join(tempfile.gettempdir(), "teaser-tex-cache"))
os.makedirs(_CACHE, exist_ok=True)

# Font size -> scene units. 1 pt of matplotlib text becomes PT scene units.
PT = 0.0058


def _clean_svg(path):
    """matplotlib emits glyph <path> defs without a d= attribute for some glyphs; drop them."""
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<metadata>.*?</metadata>", "", s, flags=re.S)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    empty = re.findall(r'<path id="([^"]*)"(?![^>]*\sd=)[^>]*/>', s)
    s = re.sub(r'<path id="([^"]*)"(?![^>]*\sd=)[^>]*/>', "", s)
    for e in empty:
        s = re.sub(r'<use xlink:href="#%s"[^>]*/>' % re.escape(e), "", s)
    # The figure background patch would become a filled rectangle.
    s = re.sub(r'<g id="patch_1">.*?</g>', "", s, count=1, flags=re.S)
    open(path, "w", encoding="utf-8").write(s)


def tex(s, size=30, color=INK, weight=None):
    """Typeset `s` (plain text with optional $...$ math) in Computer Modern.

    `size` is in points; 30 pt is a good caption size at 1080p.
    Returns a VGroup-like SVGMobject whose height is proportional to `size`
    so that different strings at the same size share a baseline scale.
    """
    key = hashlib.md5(f"{s}|{weight}".encode()).hexdigest()
    path = os.path.join(_CACHE, f"{key}.svg")
    if not os.path.exists(path):
        fig = plt.figure(figsize=(0.01, 0.01))
        kw = {"fontweight": weight} if weight else {}
        fig.text(0, 0, s, fontsize=100, color="white", **kw)
        fig.savefig(path, transparent=True, bbox_inches="tight", pad_inches=0.0)
        plt.close(fig)
        _clean_svg(path)
    mob = SVGMobject(path, height=None, stroke_width=0)
    # matplotlib SVG units are pt at fontsize 100, so rescale to the requested size.
    mob.scale(size / 100 * PT * 1.333)
    mob.set_fill(color, opacity=1)
    mob.set_stroke(width=0)
    return mob


def read_time(*texts, wps=3.0, base=0.8):
    """Seconds a first-time viewer needs to read `texts` (each $...$ span counts as two words).

    Use it to size the hold after a beat: every caption, label, or equation that appears
    in the beat should be on screen at least this long before the next caption replaces it.
    """
    words = 0
    for t in texts:
        words += len(re.sub(r"\$[^$]*\$", " eq eq ", t).split())
    return base + words / wps


class Captioner:
    """Bottom-of-frame caption line.

    Captions change with a short fade-out followed by a fade-in, so two sentences are never
    on screen at once. Each caption's start time is recorded; call `report()` at the end of
    `construct` to print how long every caption stayed up against its reading time.
    """

    def __init__(self, scene, size=30, color=SOFT):
        self.scene = scene
        self.size = size
        self.color = color
        self.current = None
        self.log = []  # (text, start time, extra seconds of reading added via `need`)

    def _now(self):
        return float(getattr(self.scene.renderer, "time", 0.0))

    def show(self, s, run_time=0.6):
        new = tex(s, self.size, self.color).move_to([0, CAPTION_Y, 0])
        if self.current is not None:
            self.scene.play(FadeOut(self.current, shift=0.08 * UP), run_time=0.3)
        self.log.append([s, self._now(), 0.0])
        self.scene.play(FadeIn(new, shift=0.08 * UP), run_time=max(0.3, run_time - 0.2))
        self.current = new
        return new

    def need(self, *texts):
        """Declare extra on-screen text (labels, equations) introduced during the current caption."""
        if self.log:
            self.log[-1][2] += read_time(*texts, base=0.0)

    def clear(self, run_time=0.4):
        if self.current is not None:
            self.scene.play(FadeOut(self.current), run_time=run_time)
            self.current = None
        self.log.append([None, self._now(), 0.0])

    def report(self):
        """Print each caption's time on screen and flag any shorter than its reading time."""
        end = self._now()
        print("\n--- caption timing (s) ---")
        for i, (text, t0, extra) in enumerate(self.log):
            if text is None:
                continue
            t1 = self.log[i + 1][1] if i + 1 < len(self.log) else end
            need = read_time(text) + extra
            flag = "  <-- too short" if t1 - t0 < need else ""
            print(f"{t0:6.1f}  on {t1 - t0:4.1f}  need {need:4.1f}{flag}  {text[:70]}")
        print(f"total {end:.1f} s\n")


def panel(width, height, color, fill_opacity=0.12, radius=0.18, stroke_width=2):
    """Rounded box in the paper hue, used for blocks and modules."""
    return RoundedRectangle(
        width=width,
        height=height,
        corner_radius=radius,
        stroke_color=color,
        stroke_width=stroke_width,
        fill_color=color,
        fill_opacity=fill_opacity,
    )


def qr(url, size=1.6):
    """QR code for `url` (segno), white modules on a transparent background."""
    import segno

    key = hashlib.md5(url.encode()).hexdigest()
    path = os.path.join(_CACHE, f"qr_{key}.png")
    if not os.path.exists(path):
        from PIL import Image

        segno.make(url, error="m").save(path, kind="png", scale=24, border=1, dark="#ffffff", light=None)
        Image.open(path).convert("RGBA").save(path)  # manim expects 8-bit RGBA
    mob = ImageMobject(path).scale_to_fit_height(size)
    mob.set_resampling_algorithm(0)  # nearest neighbour keeps the modules crisp
    return mob


def title_card(title, subtitle, authors, hue, paper_url=None, code_url=None, venue=None):
    """Closing card: title in the paper hue, subtitle, authors, and optional QR codes."""
    items = [tex(title, 72, hue)]
    items.append(tex(subtitle, 30, INK))
    if venue:
        items.append(tex(venue, 24, hue))
    for line in authors if isinstance(authors, (list, tuple)) else [authors]:
        items.append(tex(line, 22, GREY))
    head = VGroup(*items).arrange(DOWN, buff=0.2)
    head[1].shift(0.05 * DOWN)
    if not (paper_url or code_url):
        return head.move_to([0, 0, 0])
    codes = []
    for label, url in (("Paper", paper_url), ("Code", code_url)):
        if url:
            codes.append(Group(qr(url), tex(label, 22, SOFT)).arrange(DOWN, buff=0.15))
    row = Group(*codes).arrange(buff=1.2)
    return Group(head, row).arrange(DOWN, buff=0.55).move_to([0, 0, 0])


def image(path, height):
    """Raster image (e.g. a cropped paper figure) at a given scene height."""
    return ImageMobject(path).scale_to_fit_height(height)


__all__ = [
    "HUES", "INK", "SOFT", "GREY", "DIM", "PANEL", "WARM", "GOLD", "CAPTION_Y",
    "tex", "read_time", "Captioner", "panel", "qr", "title_card", "image", "Write",
]
