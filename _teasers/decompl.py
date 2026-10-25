"""Teaser for DECOMPL (ICIP 2024).

Render from the repo root:
    manim -qh --media_dir /tmp/teaser-media _teasers/decompl.py Teaser
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from manim import *  # noqa: E402,F403
from teaser_style import *  # noqa: E402,F403

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUE = HUES["decompl"]
LEFT_T = HUE
RIGHT_T = "#58C4DD"
KEY = GOLD

# Player box centres (pixels) in the cropped broadcast frame, read off Figure 1 of the paper.
CROP = (30, 42, 608, 366)
LEFT_PX = [(73, 212), (132, 228), (160, 158), (262, 222), (299, 180), (320, 138)]
RIGHT_PX = [(382, 140), (350, 205), (386, 250), (420, 178), (427, 228), (483, 208)]  # first = key player


def frame_image(height):
    img = Image.open(os.path.join(ROOT, "blog", "decompl", "fig-overview.jpg")).convert("RGBA").crop(CROP)
    return ImageMobject(np.array(img)).scale_to_fit_height(height)


class Teaser(Scene):
    def construct(self):
        cap = Captioner(self)
        W_PX, H_PX = CROP[2] - CROP[0], CROP[3] - CROP[1]

        # ---- 1. The task --------------------------------------------------
        frame = frame_image(4.3).move_to([0, 0.45, 0])

        def px(u, v, mob=frame):
            c = mob.get_center()
            return np.array([c[0] + (u / W_PX - 0.5) * mob.width, c[1] + (0.5 - v / H_PX) * mob.height, 0])

        self.play(FadeIn(frame, scale=0.97), run_time=0.6)
        cap.show("Group activity recognition: one label for the whole team")
        label = tex("right spike", 40, KEY).next_to(frame, DOWN, buff=0.3)
        cap.need("right spike")
        self.wait(1.3)
        self.play(FadeIn(label, shift=0.1 * UP), run_time=0.5)
        self.wait(2.1)

        # ---- 2. One frame instead of a clip -------------------------------
        cap.show(r"DECOMPL: one RGB frame and the players' boxes")
        small = 3.2
        self.play(FadeOut(label), frame.animate.scale_to_fit_height(small).move_to([-0.6, 0.3, 0]), run_time=0.7)
        stack = Group(*[frame_image(small).set_opacity(0.35 - 0.1 * k).move_to(frame.get_center() + (k + 1) * np.array([0.32, 0.25, 0])) for k in range(3)])
        time_arrow = Arrow(frame.get_corner(DL) + [-0.2, 0.1, 0], frame.get_corner(DL) + [0.6, 0.75, 0], buff=0, stroke_width=3, color=GREY, max_tip_length_to_length_ratio=0.25)
        time_lbl = tex("time", 26, GREY).next_to(time_arrow.get_start(), LEFT, buff=0.08)
        cap.need("time")
        self.add(*stack[::-1])
        self.bring_to_front(frame)
        self.play(LaggedStart(*[FadeIn(s) for s in stack], lag_ratio=0.2), GrowArrow(time_arrow), FadeIn(time_lbl), run_time=0.8)
        self.wait(0.4)
        self.play(FadeOut(stack), FadeOut(time_arrow), FadeOut(time_lbl),
                  frame.animate.scale_to_fit_height(4.3).move_to([0, 0.45, 0]), run_time=0.7)

        # Players: dots at the box centres.
        lefts = VGroup(*[Dot(px(u, v), radius=0.09, color=LEFT_T) for u, v in LEFT_PX])
        rights = VGroup(*[Dot(px(u, v), radius=0.09, color=KEY if k == 0 else RIGHT_T) for k, (u, v) in enumerate(RIGHT_PX)])
        self.play(LaggedStart(*[GrowFromCenter(d) for d in [*lefts, *rights]], lag_ratio=0.06), run_time=0.9)
        self.wait(0.2)

        # ---- 3. Visual branch: per-team attention pooling -------------------
        cap.show("Visual branch: attention pooling over each team's players")
        court_c = np.array([-3.7, 0.4, 0])
        players = VGroup(lefts, rights)
        target = players.copy().scale(0.8).move_to(court_c)
        court = Rectangle(width=target.width + 0.7, height=target.height + 0.6, stroke_color=DIM, stroke_width=2).move_to(court_c)
        net_x = (target[0][5].get_x() + target[1][1].get_x()) / 2
        net = DashedLine([net_x, court.get_top()[1], 0], [net_x, court.get_bottom()[1], 0], color=GREY, stroke_width=2, dash_length=0.08)
        self.play(FadeOut(frame), Transform(players, target), Create(court), Create(net), run_time=1.0)

        def tokens(color, n=6):
            return VGroup(*[RoundedRectangle(width=0.42, height=0.42, corner_radius=0.06, stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=0.35) for _ in range(n)]).arrange(buff=0.14)

        tok_l, tok_r = tokens(LEFT_T), tokens(RIGHT_T)
        tok_r[0].set_stroke(KEY).set_fill(KEY, 0.45)
        tok_l.move_to([2.6, 1.15, 0])
        tok_r.move_to([2.6, -0.95, 0])
        self.play(LaggedStart(*[TransformFromCopy(d, t) for d, t in zip(players[0], tok_l)], lag_ratio=0.08),
                  LaggedStart(*[TransformFromCopy(d, t) for d, t in zip(players[1], tok_r)], lag_ratio=0.08), run_time=1.1)

        # attention weights as bars above each token
        w_l = [0.15, 0.1, 0.12, 0.2, 0.18, 0.25]
        w_r = [0.42, 0.14, 0.1, 0.14, 0.1, 0.1]

        def bars(tok, ws, color):
            return VGroup(*[
                Rectangle(width=0.26, height=max(0.05, 1.9 * w), stroke_width=0, fill_color=color, fill_opacity=0.9).next_to(t, UP, buff=0.06)
                for t, w in zip(tok, ws)
            ])

        b_l, b_r = bars(tok_l, w_l, LEFT_T), bars(tok_r, w_r, RIGHT_T)
        b_r[0].set_fill(KEY)
        att = tex(r"$X = \sum_i a_i\, x_i$", 38, HUE).move_to([2.6, 2.95, 0])
        cap.need(r"$X = \sum_i a_i\, x_i$")
        self.play(FadeIn(att, shift=0.1 * DOWN), LaggedStart(*[GrowFromEdge(b, DOWN) for b in [*b_l, *b_r]], lag_ratio=0.04), run_time=1.0)
        self.wait(0.7)

        pooled_l = RoundedRectangle(width=0.6, height=0.6, corner_radius=0.08, stroke_color=LEFT_T, stroke_width=2, fill_color=LEFT_T, fill_opacity=0.6).move_to([5.6, 1.15, 0])
        pooled_r = RoundedRectangle(width=0.6, height=0.6, corner_radius=0.08, stroke_color=RIGHT_T, stroke_width=2, fill_color=RIGHT_T, fill_opacity=0.6).move_to([5.6, -0.95, 0])
        pl_lbl = tex(r"$X_l$", 34, SOFT).next_to(pooled_l, RIGHT, buff=0.15)
        pr_lbl = tex(r"$X_r$", 34, SOFT).next_to(pooled_r, RIGHT, buff=0.15)
        cap.need(r"$X_l$", r"$X_r$")
        self.play(ReplacementTransform(VGroup(tok_l, b_l), pooled_l), ReplacementTransform(VGroup(tok_r, b_r), pooled_r),
                  FadeIn(pl_lbl), FadeIn(pr_lbl), run_time=0.9)
        visual = VGroup(pooled_l, pooled_r, pl_lbl, pr_lbl)
        self.wait(0.5)

        # ---- 4. Coordinate branch --------------------------------------------
        cap.show("Coordinate branch: where the players stand, no pixels")
        self.play(FadeOut(att), visual.animate.scale(0.8).move_to([5.6, 2.55, 0]), run_time=0.6)
        dots = [*players[0], *players[1]]
        web = VGroup(*[
            Line(a.get_center(), b.get_center(), stroke_width=1.2, color=HUE, stroke_opacity=0.35)
            for i, a in enumerate(dots) for b in dots[i + 1:]
        ])
        key_web = VGroup(*[Line(dots[6].get_center(), d.get_center(), stroke_width=2.5, color=HUE) for d in dots if d is not dots[6]])
        self.play(LaggedStart(*[Create(l) for l in key_web], lag_ratio=0.05), run_time=0.8)
        self.play(FadeIn(web), FadeOut(key_web), run_time=0.6)
        self.bring_to_front(players)

        coord_box = VGroup(panel(3.3, 0.9, HUE), tex("coordinate module", 30, INK))
        coord_box[1].move_to(coord_box[0])
        coord_box.move_to([1.9, -1.9, 0])
        pool_c = RoundedRectangle(width=0.6, height=0.6, corner_radius=0.08, stroke_color=HUE, stroke_width=2, fill_color=HUE, fill_opacity=0.6).move_to([5.6, -1.9, 0])
        pc_lbl = tex(r"$X_{\mathrm{coord}}$", 32, SOFT).next_to(pool_c, RIGHT, buff=0.15)
        a1 = Arrow(court.get_bottom() + [0.6, 0, 0], coord_box.get_left(), buff=0.15, stroke_width=3, color=GREY)
        a2 = Arrow(coord_box.get_right(), pool_c.get_left(), buff=0.1, stroke_width=3, color=GREY)
        cap.need("coordinate module", r"$X_{\mathrm{coord}}$")
        self.play(GrowArrow(a1), FadeIn(coord_box), run_time=0.6)
        self.play(GrowArrow(a2), FadeIn(pool_c), FadeIn(pc_lbl), run_time=0.6)
        alone = tex(r"positions alone: $73.5\%$ accuracy", 34, HUE).move_to([2.6, 0.6, 0])
        cap.need("positions alone: 73.5% accuracy")
        self.play(FadeIn(alone, shift=0.1 * UP), run_time=0.5)
        self.wait(1.8)

        # ---- 5. Decomposed heads -----------------------------------------------
        cap.show("Both branches predict side, team and group activity")
        coord = VGroup(pool_c, pc_lbl)
        self.play(FadeOut(VGroup(players, court, net, web, a1, a2, coord_box, alone)),
                  visual.animate.scale(1.25).move_to([-4.6, 1.0, 0]), coord.animate.move_to([-4.6, -1.3, 0]), run_time=0.8)
        heads = VGroup(*[
            VGroup(panel(2.9, 0.8, HUE, fill_opacity=0.1, radius=0.14, stroke_width=1.8), tex(t, 30, INK))
            for t in ("side", "team", "group")
        ])
        for h in heads:
            h[1].move_to(h[0])
        heads.arrange(DOWN, buff=0.4).move_to([-0.4, 0, 0])
        links = VGroup(*[
            Line(src.get_right() + [0.15, 0, 0], h.get_left(), stroke_width=1.6, color=GREY, stroke_opacity=0.7)
            for src in (visual, coord) for h in heads
        ])
        arrows = VGroup(*[Arrow(h.get_right(), h.get_right() + [1.1, 0, 0], buff=0.15, stroke_width=3, color=GREY) for h in heads])
        outs = VGroup(tex("right", 34, SOFT), tex("spike", 34, SOFT), tex("right spike", 38, KEY))
        for o, a in zip(outs, arrows):
            o.next_to(a, RIGHT, buff=0.2)
        cap.need("side team group", "right spike right spike")
        self.play(Create(links), LaggedStart(*[FadeIn(h) for h in heads], lag_ratio=0.15), run_time=0.9)
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.2),
                  LaggedStart(*[FadeIn(o, shift=0.1 * RIGHT) for o in outs], lag_ratio=0.2), run_time=0.9)
        self.wait(2.6)

        # ---- 6. Re-annotation ---------------------------------------------
        cap.show("We also re-annotated Volleyball so labels describe the group")
        self.play(FadeOut(VGroup(visual, coord, heads, links, arrows, outs)), run_time=0.5)
        old = tex("pass", 60, GREY)
        strike = Line(old.get_left() + [-0.1, 0, 0], old.get_right() + [0.1, 0, 0], color=HUE, stroke_width=4)
        new = tex("set", 60, KEY)
        pair = VGroup(old, new).arrange(buff=4.2).move_to([0, 1.0, 0])
        strike.move_to(old)
        arrow = Arrow(old.get_right(), new.get_left(), buff=0.5, stroke_width=4, color=GREY)
        count = tex(r"$497$ of $4821$ labels corrected", 40, INK).move_to([0, -1.0, 0])
        cap.need("pass set", "497 of 4821 labels corrected")
        self.play(FadeIn(old), run_time=0.4)
        self.play(Create(strike), GrowArrow(arrow), FadeIn(new, shift=0.1 * LEFT), run_time=0.7)
        self.play(FadeIn(count, shift=0.1 * UP), run_time=0.5)
        self.wait(3.4)

        # ---- 7. Result ------------------------------------------------------
        cap.show("Best RGB-only accuracy on corrected labels, with a tenth of the FLOPs")
        self.play(FadeOut(VGroup(old, strike, new, arrow, count)), run_time=0.5)
        big = tex(r"$95.2\%$", 96, KEY)
        big_lbl = tex("accuracy", 30, GREY)
        stat = VGroup(big, big_lbl).arrange(DOWN, buff=0.3).move_to([-3.4, 0.4, 0])

        flops_title = tex("GFLOPs, without backbone", 28, GREY)
        frows = [("DIN", 0.311), ("DECOMPL", 0.031)]
        scale = 3.6 / 0.311
        fbars = VGroup()
        for n, v in frows:
            col = HUE if n == "DECOMPL" else GREY
            name = tex(n, 32, KEY if n == "DECOMPL" else SOFT)
            bar = Rectangle(width=max(0.06, v * scale), height=0.5, stroke_width=0, fill_color=col, fill_opacity=0.9)
            val = tex(f"{v}", 30, SOFT)
            fbars.add(VGroup(name, bar, val))
        names_w = max(r[0].width for r in fbars)
        for k, r in enumerate(fbars):
            y = -k * 0.85
            r[0].move_to([0, y, 0]).align_to([names_w, 0, 0], RIGHT)
            r[1].move_to([0, y, 0]).align_to([names_w + 0.25, 0, 0], LEFT)
            r[2].next_to(r[1], RIGHT, buff=0.15)
        flops_g = VGroup(flops_title, fbars).arrange(DOWN, buff=0.5).move_to([3.0, 0.4, 0])
        cap.need("95.2% accuracy", "GFLOPs, without backbone", "DIN 0.311 DECOMPL 0.031")
        self.play(FadeIn(stat, shift=0.1 * UP), run_time=0.6)
        self.play(FadeIn(flops_title), LaggedStart(*[GrowFromEdge(r[1], LEFT) for r in fbars], lag_ratio=0.2),
                  LaggedStart(*[FadeIn(VGroup(r[0], r[2])) for r in fbars], lag_ratio=0.2), run_time=0.9)
        self.wait(4.6)

        # ---- 8. Title card ----------------------------------------------------
        self.play(FadeOut(VGroup(stat, flops_g)), run_time=0.5)
        cap.clear()
        card = title_card(
            "DECOMPL",
            "Decompositional Learning with Attention Pooling for Group Activity Recognition from a Single Volleyball Image",
            ["Berker Demirel, Huseyin Ozkan"],
            HUE,
            paper_url="https://arxiv.org/abs/2303.06439",
            code_url="https://github.com/berkerdemirel/decompl",
            venue="ICIP 2024",
        )
        self.play(FadeIn(card, shift=0.1 * UP), run_time=0.8)
        self.wait(2.3)
        cap.report()
