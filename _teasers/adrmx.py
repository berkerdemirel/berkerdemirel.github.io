"""Teaser for ADRMX: Additive Disentanglement of Domain Features with Remix Loss.

Render from the repo root:
    manim -qh --media_dir /tmp/teaser-media _teasers/adrmx.py Teaser
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from manim import *  # noqa: E402,F403
from teaser_style import *  # noqa: E402,F403

HUE = HUES["adrmx"]  # domain-invariant (class) information
DOM = GOLD  # domain-specific information of the first image
DOM2 = "#E4703C"  # domain-specific information of a second image
EMPTY = "#1C2024"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACS = os.path.join(ROOT, "blog", "adrmx", "fig-pacs.jpg")

# Which cells of the toy feature vector carry domain-specific information.
PATTERN = [0, 1, 0, 0, 1, 0]


def pacs(i, height=1.5):
    """i-th panel of the PACS strip: 0 art elephant, 1 cartoon elephant, 2 art horse, 3 cartoon horse."""
    im = Image.open(PACS).convert("RGBA")
    crop = im.crop((i * 344 + 12, 0, i * 344 + 332, 320))
    mob = ImageMobject(np.array(crop)).scale_to_fit_height(height)
    return Group(mob, SurroundingRectangle(mob, color=GREY, buff=0, stroke_width=1.5))


def vector(colors, cell=0.28):
    return VGroup(
        *[Square(cell, stroke_width=0, fill_color=c, fill_opacity=1) for c in colors]
    ).arrange(DOWN, buff=0.05)


def label_vec(dom=DOM):
    return vector([dom if p else HUE for p in PATTERN])


def domain_vec(dom=DOM):
    return vector([dom if p else EMPTY for p in PATTERN])


def dinv_vec():
    return vector([EMPTY if p else HUE for p in PATTERN])


def encoder(text, color):
    body = Polygon([-0.75, -1.0, 0], [0.75, -0.55, 0], [0.75, 0.55, 0], [-0.75, 1.0, 0],
                   stroke_color=color, stroke_width=2.5, fill_color=color, fill_opacity=0.12)
    return VGroup(body, tex(text, 22, color).move_to(body))


def node(sign):
    c = Circle(0.2, stroke_color=SOFT, stroke_width=2)
    bar = Line(LEFT * 0.11, RIGHT * 0.11, stroke_width=2.5, color=SOFT)
    if sign == "+":
        return VGroup(c, bar, Line(DOWN * 0.11, UP * 0.11, stroke_width=2.5, color=SOFT))
    return VGroup(c, bar)


def arrow(a, b, **kw):
    return Arrow(a, b, buff=0.12, stroke_width=2.5, color=GREY, tip_length=0.16, max_tip_length_to_length_ratio=0.25, **kw)


class Teaser(Scene):
    def construct(self):
        cap = Captioner(self)

        # ---- 1. Domain generalization -----------------------------------
        names = ["photo", "art", "cartoon", "sketch"]
        chips = VGroup()
        for i, n in enumerate(names):
            box = RoundedRectangle(width=2.3, height=1.0, corner_radius=0.16,
                                   stroke_color=SOFT if n != "art" else HUE, stroke_width=2,
                                   fill_color=PANEL, fill_opacity=1)
            if n == "art":
                box = DashedVMobject(box, num_dashes=40)
            chips.add(VGroup(box, tex(n, 30, INK).move_to(box)))
        chips.arrange(RIGHT, buff=0.55).move_to(UP * 0.2)
        head = tex("PACS", 28, GREY).next_to(chips, UP, buff=0.8)
        tags = VGroup()
        for i, ch in enumerate(chips):
            t = tex("unseen at test" if i == 1 else "train", 24, HUE if i == 1 else GREY)
            tags.add(t.next_to(ch, DOWN, buff=0.3))
        cap.show("Domain generalization: train on some domains, test on an unseen one")
        self.play(FadeIn(head), LaggedStart(*[FadeIn(c, shift=0.2 * UP) for c in chips], lag_ratio=0.15), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(t) for t in tags], lag_ratio=0.15), run_time=0.8)
        self.wait(1.7)
        self.play(FadeOut(VGroup(chips, tags, head)), run_time=0.5)

        # ---- 2. Invariant-only features drop useful cues -----------------
        feat = label_vec().scale(1.25).move_to(LEFT * 3.2 + UP * 0.4)
        flab = tex("features", 26, GREY).next_to(feat, UP, buff=0.3)
        key = VGroup(
            VGroup(Square(0.25, stroke_width=0, fill_color=HUE, fill_opacity=1), tex("domain-invariant", 24, SOFT)).arrange(RIGHT, buff=0.2),
            VGroup(Square(0.25, stroke_width=0, fill_color=DOM, fill_opacity=1), tex("domain-specific", 24, SOFT)).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(feat, RIGHT, buff=0.8)
        cap.show("Most methods discard domain-specific features, yet art and cartoon share colors and compositions")
        cap.need("domain-invariant", "domain-specific")
        self.play(FadeIn(feat), FadeIn(flab), FadeIn(key), run_time=0.7)
        crosses = VGroup(*[Cross(feat[i], stroke_width=3, stroke_color=WARM, scale_factor=0.8) for i, p in enumerate(PATTERN) if p])
        self.play(*[feat[i].animate.set_fill(EMPTY) for i, p in enumerate(PATTERN) if p], Create(crosses), run_time=0.8)
        self.wait(0.6)

        imgs = Group(pacs(0), pacs(1), pacs(2), pacs(3)).arrange_in_grid(rows=2, cols=2, buff=0.25).move_to(RIGHT * 3.2 + UP * 0.35)
        ctitle = VGroup(tex("art", 24, GREY).next_to(imgs[0], UP, buff=0.15), tex("cartoon", 24, GREY).next_to(imgs[1], UP, buff=0.15))
        self.play(FadeOut(key), FadeIn(imgs, shift=0.2 * LEFT), FadeIn(ctitle), run_time=0.8)
        self.wait(2.0)
        self.play(FadeOut(Group(feat, flab, crosses, imgs, ctitle)), run_time=0.5)

        # ---- 3. Additive disentanglement ----------------------------------
        x_img = pacs(0, 1.3).move_to(LEFT * 6.1)
        enc_l = encoder("label enc.", HUE).move_to(LEFT * 4.05 + UP * 1.35)
        enc_d = encoder("domain enc.", DOM).move_to(LEFT * 4.05 + DOWN * 1.35)
        v_l = label_vec().move_to(LEFT * 2.2 + UP * 1.35)
        v_d = domain_vec().move_to(LEFT * 2.2 + DOWN * 1.35)
        l_l = tex(r"$x_{\mathrm{label}}$", 32, INK).next_to(v_l, UP, buff=0.18)
        l_d = tex(r"$x_{\mathrm{domain}}$", 32, INK).next_to(v_d, DOWN, buff=0.18)
        minus = node("-").move_to(LEFT * 0.6)
        v_i = dinv_vec().move_to(RIGHT * 0.9)
        l_i = tex(r"$x_{\mathrm{dinv}}$", 32, HUE).next_to(v_i, UP, buff=0.18)
        eq_s = r"$x_{\mathrm{dinv}} = x_{\mathrm{label}} - x_{\mathrm{domain}}$"
        eq = tex(eq_s, 34, INK).to_edge(UP, buff=0.55)

        a1 = arrow(x_img.get_right(), enc_l.get_left())
        a2 = arrow(x_img.get_right(), enc_d.get_left())
        a3 = arrow(enc_l.get_right(), v_l.get_left())
        a4 = arrow(enc_d.get_right(), v_d.get_left())
        cap.show("Two encoders: one for the class, one for the domain")
        cap.need(r"$x_{\mathrm{label}}$", r"$x_{\mathrm{domain}}$")
        self.play(FadeIn(x_img), run_time=0.5)
        self.play(GrowArrow(a1), GrowArrow(a2), FadeIn(enc_l), FadeIn(enc_d), run_time=1.0)
        self.play(GrowArrow(a3), GrowArrow(a4), FadeIn(v_l), FadeIn(v_d), FadeIn(l_l), FadeIn(l_d), run_time=1.0)
        self.wait(2.45)

        a5 = arrow(v_l.get_right(), minus.get_left() + UP * 0.05)
        a6 = arrow(v_d.get_right(), minus.get_left() + DOWN * 0.05)
        a7 = arrow(minus.get_right(), v_i.get_left())
        loss_s = [
            r"$\mathcal{L}_{\mathrm{CE}}$  class",
            r"$\mathcal{L}_{\mathrm{cont}}$  contrastive",
            r"$-\lambda\,\mathcal{L}_{\mathrm{disc}}$  adversarial",
        ]
        losses = VGroup(*[tex(t, 24, SOFT) for t in loss_s]).arrange(DOWN, aligned_edge=LEFT, buff=0.3).next_to(v_i, RIGHT, buff=0.75)
        brace = Brace(losses, LEFT, color=GREY, buff=0.15)
        cap.show("Their difference is the domain-invariant part")
        cap.need(eq_s, *loss_s)
        self.play(Write(eq), GrowArrow(a5), GrowArrow(a6), FadeIn(minus), run_time=1.0)
        self.play(GrowArrow(a7), TransformFromCopy(v_l, v_i), FadeIn(l_i), run_time=1.0)
        self.play(FadeIn(brace), LaggedStart(*[FadeIn(l, shift=0.15 * RIGHT) for l in losses], lag_ratio=0.3), run_time=1.5)
        self.wait(2.5)

        # ---- 4. Remix ------------------------------------------------------
        keep = VGroup(v_i, l_i)
        img1 = pacs(0, 1.25)
        img2 = pacs(1, 1.25)
        cap.show("Remix: an image of the same class from another domain")
        cap.need(r"$x'_{\mathrm{domain}}$")
        self.play(
            FadeOut(Group(x_img, enc_l, enc_d, v_l, v_d, l_l, l_d, minus, a1, a2, a3, a4, a5, a6, a7, losses, brace, eq)),
            keep.animate.move_to(LEFT * 2.0 + UP * 1.1),
            run_time=0.9,
        )
        img1.next_to(keep, LEFT, buff=0.9)
        img2.move_to([img1.get_x(), -1.45, 0])
        v_d2 = domain_vec(DOM2).move_to([v_i.get_x(), -1.45, 0])
        l_d2 = tex(r"$x'_{\mathrm{domain}}$", 32, DOM2).next_to(v_d2, DOWN, buff=0.18)
        tag1 = tex("elephant, art", 22, GREY).next_to(img1, UP, buff=0.12)
        tag2 = tex("elephant, cartoon", 22, GREY).next_to(img2, DOWN, buff=0.12)
        b1 = arrow(img1.get_right(), v_i.get_left())
        b2 = arrow(img2.get_right(), v_d2.get_left())
        self.play(FadeIn(img1), FadeIn(tag1), GrowArrow(b1), run_time=0.6)
        self.play(FadeIn(img2), FadeIn(tag2), GrowArrow(b2), FadeIn(v_d2), FadeIn(l_d2), run_time=0.8)
        self.wait(2.0)

        plus = node("+").move_to(RIGHT * 0.7 + DOWN * 0.15)
        v_r = vector([DOM2 if p else HUE for p in PATTERN]).move_to(RIGHT * 2.3 + DOWN * 0.15)
        l_r = tex(r"$x_{\mathrm{remixed}}$", 32, INK).next_to(v_r, UP, buff=0.18)
        c1 = arrow(v_i.get_right(), plus.get_left() + UP * 0.05)
        c2 = arrow(v_d2.get_right(), plus.get_left() + DOWN * 0.05)
        c3 = arrow(plus.get_right(), v_r.get_left())
        eq2_s = r"$x_{\mathrm{remixed}} = x_{\mathrm{dinv}} + x'_{\mathrm{domain}}$"
        eq2 = tex(eq2_s, 34, INK).to_edge(UP, buff=0.55)
        clf = panel(2.1, 0.95, HUE).move_to(RIGHT * 4.6 + DOWN * 0.15)
        clf_t = VGroup(tex("label classifier", 22, HUE), tex("(shared)", 18, GREY)).arrange(DOWN, buff=0.06).move_to(clf)
        c4 = arrow(v_r.get_right(), clf.get_left())
        out_s = r"$\mathcal{L}_{\mathrm{remix}}$"
        out = tex(out_s, 28, INK).next_to(clf, DOWN, buff=0.35)
        cap.show("Their sum is a new training sample in latent space")
        cap.need(eq2_s, "label classifier", out_s)
        self.play(Write(eq2), FadeIn(plus), GrowArrow(c1), GrowArrow(c2), run_time=0.9)
        self.play(GrowArrow(c3), FadeIn(v_r, shift=0.2 * RIGHT), FadeIn(l_r), run_time=0.8)
        self.play(GrowArrow(c4), FadeIn(clf), FadeIn(clf_t), run_time=0.7)
        self.play(FadeIn(out, shift=0.15 * DOWN), run_time=0.5)
        self.wait(2.05)
        self.play(FadeOut(Group(keep, img1, img2, tag1, tag2, b1, b2, v_d2, l_d2, plus, v_r, l_r, c1, c2, c3, c4, eq2, clf, clf_t, out)), run_time=0.6)

        # ---- 5. Result -----------------------------------------------------
        rows = [("ADRMX", "67.6", HUE), ("CORAL", "67.5", SOFT), ("SagNet", "67.2", SOFT), ("ERM", "66.6", SOFT)]
        table = VGroup()
        for name, val, col in rows:
            table.add(VGroup(tex(name, 34, col), tex(val, 34, col)))
        for i, r in enumerate(table):
            r[0].move_to([-1.8, 1.55 - i * 0.75, 0], aligned_edge=LEFT)
            r[1].move_to([1.8, 1.55 - i * 0.75, 0], aligned_edge=RIGHT)
        rule = Line([-2.0, 1.17, 0], [2.0, 1.17, 0], stroke_width=1.5, color=DIM)
        cap.show("Best average accuracy across DomainBed's seven datasets")
        cap.need(*[f"{n} {v}" for n, v, _ in rows])
        self.play(LaggedStart(*[FadeIn(r, shift=0.1 * UP) for r in table], lag_ratio=0.15), Create(rule), run_time=1.3)
        self.wait(3.9)
        cap.clear()

        # ---- 6. Title card -------------------------------------------------
        card = title_card(
            "ADRMX",
            "Additive Disentanglement of Domain Features with Remix Loss",
            ["Berker Demirel, Erchan Aptoula, Huseyin Ozkan"],
            HUE,
            paper_url="https://arxiv.org/abs/2308.06624",
            code_url="https://github.com/berkerdemirel/adrmx",
            venue="arXiv 2023",
        )
        self.play(FadeOut(VGroup(table, rule)), FadeIn(card), run_time=0.9)
        self.wait(2.6)
        cap.report()
