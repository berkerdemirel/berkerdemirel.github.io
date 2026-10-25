"""Teaser for "Out-of-Distribution Detection with Relative Angles" (NeurIPS 2025).

Render from the repo root:
    manim -qh --media_dir /tmp/teaser-media _teasers/ora.py Teaser
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from manim import *  # noqa: E402,F403
from teaser_style import *  # noqa: E402,F403

HUE = HUES["ora"]
C2 = "#58C4DD"

# Feature-space panel: local coordinates are mapped into the frame around BOX_C.
BOX_C = np.array([-2.75, 0.3, 0])
BASE = 0.92  # local units -> scene units
BOX_W, BOX_H = 8.2 * BASE, 5.3 * BASE
EQ_X = 4.15  # centre of the right-hand column
COL_L = 1.55  # left edge of the right-hand column's readout rows
P0 = np.array([1.15, -2.65])  # two points on the decision boundary (local coords)
P1 = np.array([2.75, 2.65])
DIR = (P1 - P0) / np.linalg.norm(P1 - P0)
NRM = np.array([DIR[1], -DIR[0]])  # points toward C2
MU = np.array([-1.7, -1.75])
Z_ID = np.array([-2.05, 0.75])
Z_OOD = np.array([1.35, 1.55])

# Fixed thresholds for the two scores in the rescaling beat. The distance threshold sits
# between the two features' distances at the original scale (4.05 and 1.02), so both scores
# agree there; scaling the space by k > 1.27 pushes the OOD feature past it.
DIST_TAU = 1.30
THETA_TAU = 30.0
K_MAX = 1.4

rng = np.random.default_rng(3)
C1_PTS = np.array([-2.65, 1.55]) + 0.42 * rng.standard_normal((26, 2))
C2_PTS = np.array([3.05, -1.25]) + 0.36 * rng.standard_normal((18, 2))


def settle(scene, cap, after=0.3, minimum=0.2):
    """Hold until the current caption (plus declared labels) has been up for its reading time.

    `after` is how long the caption will still be on screen once this returns (scene
    fade-outs plus the caption's own 0.3 s fade-out), which counts toward reading time.
    """
    text, t0, extra = cap.log[-1]
    left = read_time(text) + extra + 0.1 - (cap._now() - t0) - after
    scene.wait(max(minimum, left))


def extra(cap, seconds):
    """Reading time for an equation, which `read_time` would undercount as two words."""
    cap.log[-1][2] += seconds


class Teaser(Scene):
    def construct(self):
        cap = Captioner(self)
        k = ValueTracker(1.0)  # global feature scale
        zx = ValueTracker(Z_ID[0])
        zy = ValueTracker(Z_ID[1])
        ui = {"verdicts": False}

        def P(v):
            v = np.asarray(v, dtype=float)
            return BOX_C + np.array([v[0], v[1], 0]) * k.get_value() * BASE

        def z_local():
            return np.array([zx.get_value(), zy.get_value()])

        def proj(z):
            return z - np.dot(z - P0, NRM) * NRM

        def theta_deg(z):
            d = proj(z)
            u, v = z - MU, d - MU
            return float(np.degrees(np.arccos(np.clip(np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v)), -1, 1))))

        def dist(z):
            # Distance to the boundary in the rescaled space.
            return float(abs(np.dot(z - P0, NRM)) * k.get_value())

        # ------------------------------------------------------------ beat 1: the problem
        enc = Polygon([-1.0, 1.1, 0], [1.0, 0.55, 0], [1.0, -0.55, 0], [-1.0, -1.1, 0],
                      stroke_color=HUE, stroke_width=3, fill_color=HUE, fill_opacity=0.12)
        f_lab = tex(r"$f$", 44, INK).move_to(enc)
        id_icon = VGroup(
            RoundedRectangle(width=1.1, height=1.1, corner_radius=0.12, stroke_color=HUE, stroke_width=2.5,
                             fill_color=HUE, fill_opacity=0.25),
            Circle(radius=0.28, color=HUE, stroke_width=3),
        )
        stripes = VGroup(*[Line([-0.5 + 0.2 * i, -0.55, 0], [-0.5 + 0.2 * i + 0.45, 0.55, 0], stroke_width=2.5,
                                color=GREY) for i in range(5)])
        ood_icon = VGroup(
            RoundedRectangle(width=1.1, height=1.1, corner_radius=0.12, stroke_color=GREY, stroke_width=2.5),
            stripes,
        )
        id_icon.move_to([-4.6, 1.0, 0])
        ood_icon.move_to([-4.6, -1.1, 0])
        id_t = tex("in-distribution", 22, SOFT).next_to(id_icon, DOWN, buff=0.15)
        ood_t = tex("out-of-distribution", 22, GREY).next_to(ood_icon, DOWN, buff=0.15)
        a1 = Arrow(id_icon.get_right(), enc.get_left() + 0.35 * UP, buff=0.15, stroke_width=3, color=GREY,
                   max_tip_length_to_length_ratio=0.12)
        a2 = Arrow(ood_icon.get_right(), enc.get_left() + 0.35 * DOWN, buff=0.15, stroke_width=3, color=GREY,
                   max_tip_length_to_length_ratio=0.12)
        out_box = panel(1.6, 1.6, GREY, fill_opacity=0.05).move_to([3.0, 0, 0])
        a3 = Arrow(enc.get_right(), out_box.get_left(), buff=0.15, stroke_width=3, color=GREY,
                   max_tip_length_to_length_ratio=0.12)
        z_lab = tex(r"$z$", 40, INK).move_to(out_box)
        q = tex("label?", 26, GREY).next_to(out_box, RIGHT, buff=0.3)
        VGroup(enc, f_lab, id_icon, ood_icon, id_t, ood_t, a1, a2, out_box, a3, z_lab, q).scale(1.25, about_point=ORIGIN).shift(0.25 * UP)

        cap.show(r"A classifier labels every input, even from classes it never saw")
        cap.need("in-distribution", "out-of-distribution", "label?")
        self.play(FadeIn(id_icon), FadeIn(id_t), FadeIn(ood_icon), FadeIn(ood_t), run_time=0.6)
        self.play(GrowArrow(a1), GrowArrow(a2), FadeIn(enc), Write(f_lab), run_time=0.9)
        self.play(GrowArrow(a3), FadeIn(out_box), Write(z_lab), run_time=0.7)
        self.play(FadeIn(q, shift=0.1 * RIGHT), run_time=0.4)
        settle(self, cap, after=0.8)
        self.play(*[FadeOut(m) for m in [id_icon, id_t, ood_icon, ood_t, a1, a2, a3, enc, f_lab, out_box, z_lab, q]],
                  run_time=0.5)

        # ------------------------------------------------------------ beat 2: projection
        frame = Rectangle(width=BOX_W, height=BOX_H, stroke_color=DIM, stroke_width=1.5).move_to(BOX_C)
        title = tex("penultimate feature space", 22, GREY).next_to(frame, UP, buff=0.12).align_to(frame, LEFT)

        # Everything inside the panel is clipped to its rectangle (which does not scale with k):
        # region tints are the rectangle cut by the boundary's half-plane, the boundary is clipped
        # to the rectangle, and dots outside it are simply not drawn.
        half_w, half_h = BOX_W / 2, BOX_H / 2
        rect = [BOX_C + np.array([sx * half_w, sy * half_h, 0]) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

        def inside(q, margin=0.0):
            return abs(q[0] - BOX_C[0]) <= half_w - margin and abs(q[1] - BOX_C[1]) <= half_h - margin

        def region(side):
            o, n = P(P0), np.array([NRM[0], NRM[1], 0.0]) * side
            f = [float(np.dot(q - o, n)) for q in rect]
            pts = []
            for i in range(4):
                a, b, fa, fb = rect[i], rect[(i + 1) % 4], f[i], f[(i + 1) % 4]
                if fa >= 0:
                    pts.append(a)
                if (fa >= 0) != (fb >= 0):
                    pts.append(a + (b - a) * (fa / (fa - fb)))
            return Polygon(*pts, stroke_width=0, fill_color=C2 if side > 0 else HUE, fill_opacity=0.08)

        def boundary():
            o, d = P(P0), np.array([DIR[0], DIR[1], 0.0])
            lo, hi = -1e9, 1e9
            for ax, half in ((0, half_w), (1, half_h)):
                for bound in (BOX_C[ax] - half, BOX_C[ax] + half):
                    t = (bound - o[ax]) / d[ax]
                    if (bound > BOX_C[ax]) == (d[ax] > 0):
                        hi = min(hi, t)
                    else:
                        lo = max(lo, t)
            return DashedLine(o + lo * d, o + hi * d, dash_length=0.12, stroke_width=2.5, color=SOFT)

        def clusters():
            g = VGroup()
            for p in C1_PTS:
                if inside(P(p), 0.09):
                    g.add(Dot(P(p), radius=0.065, color=HUE))
            for p in C2_PTS:
                if inside(P(p), 0.09):
                    g.add(Square(side_length=0.12, stroke_width=0, fill_color=C2, fill_opacity=1).move_to(P(p)))
            return g

        space = always_redraw(lambda: VGroup(region(-1), region(1), boundary(), clusters()))
        c1_t = tex(r"$C_1$", 34, HUE).move_to(P([-3.5, 2.3]))
        c2_t = tex(r"$C_2$", 34, C2).move_to(P([3.55, -2.1]))

        z_dot = always_redraw(lambda: Circle(radius=0.13, stroke_color=INK, stroke_width=3,
                                             fill_color=BLACK, fill_opacity=1).move_to(P(z_local())))
        z_name = always_redraw(lambda: tex(r"$z$", 32, INK).next_to(P(z_local()), LEFT, buff=0.18))

        def perp():
            z = z_local()
            return DashedLine(P(z), P(proj(z)), dash_length=0.08, stroke_width=2.5, color=INK)

        def right_angle():
            z = z_local()
            d = proj(z)
            s = 0.17 / max(k.get_value(), 1e-3)
            u = (z - d) / (np.linalg.norm(z - d) + 1e-9)
            pts = [d + s * u, d + s * u + s * DIR, d + s * DIR]
            return VMobject(stroke_color=INK, stroke_width=2).set_points_as_corners([P(p) for p in pts])

        zdb_dot = always_redraw(lambda: Dot(P(proj(z_local())), radius=0.07, color=INK))
        zdb_name = always_redraw(lambda: tex(r"$z_{db}$", 28, INK).next_to(P(proj(z_local())), RIGHT, buff=0.12))
        perp_m = always_redraw(perp)
        ra_m = always_redraw(right_angle)

        self.add(space)
        cap.show(r"Project a feature $z$ onto the decision boundary: $z_{db}$")
        self.play(FadeIn(space), Create(frame), FadeIn(title), FadeIn(c1_t), FadeIn(c2_t), run_time=1.0)
        self.bring_to_front(cap.current)
        self.play(FadeIn(z_dot), FadeIn(z_name), run_time=0.4)
        self.add(perp_m, ra_m)
        self.play(Create(perp_m), FadeIn(zdb_dot), FadeIn(zdb_name), FadeIn(ra_m), run_time=0.9)
        settle(self, cap)

        # ------------------------------------------------------------ beat 3: the angle
        mu_m = always_redraw(lambda: Square(side_length=0.2, stroke_width=0, fill_color=INK, fill_opacity=1)
                             .rotate(PI / 4).move_to(P(MU)))
        mu_name = always_redraw(lambda: tex(r"$\mu_{ID}$", 30, INK).next_to(P(MU), LEFT, buff=0.15))

        def sides():
            z = z_local()
            d = proj(z)
            return VGroup(Line(P(MU), P(z), stroke_width=3, color=INK),
                          Line(P(MU), P(d), stroke_width=3, color=INK))

        def arc():
            z = z_local()
            d = proj(z)
            u, v = z - MU, d - MU
            a1_, a2_ = np.arctan2(u[1], u[0]), np.arctan2(v[1], v[0])
            da = (a2_ - a1_ + np.pi) % (2 * np.pi) - np.pi
            return Arc(radius=0.62, start_angle=a1_, angle=da, arc_center=P(MU), stroke_width=5, color=HUE)

        def theta_label():
            z = z_local()
            d = proj(z)
            u, v = z - MU, d - MU
            m = u / np.linalg.norm(u) + v / np.linalg.norm(v)
            m = m / (np.linalg.norm(m) + 1e-9)
            r = 1.0 if theta_deg(z) > 28 else 1.45
            return tex(r"$\theta$", 34, HUE).move_to(P(MU) + r * np.array([m[0], m[1], 0]))

        sides_m = always_redraw(sides)
        arc_m = always_redraw(arc)
        th_m = always_redraw(theta_label)

        eq2 = tex(r"$\theta(z) = \arccos \frac{\langle z-\mu_{ID},\; z_{db}-\mu_{ID}\rangle}"
                  r"{\|z-\mu_{ID}\|\,\|z_{db}-\mu_{ID}\|}$", 29, HUE).move_to([EQ_X, 2.05, 0])

        cap.show(r"Seen from the ID mean $\mu_{ID}$, they form an angle $\theta$")
        extra(cap, 1.5)
        self.play(FadeIn(mu_m, scale=0.5), FadeIn(mu_name), run_time=0.5)
        self.add(sides_m, arc_m, th_m)
        self.play(Create(sides_m), Create(arc_m), FadeIn(th_m), run_time=0.9)
        self.play(Write(eq2), run_time=1.0)
        settle(self, cap)

        # ------------------------------------------------------------ beat 4: ID vs OOD
        def verdict(ok_ood, correct):
            word = "OOD" if ok_ood else "ID"
            if correct:
                return tex(word, 27, HUE)
            return tex(word + " (wrong)", 27, WARM)

        def row(label, comp, flagged_ood, correct, y):
            parts = [tex(label, 27, SOFT)]
            if ui["verdicts"]:
                parts += [tex(comp, 27, GREY), tex(r"$\Rightarrow$", 27, GREY), verdict(flagged_ood, correct)]
            g = VGroup(*parts).arrange(RIGHT, buff=0.22)
            return g.move_to([COL_L, y, 0], aligned_edge=LEFT)

        def theta_row():
            th = theta_deg(z_local())
            return row(r"angle $\theta$ = %.1f$^\circ$" % th, r"$%s$ %d$^\circ$" % ("<" if th < THETA_TAU else ">", THETA_TAU),
                       th < THETA_TAU, True, 0.35)

        def dist_row():
            d = dist(z_local())
            flagged = d < DIST_TAU
            return row(r"distance $\|z - z_{db}\|$ = %.2f" % d, r"$%s$ %.2f" % ("<" if flagged else ">", DIST_TAU),
                       flagged, flagged, -0.5)

        th_row = always_redraw(theta_row)
        cap.show(r"Confident features form large angles; features near the boundary, small ones")
        self.play(FadeIn(th_row), run_time=0.4)
        self.wait(0.9)
        self.play(zx.animate.set_value(Z_OOD[0]), zy.animate.set_value(Z_OOD[1]), run_time=2.0, rate_func=smooth)
        settle(self, cap)

        # ------------------------------------------------------------ beat 5: rescaling
        ui["verdicts"] = True
        d_row = always_redraw(dist_row)
        k_line = always_redraw(lambda: tex(r"feature scale $k$ = %.2f" % k.get_value(), 26, GREY)
                               .move_to([COL_L, 1.1, 0], aligned_edge=LEFT))
        cap.show(r"Rescale the features: the distance changes its verdict, the angle does not")
        cap.need(r"distance $<$ 1.30 $\Rightarrow$ OOD", r"$<$ 30 OOD")
        self.play(FadeIn(k_line), FadeIn(d_row), run_time=0.5)
        self.wait(1.3)
        self.play(k.animate.set_value(K_MAX), run_time=2.4, rate_func=smooth)
        settle(self, cap, after=0.9, minimum=1.2)

        everything = [space, frame, title, c1_t, c2_t, z_dot, z_name, perp_m, ra_m, zdb_dot, zdb_name,
                      mu_m, mu_name, sides_m, arc_m, th_m, eq2, th_row, d_row, k_line]
        for m in everything:
            m.clear_updaters()
        self.play(*[FadeOut(m) for m in everything], run_time=0.6)

        # ------------------------------------------------------------ beat 6: ensembles
        names = ["ResNet-50", "ResNet-50 (SCL)", "ViT-B/16"]
        boxes = VGroup()
        for i, n in enumerate(names):
            b = panel(3.3, 0.85, HUE, fill_opacity=0.1).move_to([-3.2, 1.3 - 1.3 * i, 0])
            boxes.add(VGroup(b, tex(n, 26, INK).move_to(b)))
        thetas = VGroup(*[tex(r"$s_%d$" % (i + 1), 34, HUE).move_to([-0.45, 1.3 - 1.3 * i, 0]) for i in range(3)])
        arrows = VGroup(*[Arrow(boxes[i].get_right(), thetas[i].get_left(), buff=0.12, stroke_width=3, color=GREY,
                                max_tip_length_to_length_ratio=0.2) for i in range(3)])
        total = tex(r"$s_1 + s_2 + s_3$", 40, HUE).move_to([2.6, 0.0, 0])
        joins = VGroup(*[Line(thetas[i].get_right() + 0.1 * RIGHT, total.get_left() + 0.1 * LEFT, stroke_width=2,
                              color=DIM) for i in range(3)])
        cap.show(r"Scale-free scores from different models simply add up")
        cap.need(*names)
        self.play(LaggedStart(*[FadeIn(b, shift=0.1 * RIGHT) for b in boxes], lag_ratio=0.2), run_time=0.9)
        self.play(*[GrowArrow(a) for a in arrows], *[FadeIn(t) for t in thetas], run_time=0.6)
        self.play(*[Create(j) for j in joins], Write(total), run_time=0.8)
        settle(self, cap, after=0.8)
        self.play(*[FadeOut(m) for m in [boxes, thetas, arrows, total, joins]], run_time=0.5)

        # ------------------------------------------------------------ beat 7: results
        methods = [("MSP", 54.78), ("Energy", 62.18), ("KNN+", 52.43), ("fDBD", 43.90), ("P-Cos", 41.52),
                   ("ORA", 38.34)]
        sx = 7.0 / 65.0
        x0 = -2.4
        chart = VGroup()
        for i, (m, v) in enumerate(methods):
            y = 1.85 - 0.72 * i
            col = HUE if m == "ORA" else DIM
            bar = Rectangle(width=v * sx, height=0.44, stroke_width=0, fill_color=col, fill_opacity=0.95)
            bar.move_to([x0 + v * sx / 2, y, 0])
            lab = tex(m, 28, INK if m == "ORA" else SOFT).next_to(bar, LEFT, buff=0.25)
            val = tex(f"{v:.2f}", 26, INK if m == "ORA" else SOFT).next_to(bar, RIGHT, buff=0.14)
            chart.add(VGroup(bar, lab, val))
        head = tex("average FPR95 (%), lower is better", 26, GREY).move_to([0.6, 2.8, 0])
        cap.show(r"ORA has the lowest average FPR95 across nine ImageNet backbones")
        cap.need("FPR95, lower is better")
        self.play(FadeIn(head), LaggedStart(*[GrowFromEdge(c[0], LEFT) for c in chart], lag_ratio=0.12),
                  *[FadeIn(c[1]) for c in chart], run_time=1.3)
        self.play(*[FadeIn(c[2]) for c in chart], run_time=0.4)
        settle(self, cap, after=0.4)
        cap.clear()
        self.play(FadeOut(chart), FadeOut(head), run_time=0.5)

        # ------------------------------------------------------------ title card
        card = title_card(
            "ORA",
            "Out-of-Distribution Detection with Relative Angles",
            ["Berker Demirel, Marco Fumero, Francesco Locatello"],
            HUE,
            paper_url="https://openreview.net/forum?id=ul5mlXrLZb",
            code_url="https://github.com/berkerdemirel/ORA-OOD-Detection-with-Relative-Angles",
            venue="NeurIPS 2025",
        )
        self.play(FadeIn(card), run_time=0.9)
        self.wait(2.2)
        cap.report()
