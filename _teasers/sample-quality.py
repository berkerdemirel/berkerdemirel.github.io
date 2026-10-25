"""Teaser: Assessing Sample Quality in Conditional Generation under Compositional Shift (v2).

v2 redraws the faithfulness beat on a 2D attribute plane (observed 00, 01, 10; requested
11) and keeps every caption in sync with its visual: a caption fades in with the visual it
describes and fades out with it. v1 is kept as sample-quality-v1.py.

Render from the repo root:
    manim -qh --media_dir /tmp/teaser-media _teasers/sample-quality.py Teaser
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from manim import (  # noqa: E402
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Arrow,
    Circle,
    Create,
    Cross,
    DashedLine,
    DashedVMobject,
    Dot,
    Ellipse,
    FadeIn,
    FadeOut,
    GrowFromEdge,
    LaggedStart,
    Line,
    Rectangle,
    RoundedRectangle,
    Scene,
    Square,
    Star,
    VGroup,
    VMobject,
    Write,
    rate_functions,
)
from teaser_style import (  # noqa: E402
    CAPTION_Y,
    DIM,
    GOLD,
    GREY,
    HUES,
    INK,
    SOFT,
    WARM,
    Captioner,
    panel,
    tex,
    title_card,
)

HUE = HUES["sample-quality"]
R_COL = GOLD
OBS = "#7FC9A6"  # observed conditions (green, as in the paper's Figure 1)


def thumb(seed, good=True, size=0.62):
    """Abstract generated 'image': dark tile with a few glowing blobs; malformed ones are smeared."""
    rng = np.random.default_rng(seed)
    tile = RoundedRectangle(width=size, height=size, corner_radius=0.06, stroke_color=DIM,
                            stroke_width=1.5, fill_color="#06080C", fill_opacity=1)
    blobs = VGroup()
    for _ in range(3):
        c = tile.get_center() + np.array([*(rng.uniform(-0.28, 0.28, 2) * size), 0])
        if good:
            halo = Circle(radius=0.11 * size, stroke_width=0, fill_color=HUE, fill_opacity=0.28).move_to(c)
            core = Circle(radius=0.045 * size, stroke_width=0, fill_color=INK, fill_opacity=0.9).move_to(c)
        else:
            halo = Ellipse(width=0.42 * size, height=0.09 * size, stroke_width=0, fill_color=WARM,
                           fill_opacity=0.3).rotate(rng.uniform(0, 3.14)).move_to(c)
            core = Ellipse(width=0.16 * size, height=0.04 * size, stroke_width=0, fill_color=GOLD,
                           fill_opacity=0.7).rotate(rng.uniform(0, 3.14)).move_to(c)
        blobs.add(VGroup(halo, core))
    return VGroup(tile, blobs)


def check_mark(color, size=0.26):
    m = VMobject(stroke_color=color, stroke_width=5)
    m.set_points_as_corners([np.array([-0.5, 0.0, 0]) * size, np.array([-0.15, -0.38, 0]) * size,
                             np.array([0.55, 0.45, 0]) * size])
    return m


def x_mark(color, size=0.24):
    a = Line(np.array([-0.5, -0.5, 0]) * size, np.array([0.5, 0.5, 0]) * size, color=color, stroke_width=5)
    b = Line(np.array([-0.5, 0.5, 0]) * size, np.array([0.5, -0.5, 0]) * size, color=color, stroke_width=5)
    return VGroup(a, b)


def cap_swap(scene, cap, text, in_anims=(), out_anims=(), run_out=0.4, run_in=0.5):
    """Fade the current caption out together with `out_anims`, then fade `text` in together
    with `in_anims`, so a caption never outlives or precedes its visual."""
    outs = list(out_anims)
    if cap.current is not None:
        outs.append(FadeOut(cap.current))
    if outs:
        scene.play(*outs, run_time=run_out)
    cap.current = None
    new = tex(text, cap.size, cap.color).move_to([0, CAPTION_Y, 0])
    cap.log.append([text, cap._now(), 0.0])
    scene.play(FadeIn(new, shift=0.08 * UP), *in_anims, run_time=run_in)
    cap.current = new
    return new


def cap_end(scene, cap, out_anims=(), run_out=0.4):
    """Fade the last caption out together with its visual."""
    outs = list(out_anims)
    if cap.current is not None:
        outs.append(FadeOut(cap.current))
    scene.play(*outs, run_time=run_out)
    cap.current = None
    cap.log.append([None, cap._now(), 0.0])


class Teaser(Scene):
    def construct(self):
        cap = Captioner(self)

        # ------------------------------------------------------------------ 1. compositional grid + request
        head = tex(r"Can we trust samples for conditions nobody has observed?", 34, INK).move_to([0, 3.3, 0])
        cell = 0.9
        origin = np.array([-4.6, -1.35, 0])
        cells, marks = VGroup(), VGroup()
        for i in range(3):
            for j in range(3):
                pos = origin + np.array([i * (cell + 0.18), j * (cell + 0.18), 0])
                seen = i == 0 or j == 0
                sq = Square(side_length=cell, stroke_width=2, stroke_color=OBS if seen else GREY).move_to(pos)
                if seen:
                    sq.set_fill(OBS, opacity=0.16)
                    dots = VGroup(*[Dot(pos + np.array([dx, dy, 0]), radius=0.05, color=OBS)
                                    for dx, dy in ((-0.2, 0.15), (0.18, 0.2), (0.0, -0.18))])
                    marks.add(dots)
                    cells.add(sq)
                else:
                    sq = DashedVMobject(sq, num_dashes=22)
                    q = tex("?", 30, GREY).move_to(pos)
                    marks.add(q)
                    cells.add(sq)
        grid = VGroup(cells, marks)
        xlab = tex("attribute 1", 22, GREY).next_to(cells, DOWN, buff=0.25)
        ylab = tex("attribute 2", 22, GREY).rotate(np.pi / 2).next_to(cells, LEFT, buff=0.25)
        legend = VGroup(
            VGroup(Square(0.22, stroke_color=OBS, fill_color=OBS, fill_opacity=0.3, stroke_width=2),
                   tex("observed in training", 20, SOFT)).arrange(RIGHT, buff=0.15),
            VGroup(DashedVMobject(Square(0.22, stroke_color=GREY, stroke_width=2), num_dashes=8),
                   tex("never observed", 20, SOFT)).arrange(RIGHT, buff=0.15),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).next_to(cells, UP, buff=0.3).align_to(cells, LEFT)

        target = cells[8]  # i=2, j=2
        tpos = target.get_center()
        ring = Square(side_length=cell + 0.08, stroke_color=HUE, stroke_width=4).move_to(tpos)
        gen = panel(2.3, 1.25, HUE, fill_opacity=0.1).move_to([0.2, 0.2, 0])
        gen_lbl = VGroup(tex(r"$G_\theta$", 40, INK), tex("conditional generator", 18, GREY)).arrange(DOWN, buff=0.12).move_to(gen)
        a1 = Arrow(ring.get_right(), gen.get_left() + 0.25 * UP, buff=0.12, color=HUE, stroke_width=3, max_tip_length_to_length_ratio=0.12)
        req = tex(r"request $a^\star$", 22, HUE).next_to(a1, UP, buff=0.05)
        thumbs = VGroup(*[thumb(s, good=s % 3 != 2) for s in range(4)]).arrange(DOWN, buff=0.12).move_to([3.15, 0.2, 0])
        a2 = Arrow(gen.get_right(), thumbs.get_left(), buff=0.12, color=SOFT, stroke_width=3, max_tip_length_to_length_ratio=0.12)

        cap_swap(self, cap, r"A generator can be asked for combinations it never saw",
                 in_anims=[FadeIn(head, shift=0.1 * DOWN),
                           LaggedStart(*[Create(c) for c in cells], lag_ratio=0.06), FadeIn(xlab), FadeIn(ylab)],
                 run_in=0.9)
        self.play(FadeIn(marks), FadeIn(legend), Create(ring), run_time=0.4)
        self.play(GrowFromEdge(a1, LEFT), FadeIn(req), FadeIn(gen), FadeIn(gen_lbl), run_time=0.6)
        self.play(GrowFromEdge(a2, LEFT), LaggedStart(*[FadeIn(t, shift=0.1 * RIGHT) for t in thumbs], lag_ratio=0.15), run_time=0.7)
        cap.need(r"Can we trust samples for conditions nobody has observed?")
        self.wait(2.3)

        # ------------------------------------------------------------------ 2. no target to compare against
        ref_box = DashedVMobject(RoundedRectangle(width=2.0, height=2.3, corner_radius=0.12, stroke_color=GREY, stroke_width=2), num_dashes=34).move_to([5.6, 0.2, 0])
        ref_lbl = VGroup(tex("real samples", 20, GREY), tex("of the target", 20, GREY)).arrange(DOWN, buff=0.08).move_to(ref_box)
        vs = tex("vs.", 22, GREY).move_to([(thumbs.get_right()[0] + ref_box.get_left()[0]) / 2, 0.2, 0])
        fid = tex("FID / KID", 24, SOFT).next_to(ref_box, UP, buff=0.2)
        cross = Cross(ref_box, stroke_color=WARM, stroke_width=5).scale(0.6)
        cap_swap(self, cap, r"But FID and KID need real target samples, which do not exist",
                 in_anims=[FadeIn(ref_box), FadeIn(ref_lbl), FadeIn(vs), FadeIn(fid)], run_out=0.3)
        self.play(Create(cross), run_time=0.4)
        self.wait(3.6)
        stage1 = VGroup(head, grid, xlab, ylab, legend, ring, gen, gen_lbl, a1, req, thumbs, a2, ref_box, ref_lbl, vs, fid, cross)

        # ------------------------------------------------------------------ 3. realism (as in v1)
        rng = np.random.default_rng(3)
        left_c = np.array([-3.55, 0.35, 0])
        r_box = panel(6.2, 4.6, R_COL, fill_opacity=0.05).move_to(left_c)
        r_title = VGroup(tex(r"$R$ realism", 30, R_COL), tex("close to the real-data features?", 20, SOFT)).arrange(DOWN, buff=0.1)
        r_title.move_to(r_box.get_top() + 0.62 * DOWN)
        mu = left_c + np.array([-0.6, -0.45, 0])
        ells = VGroup(*[Ellipse(width=w, height=w * 0.58, stroke_color=R_COL, stroke_width=2).rotate(0.25).move_to(mu)
                        for w in (1.0, 1.9, 2.8)])
        ells = VGroup(*[DashedVMobject(e, num_dashes=int(18 + 10 * k)) for k, e in enumerate(ells)])
        cloud = VGroup()
        for _ in range(60):
            v = rng.normal(size=2) * np.array([0.55, 0.3])
            c, s = np.cos(0.25), np.sin(0.25)
            p = mu + np.array([c * v[0] - s * v[1], s * v[0] + c * v[1], 0])
            cloud.add(Dot(p, radius=0.035, color=GREY))
        mu_dot = Dot(mu, radius=0.07, color=R_COL)
        mu_txt = tex(r"$\mu_{\mathrm{real}}$", 24, R_COL).move_to(mu + np.array([-1.05, -1.25, 0]))
        mu_lbl = VGroup(Line(mu_txt.get_corner(UP + RIGHT) + 0.05 * UP, mu + np.array([-0.06, -0.06, 0]), color=R_COL, stroke_width=1.5), mu_txt)
        star_far = Star(5, outer_radius=0.2, color=HUE, fill_opacity=1, stroke_width=0).move_to(left_c + np.array([2.15, 0.25, 0]))
        link = DashedLine(star_far.get_center(), mu, color=HUE, stroke_width=2.5, dash_length=0.08)
        eq_r = tex(r"$E(y) = (y-\mu)^\top \Sigma^{-1} (y-\mu)$", 24, INK).move_to(r_box.get_bottom() + 0.45 * UP)

        cap_swap(self, cap, r"Realism $R$: Mahalanobis distance to the real training features",
                 in_anims=[FadeIn(r_box), FadeIn(r_title)], out_anims=[FadeOut(stage1)])
        self.play(LaggedStart(*[Create(e) for e in ells], lag_ratio=0.2), FadeIn(cloud, lag_ratio=0.02), FadeIn(mu_dot), FadeIn(mu_lbl), run_time=0.9)
        self.play(FadeIn(star_far, scale=0.5), run_time=0.3)
        self.play(Create(link), Write(eq_r), run_time=0.8)
        cap.need(r"$E(y)$")
        self.wait(2.1)

        # ------------------------------------------------------------------ 4. faithfulness on the attribute plane
        r_stage = VGroup(r_box, r_title, ells, cloud, mu_dot, mu_lbl, star_far, link, eq_r)
        fc = np.array([2.45, 0.3, 0])
        f_box = panel(8.7, 4.9, HUE, fill_opacity=0.05).move_to(fc)
        f_title = VGroup(tex(r"$F$ faithfulness", 30, HUE),
                         tex("for each attribute: closer to the requested value than to the other?", 20, SOFT)).arrange(DOWN, buff=0.1)
        f_title.move_to(f_box.get_top() + 0.58 * DOWN)

        # Plane: attribute 1 on x, attribute 2 on y, values 0 and 1.
        X = {0: -0.5, 1: 1.8}
        Y = {0: -1.35, 1: 0.75}
        P = lambda a, b: np.array([X[a], Y[b], 0])  # noqa: E731
        y_top, y_bot = 1.32, -1.78
        x_left, x_right = -0.98, 2.4
        guides = VGroup(
            *[DashedLine([X[v], y_bot, 0], [X[v], y_top, 0], color=DIM, stroke_width=1.6, dash_length=0.07) for v in (0, 1)],
            *[DashedLine([x_left, Y[v], 0], [x_right, Y[v], 0], color=DIM, stroke_width=1.6, dash_length=0.07) for v in (0, 1)],
        )
        glabels = VGroup(
            tex(r"$a_1 = 0$", 20, GREY).move_to([X[0], y_bot - 0.24, 0]),
            tex(r"$a_1 = 1$", 20, GREY).move_to([X[1], y_bot - 0.24, 0]),
            tex(r"$a_2 = 0$", 20, GREY).next_to([x_left, Y[0], 0], LEFT, buff=0.1),
            tex(r"$a_2 = 1$", 20, GREY).next_to([x_left, Y[1], 0], LEFT, buff=0.1),
        )
        clusters = VGroup()
        crng = np.random.default_rng(11)
        for a, b in ((0, 0), (0, 1), (1, 0)):
            pts = VGroup(*[Dot(P(a, b) + np.array([*crng.normal(0, 0.15, 2), 0]), radius=0.04, color=OBS) for _ in range(14)])
            clusters.add(pts)
        cl_lbls = VGroup(*[tex(t, 20, OBS).next_to(P(a, b), DOWN + RIGHT, buff=0.18) for t, (a, b) in
                           (("00", (0, 0)), ("01", (0, 1)), ("10", (1, 0)))])
        req_cell = DashedVMobject(Square(0.86, stroke_color=HUE, stroke_width=2.5).move_to(P(1, 1)), num_dashes=20)
        req_lbl = tex("11 requested, never observed", 20, HUE).next_to(req_cell, UP, buff=0.1)

        # Readout column: one row per attribute.
        rx = 4.85
        eq_f = tex(r"$M_k = d_k(y;t) - \min_{v \neq t} d_k(y;v)$", 22, INK).move_to([rx, 1.05, 0])
        eq_sub = tex(r"$M_k < 0$: closer to the requested value", 19, SOFT).next_to(eq_f, DOWN, buff=0.14)
        row_h = [tex("attribute 1 (requested 1)", 20, SOFT).move_to([rx, 0.05, 0]),
                 tex("attribute 2 (requested 1)", 20, SOFT).move_to([rx, -1.0, 0])]

        def verdict(text, ok, row):
            col = HUE if ok else WARM
            t = tex(text, 22, col)
            mark = check_mark(col) if ok else x_mark(col)
            g = VGroup(t, mark).arrange(RIGHT, buff=0.18)
            return g.next_to(row_h[row], DOWN, buff=0.14)

        def checks(s_pos, ok2):
            """Distance segments from the sample to each attribute's two values."""
            seg1 = VGroup(
                Line(s_pos, [X[1], s_pos[1], 0], color=HUE, stroke_width=5),
                DashedLine(s_pos, [X[0], s_pos[1], 0], color=GREY, stroke_width=2.5, dash_length=0.08),
            )
            near2 = 1 if ok2 else 0
            seg2 = VGroup(
                Line(s_pos, [s_pos[0], Y[near2], 0], color=HUE if ok2 else WARM, stroke_width=5),
                DashedLine(s_pos, [s_pos[0], Y[1 - near2], 0], color=GREY, stroke_width=2.5, dash_length=0.08),
            )
            return seg1, seg2

        cap_swap(self, cap, r"Faithfulness $F$: per attribute, closer to the requested value?",
                 in_anims=[FadeIn(f_box), FadeIn(f_title)],
                 out_anims=[r_stage.animate.scale(0.66).move_to([-4.85, 0.3, 0])], run_out=0.5)
        self.play(Create(guides), FadeIn(glabels), LaggedStart(*[FadeIn(c) for c in clusters], lag_ratio=0.2),
                  FadeIn(cl_lbls), Create(req_cell), FadeIn(req_lbl), run_time=0.6)
        self.play(Write(eq_f), FadeIn(eq_sub), run_time=0.5)
        cap.need("11 requested, never observed", r"$M_k < 0$: closer to the requested value")

        # A faithful sample near 11: both attributes closer to the requested value.
        s_good = P(1, 1) + np.array([-0.5, -0.42, 0])
        star = Star(5, outer_radius=0.17, color=INK, fill_opacity=1, stroke_width=0).move_to(s_good)
        seg1, seg2 = checks(s_good, ok2=True)
        v1 = verdict(r"closer to $a_1 = 1$", True, 0)
        v2 = verdict(r"closer to $a_2 = 1$", True, 1)
        self.play(FadeIn(star, scale=0.5), FadeIn(row_h[0]), FadeIn(row_h[1]), run_time=0.4)
        self.play(Create(seg1), run_time=0.45)
        self.play(FadeIn(v1, shift=0.05 * RIGHT), run_time=0.3)
        self.play(Create(seg2), run_time=0.45)
        self.play(FadeIn(v2, shift=0.05 * RIGHT), run_time=0.3)
        self.add_foreground_mobject(star)
        cap.need("closer to a1 = 1", "closer to a2 = 1")
        self.wait(2.4)

        # A sample whose second attribute leaked toward the observed 10 combination.
        s_bad = P(1, 0) + np.array([-0.42, 0.5, 0])
        seg1b, seg2b = checks(s_bad, ok2=False)
        v2b = verdict(r"closer to $a_2 = 0$", False, 1)
        leak_lbl = tex("leaked toward the observed 10", 18, WARM).next_to(v2b, DOWN, buff=0.1)
        self.play(FadeOut(seg1), FadeOut(seg2), FadeOut(v2), star.animate.move_to(s_bad), run_time=0.5)
        self.play(Create(seg1b), Create(seg2b), run_time=0.5)
        self.play(FadeIn(v2b, shift=0.05 * RIGHT), FadeIn(leak_lbl), run_time=0.35)
        cap.need("closer to a2 = 0", "leaked toward the observed 10")
        self.wait(2.8)
        self.remove_foreground_mobject(star)

        stage2 = VGroup(r_stage, f_box, f_title, guides, glabels, clusters, cl_lbls, req_cell, req_lbl,
                        eq_f, eq_sub, row_h[0], row_h[1], v1, v2b, seg1b, seg2b, star, leak_lbl)

        # ------------------------------------------------------------------ 5. T = R + F ranking
        t_eq = tex(r"$T = R + F$", 44, INK)
        t_eq[2:3].set_fill(R_COL)  # R
        t_eq[4:5].set_fill(HUE)    # F
        t_box = RoundedRectangle(width=t_eq.width + 0.6, height=t_eq.height + 0.4, corner_radius=0.12,
                                 stroke_color=SOFT, stroke_width=1.5).move_to(t_eq)
        t_grp = VGroup(t_box, t_eq).move_to([-3.6, 0.9, 0])
        t_sub = VGroup(tex("computed from training data only", 22, SOFT),
                       tex("low = trusted", 22, GREY)).arrange(DOWN, buff=0.12).next_to(t_grp, DOWN, buff=0.35)

        rows = VGroup()
        scores = [("0.08", True), ("0.29", True), ("0.62", True), ("1.79", False), ("2.93", False)]
        for k, (sc, ok) in enumerate(scores):
            th = thumb(10 + k, good=ok, size=0.55)
            num = tex(sc, 26, INK)
            mark = check_mark(HUE) if ok else x_mark(WARM)
            row = VGroup(th, num, mark).arrange(RIGHT, buff=0.35)
            rows.add(row)
        rows.arrange(DOWN, buff=0.16, aligned_edge=LEFT).move_to([2.6, 0.35, 0])
        thr_y = (rows[2].get_bottom()[1] + rows[3].get_top()[1]) / 2
        thr = DashedLine([rows.get_left()[0] - 0.3, thr_y, 0], [rows.get_right()[0] + 1.6, thr_y, 0], color=WARM, stroke_width=2.5)
        thr_lbl = VGroup(tex("threshold:", 18, WARM), tex("95th percentile", 18, WARM), tex("of real scores", 18, WARM)).arrange(DOWN, buff=0.05, aligned_edge=LEFT)
        thr_lbl.next_to(thr, RIGHT, buff=0.15)

        cap_swap(self, cap, r"$T = R + F$ ranks generated samples: keep, reject, or abstain",
                 in_anims=[FadeIn(t_grp, scale=0.9), FadeIn(t_sub)], out_anims=[FadeOut(stage2)])
        self.play(LaggedStart(*[FadeIn(r, shift=0.15 * LEFT) for r in rows], lag_ratio=0.15), run_time=0.8)
        self.play(Create(thr), FadeIn(thr_lbl), run_time=0.4)
        cap.need("threshold: 95th percentile of real scores")
        self.wait(3.2)
        rank_stage = VGroup(t_grp, t_sub, rows, thr, thr_lbl)

        # ------------------------------------------------------------------ 6. headline result
        base_y = -1.9
        scale_h = 7.0  # scene units per unit of Delta KID
        chart = VGroup()
        groups = [("CelebA", 0.368, 0.224, "+39.1%"), ("RxRx1", 0.323, 0.196, "+39.4%")]
        bars_rand, bars_trust, pct = VGroup(), VGroup(), VGroup()
        for g, (name, rnd, tru, gain) in enumerate(groups):
            x0 = -2.2 + g * 4.2
            br = Rectangle(width=0.9, height=rnd * scale_h, stroke_width=0, fill_color=GREY, fill_opacity=0.75)
            br.move_to([x0 - 0.55, base_y + rnd * scale_h / 2, 0])
            bt = Rectangle(width=0.9, height=tru * scale_h, stroke_width=0, fill_color=HUE, fill_opacity=0.95)
            bt.move_to([x0 + 0.55, base_y + tru * scale_h / 2, 0])
            vr = tex(f"{rnd:.3f}", 20, SOFT).next_to(br, UP, buff=0.1)
            vt = tex(f"{tru:.3f}", 20, SOFT).next_to(bt, UP, buff=0.1)
            nm = tex(name + " (vanilla SiT)", 22, SOFT).move_to([x0, base_y - 0.35, 0])
            gp = tex(gain, 26, HUE).move_to([x0 + 0.55, base_y + tru * scale_h + 0.62, 0])
            bars_rand.add(VGroup(br, vr))
            bars_trust.add(VGroup(bt, vt))
            pct.add(gp)
            chart.add(nm)
        axis = Line([-4.0, base_y, 0], [4.2, base_y, 0], color=DIM, stroke_width=2)
        ylab = tex(r"$\Delta$KID (lower is better)", 22, GREY).move_to([0, 2.55, 0])
        key = VGroup(
            VGroup(Square(0.2, stroke_width=0, fill_color=GREY, fill_opacity=0.75), tex("random subset", 20, SOFT)).arrange(RIGHT, buff=0.12),
            VGroup(Square(0.2, stroke_width=0, fill_color=HUE, fill_opacity=0.95), tex("trust-selected, same size", 20, SOFT)).arrange(RIGHT, buff=0.12),
        ).arrange(RIGHT, buff=0.6).move_to([0, 2.05, 0])

        cap_swap(self, cap, r"Kept samples: 39 to 44% lower $\Delta$KID than random subsets",
                 in_anims=[Create(axis), FadeIn(ylab), FadeIn(key), FadeIn(chart)], out_anims=[FadeOut(rank_stage)])
        self.play(*[GrowFromEdge(b[0], DOWN) for b in bars_rand], *[FadeIn(b[1]) for b in bars_rand], run_time=0.5)
        self.play(*[GrowFromEdge(b[0], DOWN) for b in bars_trust], *[FadeIn(b[1]) for b in bars_trust], run_time=0.5)
        self.play(LaggedStart(*[FadeIn(p, shift=0.1 * UP) for p in pct], lag_ratio=0.3), run_time=0.4)
        cap.need("trust-selected, same size")
        self.wait(3.4)
        res_stage = VGroup(axis, ylab, key, chart, bars_rand, bars_trust, pct)

        # ------------------------------------------------------------------ 7. during generation
        steps = VGroup()
        xs = np.linspace(-4.8, 4.8, 6)
        for k, x in enumerate(xs):
            tile = RoundedRectangle(width=1.1, height=1.1, corner_radius=0.08, stroke_color=DIM, stroke_width=1.5,
                                    fill_color="#06080C", fill_opacity=1).move_to([x, 0.6, 0])
            noise = VGroup(*[Dot(tile.get_center() + np.array([*rng.uniform(-0.45, 0.45, 2), 0]), radius=0.025,
                                 color=GREY).set_opacity(0.9 - 0.15 * k) for _ in range(40)])
            clean = thumb(30, good=True, size=1.1).move_to(tile)
            clean.set_opacity(min(1, 0.18 * k))
            steps.add(VGroup(tile, noise, clean[1]))
        track = Line([-5.4, -0.45, 0], [5.4, -0.45, 0], color=DIM, stroke_width=3)
        lbl0 = tex("noise", 20, GREY).next_to(track.get_start(), DOWN, buff=0.15)
        lbl1 = tex("decoded image", 20, GREY).next_to(track.get_end(), DOWN, buff=0.15)
        k83 = -5.4 + 10.8 * 83 / 250
        tick = Line([k83, -0.65, 0], [k83, -0.25, 0], color=HUE, stroke_width=4)
        tick_lbl = VGroup(tex(r"score $T$ here", 22, HUE), tex("step 83 of 250", 18, SOFT)).arrange(DOWN, buff=0.08).next_to(tick, DOWN, buff=0.15)

        cap_swap(self, cap, r"It also works mid-generation, abstaining before the image is decoded",
                 in_anims=[Create(track), FadeIn(lbl0), FadeIn(lbl1),
                           LaggedStart(*[FadeIn(s) for s in steps], lag_ratio=0.12)],
                 out_anims=[FadeOut(res_stage)], run_in=0.8)
        self.play(Create(tick), FadeIn(tick_lbl), run_time=0.4)
        cap.need(r"score $T$ here, step 83 of 250")
        self.wait(3.8)
        gen_stage = VGroup(steps, track, lbl0, lbl1, tick, tick_lbl)
        cap_end(self, cap, out_anims=[FadeOut(gen_stage)])

        # ------------------------------------------------------------------ title card
        card = title_card(
            "Assessing Sample Quality",
            "in Conditional Generation under Compositional Shift",
            ["Berker Demirel, Valentino Maiorca, Marco Fumero, Theofanis Karaletsos, Francesco Locatello"],
            HUE,
            paper_url="https://arxiv.org/abs/2606.09601",
            code_url="https://github.com/berkerdemirel/faithful-cond-gen",
            venue="NeurIPS 2026",
        )
        self.play(FadeIn(card, shift=0.1 * UP), run_time=0.6, rate_func=rate_functions.ease_out_sine)
        self.wait(2.0)
        cap.report()
