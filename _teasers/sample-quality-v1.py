"""Teaser: Assessing Sample Quality in Conditional Generation under Compositional Shift.

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
    Write,
    rate_functions,
)
from teaser_style import (  # noqa: E402
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


class Teaser(Scene):
    def construct(self):
        cap = Captioner(self)

        # ------------------------------------------------------------------ 1. compositional grid
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

        self.play(FadeIn(head, shift=0.1 * DOWN), run_time=0.7)
        self.play(LaggedStart(*[Create(c) for c in cells], lag_ratio=0.06), FadeIn(xlab), FadeIn(ylab), run_time=1.4)
        self.play(FadeIn(marks), FadeIn(legend), run_time=0.6)
        cap.show(r"A conditional generator can be asked for combinations of attributes it never saw")
        self.wait(0.8)

        # ------------------------------------------------------------------ 2. request an unseen combo
        target = cells[8]  # i=2, j=2
        tpos = target.get_center()
        ring = Square(side_length=cell + 0.08, stroke_color=HUE, stroke_width=4).move_to(tpos)
        gen = panel(2.3, 1.25, HUE, fill_opacity=0.1).move_to([0.2, 0.2, 0])
        gen_lbl = VGroup(tex(r"$G_\theta$", 40, INK), tex("conditional generator", 18, GREY)).arrange(DOWN, buff=0.12).move_to(gen)
        a1 = Arrow(ring.get_right(), gen.get_left() + 0.25 * UP, buff=0.12, color=HUE, stroke_width=3, max_tip_length_to_length_ratio=0.12)
        req = tex(r"request $a^\star$", 22, HUE).next_to(a1, UP, buff=0.05)
        thumbs = VGroup(*[thumb(s, good=s % 3 != 2) for s in range(4)]).arrange(DOWN, buff=0.12).move_to([3.15, 0.2, 0])
        a2 = Arrow(gen.get_right(), thumbs.get_left(), buff=0.12, color=SOFT, stroke_width=3, max_tip_length_to_length_ratio=0.12)
        self.play(Create(ring), run_time=0.5)
        self.play(GrowFromEdge(a1, LEFT), FadeIn(req), FadeIn(gen), FadeIn(gen_lbl), run_time=0.9)
        self.play(GrowFromEdge(a2, LEFT), LaggedStart(*[FadeIn(t, shift=0.1 * RIGHT) for t in thumbs], lag_ratio=0.15), run_time=1.0)

        ref_box = DashedVMobject(RoundedRectangle(width=2.0, height=2.3, corner_radius=0.12, stroke_color=GREY, stroke_width=2), num_dashes=34).move_to([5.6, 0.2, 0])
        ref_lbl = VGroup(tex("real samples", 20, GREY), tex("of the target", 20, GREY)).arrange(DOWN, buff=0.08).move_to(ref_box)
        vs = tex("vs.", 22, GREY).move_to([(thumbs.get_right()[0] + ref_box.get_left()[0]) / 2, 0.2, 0])
        fid = tex("FID / KID", 24, SOFT).next_to(ref_box, UP, buff=0.2)
        self.play(FadeIn(ref_box), FadeIn(ref_lbl), FadeIn(vs), FadeIn(fid), run_time=0.6)
        cross = Cross(ref_box, stroke_color=WARM, stroke_width=5).scale(0.6)
        cap.show(r"Standard metrics compare to real target samples, which do not exist here")
        self.play(Create(cross), run_time=0.5)
        self.wait(1.0)

        stage1 = VGroup(head, grid, xlab, ylab, legend, ring, gen, gen_lbl, a1, req, thumbs, a2, ref_box, ref_lbl, vs, fid, cross)
        self.play(FadeOut(stage1), run_time=0.6)

        # ------------------------------------------------------------------ 3. realism
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
        self.play(FadeIn(r_box), FadeIn(r_title), run_time=0.6)
        self.play(LaggedStart(*[Create(e) for e in ells], lag_ratio=0.2), FadeIn(cloud, lag_ratio=0.02), FadeIn(mu_dot), FadeIn(mu_lbl), run_time=1.2)
        cap.show(r"Realism $R$: Mahalanobis distance to the real training features")
        self.play(FadeIn(star_far, scale=0.5), run_time=0.4)
        self.play(Create(link), Write(eq_r), run_time=1.0)
        self.wait(0.8)

        # ------------------------------------------------------------------ 4. faithfulness
        right_c = np.array([3.55, 0.35, 0])
        f_box = panel(6.2, 4.6, HUE, fill_opacity=0.05).move_to(right_c)
        f_title = VGroup(tex(r"$F$ faithfulness", 30, HUE), tex("closer to the requested value than to the others?", 20, SOFT)).arrange(DOWN, buff=0.1)
        f_title.move_to(f_box.get_top() + 0.62 * DOWN)
        protos = []
        spots = [right_c + np.array([-1.95, -0.55, 0]), right_c + np.array([0.15, 0.55, 0]), right_c + np.array([1.95, -0.65, 0])]
        names = [r"$v_1$", r"$t$ (requested)", r"$v_3$"]
        proto_g = VGroup()
        for k, (pt, nm) in enumerate(zip(spots, names)):
            col = HUE if k == 1 else OBS
            e = Ellipse(width=1.0, height=0.5, stroke_color=col, stroke_width=2, fill_color=col, fill_opacity=0.18).move_to(pt)
            d = Dot(pt, radius=0.05, color=col)
            lbl = tex(nm, 22, col).next_to(e, UP if k == 1 else DOWN, buff=0.12)
            proto_g.add(VGroup(e, d, lbl))
            protos.append(pt)
        star = Star(5, outer_radius=0.2, color=INK, fill_opacity=1, stroke_width=0).move_to(right_c + np.array([0.45, -0.25, 0]))
        lines = VGroup(*[DashedLine(star.get_center(), p, color=(HUE if k == 1 else GREY), stroke_width=2.5 if k == 1 else 1.8, dash_length=0.08)
                         for k, p in enumerate(protos)])
        eq_f = tex(r"$M_k = d_k(y;t) - \min_{v \neq t} d_k(y;v) < 0$", 24, INK).move_to(f_box.get_bottom() + 0.45 * UP)
        self.play(FadeIn(f_box), FadeIn(f_title), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(p, scale=0.8) for p in proto_g], lag_ratio=0.2), run_time=0.9)
        cap.show(r"Faithfulness $F$: attribute by attribute, is it closer to the requested value?")
        self.play(FadeIn(star, scale=0.5), run_time=0.4)
        self.play(LaggedStart(*[Create(l) for l in lines], lag_ratio=0.15), run_time=0.8)
        self.play(Write(eq_f), run_time=0.9)
        self.wait(0.9)

        stage2 = VGroup(r_box, r_title, ells, cloud, mu_dot, mu_lbl, star_far, link, eq_r,
                        f_box, f_title, proto_g, star, lines, eq_f)
        self.play(FadeOut(stage2), run_time=0.6)

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
            verdict = tex("keep" if ok else "reject", 24, HUE if ok else WARM)
            row = VGroup(th, num, verdict).arrange(RIGHT, buff=0.35)
            rows.add(row)
        rows.arrange(DOWN, buff=0.16, aligned_edge=LEFT).move_to([2.6, 0.35, 0])
        thr_y = (rows[2].get_bottom()[1] + rows[3].get_top()[1]) / 2
        thr = DashedLine([rows.get_left()[0] - 0.3, thr_y, 0], [rows.get_right()[0] + 1.6, thr_y, 0], color=WARM, stroke_width=2.5)
        thr_lbl = VGroup(tex("threshold:", 18, WARM), tex("95th percentile", 18, WARM), tex("of real scores", 18, WARM)).arrange(DOWN, buff=0.05, aligned_edge=LEFT)
        thr_lbl.next_to(thr, RIGHT, buff=0.15)
        self.play(FadeIn(t_grp, scale=0.9), run_time=0.7)
        self.play(FadeIn(t_sub), run_time=0.5)
        cap.show(r"$T = R + F$ ranks generated samples: keep, reject, or abstain")
        self.play(LaggedStart(*[FadeIn(r, shift=0.15 * LEFT) for r in rows], lag_ratio=0.15), run_time=1.2)
        self.play(Create(thr), FadeIn(thr_lbl), run_time=0.6)
        self.wait(1.0)
        self.play(FadeOut(VGroup(t_grp, t_sub, rows, thr, thr_lbl)), run_time=0.6)

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
        self.play(Create(axis), FadeIn(ylab), FadeIn(key), FadeIn(chart), run_time=0.6)
        self.play(*[GrowFromEdge(b[0], DOWN) for b in bars_rand], *[FadeIn(b[1]) for b in bars_rand], run_time=0.7)
        self.play(*[GrowFromEdge(b[0], DOWN) for b in bars_trust], *[FadeIn(b[1]) for b in bars_trust], run_time=0.7)
        cap.show(r"Kept samples: 39 to 44% lower $\Delta$KID than random subsets of the same size")
        self.play(LaggedStart(*[FadeIn(p, shift=0.1 * UP) for p in pct], lag_ratio=0.3), run_time=0.7)
        self.wait(1.1)
        self.play(FadeOut(VGroup(axis, ylab, key, chart, bars_rand, bars_trust, pct)), run_time=0.6)

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
        saving = tex(r"CelebA: 33% $\Delta$KID gain while skipping 67% of denoising", 24, INK).move_to([0, 2.5, 0])
        self.play(Create(track), FadeIn(lbl0), FadeIn(lbl1), LaggedStart(*[FadeIn(s) for s in steps], lag_ratio=0.12), run_time=1.2)
        cap.show(r"It also works during generation, abstaining before the image is decoded")
        self.play(Create(tick), FadeIn(tick_lbl), run_time=0.6)
        self.play(FadeIn(saving, shift=0.1 * DOWN), run_time=0.6)
        self.wait(1.3)
        cap.clear()
        self.play(FadeOut(VGroup(steps, track, lbl0, lbl1, tick, tick_lbl, saving)), run_time=0.6)

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
        self.play(FadeIn(card, shift=0.1 * UP), run_time=1.0, rate_func=rate_functions.ease_out_sine)
        self.wait(3.0)
