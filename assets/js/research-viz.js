// Interactive sketches for the Research page (and reused inside posts).
// Each figure is a small 2D toy that follows the definitions in the papers;
// none of them reproduces experimental results.
(() => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  // ---- Shared helpers -------------------------------------------------------
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const palette = () => ({
    ink: css('--ink'),
    soft: css('--ink-soft'),
    faint: css('--ink-faint'),
    hair: css('--hairline'),
    hairStrong: css('--hairline-strong'),
    accent: css('--accent'),
    warm: css('--warm'),
    card: css('--card'),
    grid: css('--plot-grid'),
    axis: css('--plot-axis'),
    s1: css('--series-1'),
    s2: css('--series-2'),
    s3: css('--series-3'),
    sans: css('--sans'),
    mono: css('--mono'),
  });

  const mulberry32 = (seed) => () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  const gaussian = (rand) => {
    let u = 0, v = 0;
    while (u === 0) u = rand();
    while (v === 0) v = rand();
    return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  };
  const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

  // Keeps a canvas's backing store matched to its CSS size and device pixel ratio.
  function surface(canvas, draw) {
    const ctx = canvas.getContext('2d');
    const state = { ctx, w: 0, h: 0 };
    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = canvas.clientWidth, h = canvas.clientHeight;
      if (!w || !h) return;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      state.w = w; state.h = h;
      draw();
    };
    // The observer fires once on observe(), after the caller has stored the returned state.
    new ResizeObserver(resize).observe(canvas);
    return state;
  }

  function withAlpha(color, a) {
    // Accepts #rgb/#rrggbb; returns rgba().
    let c = color.replace('#', '');
    if (c.length === 3) c = c.split('').map((x) => x + x).join('');
    const n = parseInt(c, 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
  }

  function onTheme(fn) { document.addEventListener('themechange', fn); }

  function segmented(group, onChange) {
    const buttons = [...group.querySelectorAll('button')];
    buttons.forEach((b) => b.addEventListener('click', () => {
      buttons.forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      onChange(b.dataset.value);
    }));
  }

  const PLAY_ICON = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M3 1.5v9l7.5-4.5z" fill="currentColor"/></svg>';
  const PAUSE_ICON = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 1.5h2.5v9H2.5zM7 1.5h2.5v9H7z" fill="currentColor"/></svg>';

  // ==========================================================================
  // 1. Dimensional collapse in the backbone (lambda-JEPA)
  // ==========================================================================
  function collapseViz(root) {
    const K = 16, N_IMG = 30, N_VIEW = 4;
    const rand = mulberry32(7);
    const centers = Array.from({ length: N_IMG }, () => Array.from({ length: K }, () => gaussian(rand)));
    const views = centers.map((c) =>
      Array.from({ length: N_VIEW }, () => c.map((x) => x + 0.3 * gaussian(rand))));

    const scatter = root.querySelector('[data-role="scatter"]');
    const spectrum = root.querySelector('[data-role="spectrum"]');
    const slider = root.querySelector('input[type="range"]');
    const out = root.querySelector('output');
    const play = root.querySelector('[data-role="play"]');
    const read = {
      h: root.querySelector('[data-read="rank-h"]'),
      z: root.querySelector('[data-read="rank-z"]'),
      reg: root.querySelector('[data-read="sacreg"]'),
    };

    let t = Number(slider.value) / 100;
    let mode = 'baseline';
    let colors = palette();
    let anim = null;

    // Spectra: singular values of the backbone h and projector z as training proceeds.
    const specH = () => Array.from({ length: K }, (_, k) =>
      mode === 'baseline' ? Math.exp(-t * 1.4 * k) : Math.exp(-t * 0.05 * k));
    const specZ = () => Array.from({ length: K }, (_, k) => Math.exp(-t * 0.045 * k));
    const effRank = (s) => {
      const sum = s.reduce((a, b) => a + b, 0);
      let H = 0;
      for (const x of s) { const p = x / sum; if (p > 0) H -= p * Math.log(p); }
      return Math.exp(H);
    };
    // SACReg on view centers with mean ~0 and covariance diag(s^2): 0.5 * sum(s^2 - log s^2 - 1)
    const sacreg = (s) => 0.5 * s.reduce((a, x) => a + x * x - Math.log(x * x + 1e-4) - 1, 0);

    const ROT = -0.5;
    const project = (v, s) => {
      const x = v[0] * s[0], y = v[1] * s[1];
      return [x * Math.cos(ROT) - y * Math.sin(ROT), x * Math.sin(ROT) + y * Math.cos(ROT)];
    };

    const sc = surface(scatter, drawScatter);
    const sp = surface(spectrum, drawSpectrum);

    function drawScatter() {
      const { ctx, w, h } = sc;
      if (!w) return;
      ctx.clearRect(0, 0, w, h);
      const s = specH();
      const cx = w / 2, cy = h / 2;
      const R = Math.min(w, h) * 0.42;
      const scale = R / 2.6;

      // reference circle and axes
      ctx.strokeStyle = colors.axis;
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.stroke();
      ctx.strokeStyle = colors.grid;
      ctx.beginPath(); ctx.moveTo(cx - R, cy); ctx.lineTo(cx + R, cy); ctx.moveTo(cx, cy - R); ctx.lineTo(cx, cy + R); ctx.stroke();

      const hue = mode === 'baseline' && t > 0.35 ? colors.warm : colors.accent;
      // views (hollow) then centers (filled)
      ctx.lineWidth = 1.2;
      ctx.strokeStyle = withAlpha(hue, 0.55);
      for (const vs of views) for (const v of vs) {
        const [x, y] = project(v, s);
        ctx.beginPath(); ctx.arc(cx + x * scale, cy - y * scale, 2.6, 0, Math.PI * 2); ctx.stroke();
      }
      for (const c of centers) {
        const [x, y] = project(c, s);
        ctx.beginPath(); ctx.arc(cx + x * scale, cy - y * scale, 4, 0, Math.PI * 2);
        ctx.fillStyle = hue; ctx.fill();
        ctx.strokeStyle = colors.card; ctx.lineWidth = 1.5; ctx.stroke();
      }

      ctx.fillStyle = colors.faint;
      ctx.font = `500 11px ${colors.sans}`;
      ctx.textAlign = 'left';
      ctx.fillText('backbone h (top-2 directions)', 8, 16);
      if (mode === 'baseline' && t > 0.6) {
        ctx.fillStyle = colors.warm;
        ctx.textAlign = 'center';
        ctx.fillText('dimensional collapse', cx, h - 10);
      }
    }

    function drawSpectrum() {
      const { ctx, w, h } = sp;
      if (!w) return;
      ctx.clearRect(0, 0, w, h);
      const sH = specH(), sZ = specZ();
      const padL = 30, padR = 10, padT = 24, padB = 30;
      const pw = w - padL - padR, ph = h - padT - padB;
      const y0 = padT + ph;

      // gridlines
      ctx.font = `400 10px ${colors.mono}`;
      ctx.textAlign = 'right';
      ctx.fillStyle = colors.faint;
      for (const g of [0, 0.5, 1]) {
        const y = y0 - g * ph;
        ctx.strokeStyle = g === 0 ? colors.axis : colors.grid;
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(w - padR, y); ctx.stroke();
        ctx.fillText(g.toFixed(1), padL - 6, y + 3);
      }

      const slot = pw / K;
      const bw = Math.max(2, slot * 0.34);
      for (let k = 0; k < K; k++) {
        const x = padL + k * slot + slot / 2;
        // projector z: outlined bar
        const hz = sZ[k] * ph;
        ctx.strokeStyle = colors.s2;
        ctx.lineWidth = 1.5;
        roundBar(ctx, x + 1, y0, bw, hz, false);
        // backbone h: filled bar
        const hh = Math.max(1, sH[k] * ph);
        ctx.fillStyle = colors.s1;
        roundBar(ctx, x - bw - 1, y0, bw, hh, true);
      }
      ctx.fillStyle = colors.faint;
      ctx.textAlign = 'center';
      ctx.font = `500 11px ${colors.sans}`;
      ctx.fillText('direction k (sorted)', padL + pw / 2, h - 8);
      ctx.textAlign = 'left';
      ctx.fillText('singular value', 8, 14);
    }

    function roundBar(ctx, x, y0, bw, hgt, fill) {
      const r = Math.min(3, bw / 2, hgt);
      ctx.beginPath();
      ctx.moveTo(x, y0);
      ctx.lineTo(x, y0 - hgt + r);
      ctx.quadraticCurveTo(x, y0 - hgt, x + r, y0 - hgt);
      ctx.lineTo(x + bw - r, y0 - hgt);
      ctx.quadraticCurveTo(x + bw, y0 - hgt, x + bw, y0 - hgt + r);
      ctx.lineTo(x + bw, y0);
      if (fill) ctx.fill(); else ctx.stroke();
    }

    function update() {
      out.textContent = `${Math.round(t * 100)}%`;
      const sH = specH();
      read.h.textContent = effRank(sH).toFixed(1);
      read.z.textContent = effRank(specZ()).toFixed(1);
      read.reg.textContent = sacreg(sH).toFixed(1);
      drawScatter();
      drawSpectrum();
    }

    function setPlaying(on) {
      play.innerHTML = (on ? PAUSE_ICON : PLAY_ICON) + (on ? 'Pause' : 'Train');
      play.setAttribute('aria-pressed', String(on));
    }

    function stop() { if (anim) cancelAnimationFrame(anim); anim = null; setPlaying(false); }

    play.addEventListener('click', () => {
      if (anim) { stop(); return; }
      if (reduceMotion.matches) { t = 1; slider.value = 100; update(); return; }
      if (t >= 0.999) t = 0;
      let last = performance.now();
      setPlaying(true);
      const step = (now) => {
        t = Math.min(1, t + (now - last) / 4200);
        last = now;
        slider.value = Math.round(t * 100);
        update();
        if (t < 1) anim = requestAnimationFrame(step); else stop();
      };
      anim = requestAnimationFrame(step);
    });
    slider.addEventListener('input', () => { stop(); t = Number(slider.value) / 100; update(); });
    segmented(root.querySelector('.seg'), (v) => { mode = v; update(); });
    onTheme(() => { colors = palette(); update(); });
    setPlaying(false);
    update();
  }

  // ==========================================================================
  // 2. OOD detection with relative angles (ORA)
  // ==========================================================================
  function oraViz(root) {
    const field = root.querySelector('[data-role="field"]');
    const strip = root.querySelector('[data-role="strip"]');
    const slider = root.querySelector('input[type="range"]');
    const out = root.querySelector('output');
    const read = {
      theta: root.querySelector('[data-read="theta"]'),
      dist: root.querySelector('[data-read="dist"]'),
      verdict: root.querySelector('[data-read="verdict"]'),
    };

    // Two classes in a 2D penultimate space, as in Figure 1 of the paper. The head is a
    // nearest-mean linear classifier, so the boundary is the perpendicular bisector.
    const m1 = [-1.45, 0.85], m2 = [1.55, -0.75];
    const rand = mulberry32(11);
    const idPts = [];
    // Unequal class sizes keep the ID mean visibly off the boundary, as in the paper's figure.
    for (let i = 0; i < 150; i++) idPts.push({ c: 0, z: [m1[0] + 0.55 * gaussian(rand), m1[1] + 0.55 * gaussian(rand)] });
    for (let i = 0; i < 60; i++) idPts.push({ c: 1, z: [m2[0] + 0.55 * gaussian(rand), m2[1] + 0.55 * gaussian(rand)] });
    const mu = idPts.reduce((a, p) => [a[0] + p.z[0] / idPts.length, a[1] + p.z[1] / idPts.length], [0, 0]);
    const dw = [m1[0] - m2[0], m1[1] - m2[1]];
    const c0 = -(dw[0] * (m1[0] + m2[0]) + dw[1] * (m1[1] + m2[1])) / 2;

    // Eq. (1): project onto the boundary; Eq. (2): angle at the ID mean. With two classes
    // the max in Eq. (3) is over a single boundary. `s` rescales the whole feature space.
    function ora(z, s = 1) {
      const zs = [z[0] * s, z[1] * s], ms = [mu[0] * s, mu[1] * s];
      const g = dw[0] * zs[0] + dw[1] * zs[1] + c0 * s;
      const n2 = dw[0] * dw[0] + dw[1] * dw[1];
      const zdb = [zs[0] - (g / n2) * dw[0], zs[1] - (g / n2) * dw[1]];
      const u = [zs[0] - ms[0], zs[1] - ms[1]], v = [zdb[0] - ms[0], zdb[1] - ms[1]];
      const nu = Math.hypot(u[0], u[1]), nv = Math.hypot(v[0], v[1]);
      const theta = nu < 1e-9 || nv < 1e-9 ? 0 : Math.acos(clamp((u[0] * v[0] + u[1] * v[1]) / (nu * nv), -1, 1)) * 180 / Math.PI;
      return { theta, zdb, dist: Math.hypot(zs[0] - zdb[0], zs[1] - zdb[1]), side: g > 0 ? 0 : 1 };
    }

    const idScores = idPts.map((p) => ora(p.z).theta).sort((a, b2) => a - b2);
    const threshold = idScores[Math.floor(0.05 * idScores.length)]; // keeps 95% of ID

    let colors = palette();
    let z = [0.86, 1.88];
    let scale = 1;
    let dragging = false;

    const fv = surface(field, drawField);
    const sv = surface(strip, drawStrip);

    const view = () => {
      const { w, h } = fv;
      const s = Math.min(w / 7.6, h / 6.0);
      return { s, ox: w / 2, oy: h / 2 };
    };
    const toPx = ([x, y]) => { const v = view(); return [v.ox + x * v.s, v.oy - y * v.s]; };
    const toWorld = ([px, py]) => { const v = view(); return [(px - v.ox) / v.s, -(py - v.oy) / v.s]; };
    const S = (p) => [p[0] * scale, p[1] * scale];

    function drawField() {
      const { ctx, w, h } = fv;
      if (!w) return;
      ctx.clearRect(0, 0, w, h);

      // Class regions: tint each side of the boundary (dw.z + c = 0, scaled).
      const n = Math.hypot(dw[0], dw[1]);
      const dir = [-dw[1] / n, dw[0] / n];
      const p0 = [(-c0 * scale) * dw[0] / (n * n), (-c0 * scale) * dw[1] / (n * n)];
      const A = toPx([p0[0] - dir[0] * 20, p0[1] - dir[1] * 20]);
      const B = toPx([p0[0] + dir[0] * 20, p0[1] + dir[1] * 20]);
      const nrm = [dw[0] / n, dw[1] / n];
      const off = (p, k) => toPx([p[0] + nrm[0] * k, p[1] + nrm[1] * k]);
      const quad = (k) => {
        const a = [p0[0] - dir[0] * 20, p0[1] - dir[1] * 20], b2 = [p0[0] + dir[0] * 20, p0[1] + dir[1] * 20];
        const C = off(b2, k), D = off(a, k);
        ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.lineTo(C[0], C[1]); ctx.lineTo(D[0], D[1]); ctx.closePath();
      };
      quad(20); ctx.fillStyle = withAlpha(colors.s1, 0.07); ctx.fill();
      quad(-20); ctx.fillStyle = withAlpha(colors.s2, 0.07); ctx.fill();
      ctx.strokeStyle = colors.soft; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.stroke();

      for (const p of idPts) {
        const [x, y] = toPx(S(p.z));
        ctx.beginPath(); ctx.arc(x, y, 2.3, 0, Math.PI * 2);
        ctx.fillStyle = withAlpha(p.c ? colors.s2 : colors.s1, 0.6); ctx.fill();
      }
      ctx.font = `600 12px ${colors.sans}`;
      ctx.textAlign = 'center';
      ctx.fillStyle = colors.s1;
      let [lx, ly] = toPx(S([m1[0] - 0.9, m1[1] + 1.15]));
      ctx.fillText('C1', lx, ly);
      ctx.fillStyle = colors.s2;
      [lx, ly] = toPx(S([m2[0] + 0.95, m2[1] - 1.1]));
      ctx.fillText('C2', lx, ly);

      // The triangle (mu, z, z_db) and the relative angle at mu.
      const r = ora(z, scale);
      const M = toPx(S(mu)), Z = toPx(S(z)), D = toPx(r.zdb);
      ctx.strokeStyle = colors.ink; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(M[0], M[1]); ctx.lineTo(Z[0], Z[1]); ctx.moveTo(M[0], M[1]); ctx.lineTo(D[0], D[1]); ctx.stroke();
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(Z[0], Z[1]); ctx.lineTo(D[0], D[1]); ctx.stroke();
      ctx.setLineDash([]);
      const a1 = Math.atan2(-(Z[1] - M[1]), Z[0] - M[0]);
      const a2 = Math.atan2(-(D[1] - M[1]), D[0] - M[0]);
      let da = a2 - a1;
      while (da > Math.PI) da -= 2 * Math.PI;
      while (da < -Math.PI) da += 2 * Math.PI;
      ctx.strokeStyle = colors.accent; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(M[0], M[1], 26, -a1, -(a1 + da), da > 0); ctx.stroke();
      const mid = a1 + da / 2;
      ctx.fillStyle = colors.accent;
      ctx.font = `italic 600 14px ${colors.sans}`;
      ctx.fillText('θ', M[0] + 40 * Math.cos(mid), M[1] - 40 * Math.sin(mid) + 5);

      ctx.fillStyle = colors.ink;
      ctx.beginPath(); ctx.arc(D[0], D[1], 3.5, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath();
      ctx.moveTo(M[0], M[1] - 6); ctx.lineTo(M[0] + 6, M[1]); ctx.lineTo(M[0], M[1] + 6); ctx.lineTo(M[0] - 6, M[1]);
      ctx.closePath(); ctx.fill();
      ctx.font = `500 12px ${colors.sans}`;
      ctx.textAlign = 'left';
      ctx.fillText('μ_ID', M[0] + 9, M[1] + 15);
      // Put the z_db and z labels on opposite sides of the boundary so they never collide.
      const nx = -dw[0] / n, ny = dw[1] / n; // boundary normal in canvas space, pointing to C2
      ctx.textAlign = 'center';
      ctx.fillText('z_db', D[0] + nx * 24, D[1] + ny * 24 + 4);

      ctx.beginPath(); ctx.arc(Z[0], Z[1], 7.5, 0, Math.PI * 2);
      ctx.fillStyle = colors.card; ctx.fill();
      ctx.strokeStyle = colors.accent; ctx.lineWidth = 2.5; ctx.stroke();
      ctx.fillStyle = colors.ink;
      ctx.fillText('z', Z[0] - nx * 20, Z[1] - ny * 20 + 4);
      ctx.textAlign = 'left';

      ctx.fillStyle = colors.faint;
      ctx.font = `500 11px ${colors.sans}`;
      ctx.fillText('drag z', 8, 16);
    }

    function drawStrip() {
      const { ctx, w, h } = sv;
      if (!w) return;
      ctx.clearRect(0, 0, w, h);
      const padL = 14, padR = 14;
      const pw = w - padL - padR;
      const y0 = h / 2 + 6;
      const X = (a) => padL + (a / 180) * pw;

      ctx.fillStyle = withAlpha(colors.warm, 0.1);
      ctx.fillRect(X(0), y0 - 26, X(threshold) - X(0), 46);
      ctx.strokeStyle = colors.axis; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(X(0), y0 + 20); ctx.lineTo(X(180), y0 + 20); ctx.stroke();
      // ID scores as a jittered strip
      const jr = mulberry32(3);
      ctx.fillStyle = withAlpha(colors.soft, 0.5);
      for (const s of idScores) {
        ctx.beginPath(); ctx.arc(X(s), y0 + (jr() - 0.5) * 22, 2.1, 0, Math.PI * 2); ctx.fill();
      }
      ctx.setLineDash([4, 3]);
      ctx.strokeStyle = colors.ink;
      ctx.beginPath(); ctx.moveTo(X(threshold), y0 - 30); ctx.lineTo(X(threshold), y0 + 20); ctx.stroke();
      ctx.setLineDash([]);
      const t = ora(z, scale).theta;
      ctx.fillStyle = colors.accent;
      ctx.beginPath();
      ctx.moveTo(X(t), y0 - 16); ctx.lineTo(X(t) - 6, y0 - 28); ctx.lineTo(X(t) + 6, y0 - 28); ctx.closePath(); ctx.fill();
      ctx.fillRect(X(t) - 1, y0 - 16, 2, 34);

      ctx.font = `400 10px ${colors.mono}`;
      ctx.fillStyle = colors.faint;
      ctx.textAlign = 'center';
      for (const a of [0, 45, 90, 135, 180]) ctx.fillText(`${a}°`, X(a), y0 + 34);
      ctx.font = `500 11px ${colors.sans}`;
      ctx.textAlign = 'left';
      ctx.fillStyle = colors.warm;
      ctx.fillText('flagged OOD', X(0) + 2, y0 - 34);
      ctx.textAlign = 'right';
      ctx.fillStyle = colors.faint;
      ctx.fillText('ID training scores', X(180), y0 - 34);
    }

    function update() {
      const r = ora(z, scale);
      out.textContent = `×${scale.toFixed(2)}`;
      read.theta.textContent = `${r.theta.toFixed(1)}°`;
      read.dist.textContent = r.dist.toFixed(2);
      const flagged = r.theta < threshold;
      read.verdict.textContent = flagged ? 'flagged OOD' : 'looks in-distribution';
      read.verdict.style.color = flagged ? colors.warm : colors.ink;
      drawField();
      drawStrip();
    }

    const pointer = (e) => {
      const r = field.getBoundingClientRect();
      const p = toWorld([e.clientX - r.left, e.clientY - r.top]);
      return [clamp(p[0] / scale, -3.6, 3.6), clamp(p[1] / scale, -2.9, 2.9)];
    };
    field.addEventListener('pointerdown', (e) => { dragging = true; field.setPointerCapture(e.pointerId); z = pointer(e); update(); });
    field.addEventListener('pointermove', (e) => { if (dragging) { z = pointer(e); update(); } });
    field.addEventListener('pointerup', () => { dragging = false; });
    field.addEventListener('keydown', (e) => {
      const d = { ArrowLeft: [-0.12, 0], ArrowRight: [0.12, 0], ArrowUp: [0, 0.12], ArrowDown: [0, -0.12] }[e.key];
      if (!d) return;
      e.preventDefault();
      z = [clamp(z[0] + d[0], -3.6, 3.6), clamp(z[1] + d[1], -2.9, 2.9)];
      update();
    });
    const places = { boundary: [0.86, 1.88], c1: [-1.9, 1.3], c2: [1.9, -1.1] };
    for (const btn of root.querySelectorAll('[data-place]')) {
      btn.addEventListener('click', () => { z = places[btn.dataset.place]; update(); });
    }
    slider.addEventListener('input', () => { scale = Number(slider.value) / 100; update(); });
    onTheme(() => { colors = palette(); update(); });
    update();
  }

  // ==========================================================================
  // 3. Compositional generation + trust score (MorphGen, sample quality)
  // ==========================================================================
  function trustViz(root) {
    const canvas = root.querySelector('[data-role="features"]');
    const grid = root.querySelector('[data-role="grid"]');
    const slider = root.querySelector('input[type="range"]');
    const out = root.querySelector('output');
    const regen = root.querySelector('[data-role="generate"]');
    const tip = root.querySelector('.viz-tip');
    const read = {
      kept: root.querySelector('[data-read="kept"]'),
      precKept: root.querySelector('[data-read="prec-kept"]'),
      precAll: root.querySelector('[data-read="prec-all"]'),
    };

    // Features: two attribute directions (drawn as x/y), one appearance direction r (drawn as
    // glyph shape; real images have r close to 0), and a few nuisance directions that vary
    // within every condition, as most directions of a real feature space do.
    const POS = [-1.25, 0, 1.25];
    const NUISANCE = 4;
    // Reference coverage: every value of each attribute is observed together with
    // the reference value (index 0) of the other attribute.
    const observed = (i, j) => i === 0 || j === 0;
    const rand = mulberry32(5);
    const nuisance = (r) => Array.from({ length: NUISANCE }, () => gaussian(r));
    const real = [];
    for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
      if (!observed(i, j)) continue;
      for (let n = 0; n < 45; n++) {
        real.push({ i, j, y: [POS[i] + 0.2 * gaussian(rand), POS[j] + 0.2 * gaussian(rand), 0.1 * gaussian(rand), ...nuisance(rand)] });
      }
    }

    const D = 3 + NUISANCE;
    const meanOf = (ys) => ys.reduce((a, y) => a.map((v, d) => v + y[d] / ys.length), new Array(D).fill(0));
    const covOf = (ys, m) => {
      const c = Array.from({ length: D }, () => new Array(D).fill(0));
      for (const y of ys) for (let a = 0; a < D; a++) for (let b2 = 0; b2 < D; b2++) c[a][b2] += (y[a] - m[a]) * (y[b2] - m[b2]) / ys.length;
      for (let a = 0; a < D; a++) c[a][a] += 1e-3; // ridge
      return c;
    };
    // Gauss-Jordan inverse for the small, well-conditioned covariance matrices used here.
    const inv = (m) => {
      const n = m.length;
      const a = m.map((row, i) => [...row, ...Array.from({ length: n }, (_, j) => (i === j ? 1 : 0))]);
      for (let c = 0; c < n; c++) {
        let piv = c;
        for (let r = c + 1; r < n; r++) if (Math.abs(a[r][c]) > Math.abs(a[piv][c])) piv = r;
        [a[c], a[piv]] = [a[piv], a[c]];
        const d = a[c][c];
        for (let k = 0; k < 2 * n; k++) a[c][k] /= d;
        for (let r = 0; r < n; r++) {
          if (r === c) continue;
          const f = a[r][c];
          for (let k = 0; k < 2 * n; k++) a[r][k] -= f * a[c][k];
        }
      }
      return a.map((row) => row.slice(n));
    };
    const maha = (y, m, Pm) => {
      let s = 0;
      for (let a = 0; a < D; a++) for (let b2 = 0; b2 < D; b2++) s += (y[a] - m[a]) * Pm[a][b2] * (y[b2] - m[b2]);
      return s;
    };
    const stats = (arr) => {
      const m = arr.reduce((a, b2) => a + b2, 0) / arr.length;
      const s = Math.sqrt(arr.reduce((a, b2) => a + (b2 - m) * (b2 - m), 0) / arr.length) || 1;
      return [m, s];
    };

    // Global realism R: Mahalanobis energy to the real feature distribution, standardized on real data.
    const ys = real.map((r) => r.y);
    const mReal = meanOf(ys);
    const PReal = inv(covOf(ys, mReal));
    const [mR, sR] = stats(ys.map((y) => maha(y, mReal, PReal)));
    const realism = (y) => (maha(y, mReal, PReal) - mR) / sR;

    // Attribute-wise faithfulness F: value prototypes (anchored at the reference value of the
    // other attribute), a shared within-value precision, and a standardized target-vs-competitor margin.
    const valueOf = (r, k) => (k === 0 ? r.i : r.j);
    const anchored = (r, k) => (k === 0 ? r.j : r.i) === 0;
    const proto = [0, 1].map((k) => POS.map((_, v) => meanOf(real.filter((r) => valueOf(r, k) === v && anchored(r, k)).map((r) => r.y))));
    const precK = [0, 1].map((k) => {
      const centred = real.filter((r) => anchored(r, k)).map((r) => r.y.map((x, d) => x - proto[k][valueOf(r, k)][d]));
      return inv(covOf(centred, new Array(D).fill(0)));
    });
    const margin = (y, k, t) => {
      let best = Infinity;
      for (let v = 0; v < 3; v++) if (v !== t) best = Math.min(best, maha(y, proto[k][v], precK[k]));
      return maha(y, proto[k][t], precK[k]) - best;
    };
    const calib = [0, 1].map((k) => POS.map((_, t) => stats(real.filter((r) => valueOf(r, k) === t).map((r) => margin(r.y, k, t)))));
    const faithfulness = (y, a) =>
      [0, 1].reduce((acc, k) => acc + (margin(y, k, a[k]) - calib[k][a[k]][0]) / calib[k][a[k]][1], 0) / 2;

    let colors = palette();
    let req = [2, 2];
    let samples = [];
    let progress = 1;
    let anim = null;
    let keep = Number(slider.value) / 100;
    let seed = 1;
    let hover = null;

    // Toy generator: mostly lands on the requested composition; sometimes an attribute
    // leaks toward an observed value; sometimes the sample is malformed (large r).
    function generate() {
      const r = mulberry32(seed++ * 977);
      const [i, j] = req;
      const seen = observed(i, j);
      const leakP = seen ? 0.06 : 0.1 + 0.06 * (i + j - 2);
      const offP = seen ? 0.06 : 0.14;
      samples = Array.from({ length: 60 }, () => {
        const u = r();
        let kind = 'ok';
        let target = [POS[i], POS[j]];
        let appearance = 0.1 * gaussian(r);
        if (u < leakP) {
          kind = 'leak';
          target = seen ? [POS[(i + 1) % 3], POS[j]] : r() < 0.5 ? [POS[i], POS[0]] : [POS[0], POS[j]];
        } else if (u < leakP + offP) {
          kind = 'off';
          appearance = (r() < 0.5 ? -1 : 1) * (0.45 + 0.5 * r());
        }
        const y = [target[0] + 0.21 * gaussian(r), target[1] + 0.21 * gaussian(r), appearance, ...nuisance(r)];
        const R = realism(y), F = faithfulness(y, req);
        return { y, kind, R, F, T: R + F, noise: [1.4 * gaussian(r), 1.4 * gaussian(r)] };
      });
      rank();
    }

    // Keep the most trusted fraction (lowest T).
    function rank() {
      const order = [...samples].sort((a, c) => a.T - c.T);
      const n = Math.round(keep * samples.length);
      order.forEach((s, idx) => { s.kept = idx < n; });
    }

    const cv = surface(canvas, draw);
    const view = () => {
      const { w, h } = cv;
      const s = Math.min((w - 40) / 4.2, (h - 30) / 3.9);
      return { s, ox: 34 + (w - 34) / 2, oy: (h - 22) / 2 };
    };
    const toPx = ([x, y]) => { const v = view(); return [v.ox + x * v.s, v.oy - y * v.s]; };
    const posOf = (s) => {
      const e = ease(progress);
      return toPx([s.noise[0] * (1 - e) + s.y[0] * e, s.noise[1] * (1 - e) + s.y[1] * e]);
    };

    function glyph(ctx, x, y, malformed, r) {
      ctx.beginPath();
      if (!malformed) { ctx.arc(x, y, r, 0, Math.PI * 2); return; }
      for (let k = 0; k < 10; k++) {
        const a = (k / 10) * Math.PI * 2;
        const rr = k % 2 ? r * 0.55 : r * 1.35;
        ctx[k ? 'lineTo' : 'moveTo'](x + rr * Math.cos(a), y + rr * Math.sin(a));
      }
      ctx.closePath();
    }

    function draw() {
      const { ctx, w, h } = cv;
      if (!w) return;
      ctx.clearRect(0, 0, w, h);
      const v = view();

      ctx.strokeStyle = colors.grid;
      ctx.lineWidth = 1;
      ctx.font = `400 10px ${colors.mono}`;
      ctx.fillStyle = colors.faint;
      ctx.textAlign = 'center';
      POS.forEach((p, k) => {
        const [x] = toPx([p, 0]);
        const [, y] = toPx([0, p]);
        ctx.beginPath(); ctx.moveTo(x, 6); ctx.lineTo(x, h - 24); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(34, y); ctx.lineTo(w - 6, y); ctx.stroke();
        ctx.fillText(`c${k + 1}`, x, h - 9);
        ctx.fillText(`p${k + 1}`, 16, y + 3);
      });

      ctx.fillStyle = withAlpha(colors.soft, 0.38);
      for (const r of real) {
        const [x, y] = toPx(r.y);
        ctx.beginPath(); ctx.arc(x, y, 1.9, 0, Math.PI * 2); ctx.fill();
      }

      const [tx, ty] = toPx([POS[req[0]], POS[req[1]]]);
      ctx.setLineDash([4, 4]);
      ctx.strokeStyle = colors.ink;
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(tx, ty, v.s * 0.44, 0, Math.PI * 2); ctx.stroke();
      ctx.setLineDash([]);

      const scored = progress >= 1;
      for (const s of samples) {
        const [x, y] = posOf(s);
        const malformed = Math.abs(s.y[2]) > 0.3;
        glyph(ctx, x, y, malformed, 3.6);
        if (!scored) {
          ctx.fillStyle = withAlpha(colors.accent, 0.3 + 0.5 * ease(progress)); ctx.fill();
        } else if (s.kept) {
          ctx.fillStyle = colors.accent; ctx.fill();
          ctx.strokeStyle = colors.card; ctx.lineWidth = 1.2; ctx.stroke();
        } else {
          ctx.strokeStyle = colors.faint; ctx.lineWidth = 1.3; ctx.stroke();
        }
        if (hover === s) {
          ctx.strokeStyle = colors.ink; ctx.lineWidth = 1.5;
          ctx.beginPath(); ctx.arc(x, y, 7.5, 0, Math.PI * 2); ctx.stroke();
        }
      }
      ctx.fillStyle = colors.faint;
      ctx.font = `500 11px ${colors.sans}`;
      ctx.textAlign = 'left';
      ctx.fillText(progress < 1 ? 'denoising…' : 'feature space', 40, 16);
    }

    function updateReadout() {
      out.textContent = `${Math.round(keep * 100)}%`;
      const kept = samples.filter((s) => s.kept);
      read.kept.textContent = `${kept.length} / ${samples.length}`;
      const pct = (arr) => (arr.length ? `${Math.round((100 * arr.filter((s) => s.kind === 'ok').length) / arr.length)}%` : '–');
      read.precKept.textContent = progress >= 1 ? pct(kept) : '…';
      read.precAll.textContent = progress >= 1 ? pct(samples) : '…';
    }

    function run() {
      generate();
      hover = null; tip.hidden = true;
      if (anim) cancelAnimationFrame(anim);
      if (reduceMotion.matches) { progress = 1; draw(); updateReadout(); return; }
      progress = 0;
      const t0 = performance.now();
      const step = (now) => {
        progress = Math.min(1, (now - t0) / 1300);
        draw(); updateReadout();
        if (progress < 1) anim = requestAnimationFrame(step);
      };
      anim = requestAnimationFrame(step);
    }

    // Hover: nearest sample within a generous radius.
    canvas.addEventListener('pointermove', (e) => {
      if (progress < 1) return;
      const r = canvas.getBoundingClientRect();
      const px = e.clientX - r.left, py = e.clientY - r.top;
      let best = null, bd = 14 * 14;
      for (const s of samples) {
        const [x, y] = posOf(s);
        const d = (x - px) ** 2 + (y - py) ** 2;
        if (d < bd) { bd = d; best = s; }
      }
      if (best !== hover) { hover = best; draw(); }
      if (!best) { tip.hidden = true; return; }
      const label = { ok: 'faithful', leak: 'attribute leaked', off: 'malformed' }[best.kind];
      tip.innerHTML = `<b>${best.kept ? 'kept' : 'rejected'}</b> · ${label}<br>R ${best.R.toFixed(1)} + F ${best.F.toFixed(1)} = T ${best.T.toFixed(1)}`;
      tip.hidden = false;
      const [x, y] = posOf(best);
      tip.style.left = `${x}px`;
      tip.style.top = `${y}px`;
    });
    canvas.addEventListener('pointerleave', () => { hover = null; tip.hidden = true; draw(); });

    // Condition grid: rows are perturbations p3..p1, columns are cell types c1..c3.
    for (let j = 2; j >= 0; j--) {
      const lab = document.createElement('span');
      lab.className = 'cg-label';
      lab.textContent = `p${j + 1}`;
      grid.append(lab);
      for (let i = 0; i < 3; i++) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cg-cell' + (observed(i, j) ? ' is-seen' : '');
        btn.dataset.i = i; btn.dataset.j = j;
        btn.setAttribute('aria-label', `Generate cell type c${i + 1} under perturbation p${j + 1} (${observed(i, j) ? 'observed in training' : 'never observed'})`);
        btn.innerHTML = `<span aria-hidden="true">${observed(i, j) ? '' : '?'}</span>`;
        btn.addEventListener('click', () => { req = [i, j]; markGrid(); run(); });
        grid.append(btn);
      }
    }
    grid.append(document.createElement('span'));
    for (let i = 0; i < 3; i++) {
      const lab = document.createElement('span');
      lab.className = 'cg-label';
      lab.textContent = `c${i + 1}`;
      grid.append(lab);
    }
    function markGrid() {
      for (const b2 of grid.querySelectorAll('.cg-cell')) {
        b2.setAttribute('aria-pressed', String(Number(b2.dataset.i) === req[0] && Number(b2.dataset.j) === req[1]));
      }
    }

    slider.addEventListener('input', () => { keep = Number(slider.value) / 100; rank(); draw(); updateReadout(); });
    regen.addEventListener('click', run);
    onTheme(() => { colors = palette(); draw(); });
    markGrid();
    generate();
    progress = 1;
    draw();
    updateReadout();
  }

  // ==========================================================================
  // 4. What makes a representation good? (Research page, representation learning)
  // ==========================================================================
  function desiderataViz(root) {
    const scatter = root.querySelector('[data-role="rep"]');
    const bars = root.querySelector('[data-role="probes"]');
    const verdict = root.querySelector('[data-read="verdict"]');

    // Every input has two binary factors: shape (circle/triangle) and color.
    const rand = mulberry32(21);
    const pts = [];
    for (let s = 0; s < 2; s++) for (let c = 0; c < 2; c++) for (let n = 0; n < 40; n++) {
      pts.push({ s, c, u: [gaussian(rand), gaussian(rand)], v: rand() });
    }
    const layouts = {
      // Both factors kept, each along its own direction.
      good: (p) => [(p.s ? 1 : -1) + 0.3 * p.u[0], (p.c ? 1 : -1) + 0.3 * p.u[1]],
      // Color squeezed out: only shape survives.
      collapsed: (p) => [(p.s ? 1 : -1) + 0.3 * p.u[0], 0.07 * p.u[1]],
      // Everything kept, but shape is encoded by radius: present, not linearly readable.
      entangled: (p) => {
        const r = p.s ? 1.5 : 0.62;
        const a = (p.c ? -Math.PI / 2 : Math.PI / 2) + (p.v - 0.5) * Math.PI * 0.92;
        return [r * Math.cos(a) + 0.07 * p.u[0], r * Math.sin(a) + 0.07 * p.u[1]];
      },
    };
    const notes = {
      good: 'Both factors are present and a linear probe reads each of them.',
      collapsed: 'Color has been squeezed out. No probe, however flexible, can recover it.',
      entangled: 'Shape is still there, but only a flexible probe can read it.',
    };

    // Probes: logistic regression (linear) and leave-one-out kNN (flexible).
    function linearProbe(X, y) {
      let w = [0, 0], b = 0;
      for (let it = 0; it < 400; it++) {
        let g0 = 0, g1 = 0, gb = 0;
        for (let i = 0; i < X.length; i++) {
          const p = 1 / (1 + Math.exp(-(w[0] * X[i][0] + w[1] * X[i][1] + b)));
          const e = p - y[i];
          g0 += e * X[i][0]; g1 += e * X[i][1]; gb += e;
        }
        w = [w[0] - (0.5 * g0) / X.length - 0.002 * w[0], w[1] - (0.5 * g1) / X.length - 0.002 * w[1]];
        b -= (0.5 * gb) / X.length;
      }
      let ok = 0;
      for (let i = 0; i < X.length; i++) ok += ((w[0] * X[i][0] + w[1] * X[i][1] + b > 0) ? 1 : 0) === y[i] ? 1 : 0;
      return { w, b, acc: ok / X.length };
    }
    function knnProbe(X, y, k = 7) {
      let ok = 0;
      for (let i = 0; i < X.length; i++) {
        const d = X.map((q, j) => [j === i ? Infinity : (q[0] - X[i][0]) ** 2 + (q[1] - X[i][1]) ** 2, y[j]]).sort((a, c) => a[0] - c[0]);
        let votes = 0;
        for (let j = 0; j < k; j++) votes += d[j][1];
        ok += (votes * 2 > k ? 1 : 0) === y[i] ? 1 : 0;
      }
      return ok / X.length;
    }
    const results = {};
    for (const [name, f] of Object.entries(layouts)) {
      const X = pts.map(f);
      results[name] = {};
      for (const task of ['s', 'c']) {
        const y = pts.map((p) => p[task]);
        const lin = linearProbe(X, y);
        results[name][task] = { lin, knn: knnProbe(X, y) };
      }
    }

    let colors = palette();
    let mode = 'good';
    let from = 'good';
    let progress = 1;
    let anim = null;

    const sv = surface(scatter, drawScatter);
    const bv = surface(bars, drawBars);
    const view = () => {
      const { w, h } = sv;
      const s = Math.min(w / 4.4, h / 4.0);
      return { s, ox: w / 2, oy: h / 2 };
    };
    const toPx = ([x, y]) => { const v = view(); return [v.ox + x * v.s, v.oy - y * v.s]; };

    function marker(ctx, x, y, tri, r) {
      ctx.beginPath();
      if (tri) {
        ctx.moveTo(x, y - r * 1.25); ctx.lineTo(x + r * 1.15, y + r * 0.85); ctx.lineTo(x - r * 1.15, y + r * 0.85); ctx.closePath();
      } else ctx.arc(x, y, r, 0, Math.PI * 2);
    }

    function probeLine(ctx, { w, b }, dash, label) {
      // Clip w.x + b = 0 to the visible box.
      const v = view();
      const { w: W, h: H } = sv;
      const xs = [-(v.ox / v.s), (W - v.ox) / v.s], ys = [-((H - v.oy) / v.s), v.oy / v.s];
      const pts2 = [];
      if (Math.abs(w[1]) > 1e-6) for (const x of xs) { const y = -(w[0] * x + b) / w[1]; if (y >= ys[0] && y <= ys[1]) pts2.push([x, y]); }
      if (Math.abs(w[0]) > 1e-6) for (const y of ys) { const x = -(w[1] * y + b) / w[0]; if (x >= xs[0] && x <= xs[1]) pts2.push([x, y]); }
      if (pts2.length < 2) return;
      const [A, B] = [toPx(pts2[0]), toPx(pts2[1])];
      ctx.setLineDash(dash);
      ctx.strokeStyle = colors.ink; ctx.lineWidth = 1.4;
      ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.stroke();
      ctx.setLineDash([]);
      const top = A[1] < B[1] ? A : B;
      ctx.fillStyle = colors.soft;
      ctx.font = `500 11px ${colors.sans}`;
      ctx.textAlign = top[0] > sv.w / 2 ? 'right' : 'left';
      ctx.fillText(label, top[0] + (top[0] > sv.w / 2 ? -6 : 6), Math.max(14, top[1] + 14));
    }

    function drawScatter() {
      const { ctx, w, h } = sv;
      if (!w) return;
      ctx.clearRect(0, 0, w, h);
      const e = ease(progress);
      for (const p of pts) {
        const a = layouts[from](p), b2 = layouts[mode](p);
        const [x, y] = toPx([a[0] * (1 - e) + b2[0] * e, a[1] * (1 - e) + b2[1] * e]);
        marker(ctx, x, y, p.s === 1, 3.6);
        ctx.fillStyle = withAlpha(p.c ? colors.s2 : colors.s1, 0.85); ctx.fill();
      }
      if (progress >= 1) {
        probeLine(ctx, results[mode].s.lin, [], 'linear probe: shape');
        if (mode !== 'collapsed') probeLine(ctx, results[mode].c.lin, [5, 4], 'linear probe: color');
      }
    }

    function drawBars() {
      const { ctx, w, h } = bv;
      if (!w) return;
      ctx.clearRect(0, 0, w, h);
      const padL = 34, padR = 8, padT = 22, padB = 30;
      const pw = w - padL - padR, ph = h - padT - padB;
      const y0 = padT + ph;
      const Y = (a) => y0 - a * ph;
      ctx.font = `400 10px ${colors.mono}`;
      ctx.textAlign = 'right';
      for (const g of [0, 0.5, 1]) {
        ctx.strokeStyle = g === 0 ? colors.axis : colors.grid;
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(padL, Y(g)); ctx.lineTo(w - padR, Y(g)); ctx.stroke();
        ctx.fillStyle = colors.faint;
        ctx.fillText(`${g * 100}%`, padL - 5, Y(g) + 3);
      }
      ctx.setLineDash([3, 3]);
      ctx.strokeStyle = colors.faint;
      ctx.beginPath(); ctx.moveTo(padL, Y(0.5)); ctx.lineTo(w - padR, Y(0.5)); ctx.stroke();
      ctx.setLineDash([]);
      const r = results[mode];
      const groups = [['shape', r.s], ['color', r.c]];
      const gw = pw / 2;
      const bw = Math.min(46, gw * 0.3);
      groups.forEach(([name, res], gi) => {
        const cx = padL + gw * gi + gw / 2;
        [[res.lin.acc, true], [res.knn, false]].forEach(([acc, filled], k) => {
          const x = cx + (k ? 4 : -bw - 4);
          const top = Y(acc);
          ctx.beginPath();
          ctx.moveTo(x, y0); ctx.lineTo(x, top + 3); ctx.quadraticCurveTo(x, top, x + 3, top);
          ctx.lineTo(x + bw - 3, top); ctx.quadraticCurveTo(x + bw, top, x + bw, top + 3); ctx.lineTo(x + bw, y0);
          if (filled) { ctx.fillStyle = colors.accent; ctx.fill(); } else { ctx.strokeStyle = colors.accent; ctx.lineWidth = 1.5; ctx.stroke(); }
          ctx.fillStyle = colors.ink;
          ctx.font = `500 11px ${colors.mono}`;
          ctx.textAlign = 'center';
          ctx.fillText(`${Math.round(acc * 100)}`, x + bw / 2, top - 5);
        });
        ctx.fillStyle = colors.soft;
        ctx.font = `500 12px ${colors.sans}`;
        ctx.fillText(`task: ${name}`, cx, h - 9);
      });
      ctx.fillStyle = colors.faint;
      ctx.font = `500 11px ${colors.sans}`;
      ctx.textAlign = 'right';
      ctx.fillText('chance', w - padR, Y(0.5) - 4);
    }

    function show(next) {
      if (anim) cancelAnimationFrame(anim);
      from = mode === next ? from : mode;
      mode = next;
      verdict.textContent = notes[mode];
      drawBars();
      if (reduceMotion.matches) { progress = 1; drawScatter(); return; }
      progress = 0;
      const t0 = performance.now();
      const step = (now) => {
        progress = Math.min(1, (now - t0) / 700);
        drawScatter();
        if (progress < 1) anim = requestAnimationFrame(step);
      };
      anim = requestAnimationFrame(step);
    }

    segmented(root.querySelector('.seg'), show);
    onTheme(() => { colors = palette(); drawScatter(); drawBars(); });
    verdict.textContent = notes[mode];
  }

  // ==========================================================================
  // 5. When should a model generalize? (Research page, generalization)
  // ==========================================================================
  function shiftViz(root) {
    const field = root.querySelector('[data-role="inputs"]');
    const chart = root.querySelector('[data-role="curves"]');
    const slider = root.querySelector('input[type="range"]');
    const out = root.querySelector('output');
    const play = root.querySelector('[data-role="play"]');
    const status = { inputs: root.querySelector('[data-read="inputs"]'), rule: root.querySelector('[data-read="rule"]') };
    const read = {
      acc: root.querySelector('[data-read="acc"]'),
      conf: root.querySelector('[data-read="conf"]'),
      ood: root.querySelector('[data-read="ood"]'),
    };

    // Training data: two classes separated along x. The model is a logistic regression.
    const rand = mulberry32(31);
    const sample = (r) => {
      const c = r() < 0.5 ? 0 : 1;
      return { c, z: [(c ? 1.1 : -1.1) + 0.45 * gaussian(r), 0.45 * gaussian(r)] };
    };
    const train = Array.from({ length: 160 }, () => sample(rand));
    let lw = [0, 0], lb = 0;
    for (let it = 0; it < 300; it++) {
      let g0 = 0, g1 = 0, gb = 0;
      for (const p of train) {
        const q = 1 / (1 + Math.exp(-(lw[0] * p.z[0] + lw[1] * p.z[1] + lb)));
        g0 += (q - p.c) * p.z[0]; g1 += (q - p.c) * p.z[1]; gb += q - p.c;
      }
      lw = [lw[0] - 0.4 * (g0 / train.length + 0.05 * lw[0]), lw[1] - 0.4 * (g1 / train.length + 0.05 * lw[1])];
      lb -= 0.4 * gb / train.length;
    }
    const prob = (z) => 1 / (1 + Math.exp(-(lw[0] * z[0] + lw[1] * z[1] + lb)));

    // Out-of-distribution score: Mahalanobis distance to the training inputs, thresholded
    // at the 95th percentile of training scores.
    const mu = train.reduce((a, p) => [a[0] + p.z[0] / train.length, a[1] + p.z[1] / train.length], [0, 0]);
    const C = [[0, 0], [0, 0]];
    for (const p of train) {
      const d = [p.z[0] - mu[0], p.z[1] - mu[1]];
      C[0][0] += d[0] * d[0] / train.length; C[0][1] += d[0] * d[1] / train.length; C[1][1] += d[1] * d[1] / train.length;
    }
    const det = C[0][0] * C[1][1] - C[0][1] * C[0][1];
    const P = [[C[1][1] / det, -C[0][1] / det], [-C[0][1] / det, C[0][0] / det]];
    const maha = (z) => {
      const d = [z[0] - mu[0], z[1] - mu[1]];
      return d[0] * (P[0][0] * d[0] + P[0][1] * d[1]) + d[1] * (P[1][0] * d[0] + P[1][1] * d[1]);
    };
    const trainScores = train.map((p) => maha(p.z)).sort((a, c) => a - c);
    const tau = trainScores[Math.floor(0.95 * trainScores.length)];

    // Test distribution for each kind of shift: where its inputs sit (an offset of the two
    // class clusters) and the rule that labels them (a line: a point on it and its normal).
    const base = Array.from({ length: 150 }, () => sample(mulberry32(7 + Math.floor(rand() * 1e6))).z);
    const SHIFT_X = 1.9, SHIFT_Y = 2.4;
    const kinds = {
      benign: {
        changes: { inputs: 'shifted', rule: 'unchanged' },
        offset: (s) => [0, SHIFT_Y * s],
        line: () => ({ p: [0, 0], n: [1, 0] }),
      },
      harmful: {
        changes: { inputs: 'shifted', rule: 'shifted with the inputs' },
        offset: (s) => [SHIFT_X * s, 0],
        line: (s) => ({ p: [SHIFT_X * s, 0], n: [1, 0] }),
      },
      concept: {
        changes: { inputs: 'unchanged', rule: 'changed' },
        offset: () => [0, 0],
        line: (s) => { const phi = s * Math.PI / 2; return { p: [0, 0], n: [Math.cos(phi), Math.sin(phi)] }; },
      },
    };
    const ruleFor = (k, s) => {
      const { p, n } = kinds[k].line(s);
      return (z) => ((z[0] - p[0]) * n[0] + (z[1] - p[1]) * n[1] > 0 ? 1 : 0);
    };
    const inputsFor = (k, s) => { const o = kinds[k].offset(s); return (z) => [z[0] + o[0], z[1] + o[1]]; };
    const metrics = (k, s) => {
      const rule = ruleFor(k, s), move = inputsFor(k, s);
      let acc = 0, conf = 0, ood = 0;
      for (const z0 of base) {
        const z = move(z0);
        const q = prob(z);
        acc += ((q > 0.5 ? 1 : 0) === rule(z)) ? 1 : 0;
        conf += Math.max(q, 1 - q);
        ood += maha(z) > tau ? 1 : 0;
      }
      return { acc: acc / base.length, conf: conf / base.length, ood: ood / base.length };
    };
    const STEPS = 40;
    const curves = {};
    for (const k of Object.keys(kinds)) curves[k] = Array.from({ length: STEPS + 1 }, (_, i) => metrics(k, i / STEPS));

    let colors = palette();
    let kind = 'benign';
    let s = Number(slider.value) / 100;
    let anim = null;

    const fv = surface(field, drawField);
    const cv = surface(chart, drawChart);
    // A fixed view that holds every case: up to SHIFT_X to the right and SHIFT_Y upwards.
    const view = () => {
      const { w, h } = fv;
      const sc = Math.min(w / 7.2, h / 5.6);
      return { sc, ox: w / 2 - 0.75 * sc, oy: h / 2 + 1.05 * sc };
    };
    const toPx = ([x, y]) => { const v = view(); return [v.ox + x * v.sc, v.oy - y * v.sc]; };
    const toWorld = ([px, py]) => { const v = view(); return [(px - v.ox) / v.sc, -(py - v.oy) / v.sc]; };
    const predict = (z) => (prob(z) > 0.5 ? 1 : 0);

    // Draw a full-length line w.x = c (given by a point and a normal) across the canvas.
    function fullLine(ctx, p, n) {
      const { w, h } = fv;
      const d = [-n[1], n[0]];
      const A = toPx([p[0] - d[0] * 20, p[1] - d[1] * 20]), B = toPx([p[0] + d[0] * 20, p[1] + d[1] * 20]);
      ctx.beginPath(); ctx.moveTo(A[0], A[1]); ctx.lineTo(B[0], B[1]); ctx.stroke();
      // the end that reaches the top edge, for labeling
      const t = (A[1] < B[1]) ? A : B, o = t === A ? B : A;
      const k = (0 - o[1]) / (t[1] - o[1] || 1e-9);
      return [o[0] + (t[0] - o[0]) * Math.min(1, Math.max(0, k)), Math.max(0, o[1] + (t[1] - o[1]) * k)].map((v2, i) => (i ? v2 : Math.min(w - 4, Math.max(4, v2))));
    }

    function chip(ctx, text, x, y, color, align) {
      ctx.font = `600 11px ${colors.sans}`;
      const tw = ctx.measureText(text).width;
      const x0 = align === 'right' ? x - tw : x;
      ctx.fillStyle = withAlpha(colors.card, 0.92);
      ctx.fillRect(x0 - 3, y - 11, tw + 6, 15);
      ctx.fillStyle = color;
      ctx.textAlign = 'left';
      ctx.fillText(text, x0, y);
    }

    function drawField() {
      const { ctx, w, h } = fv;
      if (!w) return;
      ctx.clearRect(0, 0, w, h);
      const rule = ruleFor(kind, s);
      const o = kinds[kind].offset(s);
      const v = view();

      // Test distribution: density of the two shifted class clusters, colored by the true label,
      // with the part the learned boundary gets wrong hatched.
      const sig2 = 0.45 * 0.45;
      const dens = (z) => {
        const a = (z[0] - (-1.1 + o[0])) ** 2 + (z[1] - o[1]) ** 2;
        const b2 = (z[0] - (1.1 + o[0])) ** 2 + (z[1] - o[1]) ** 2;
        return Math.exp(-a / (2 * sig2)) + Math.exp(-b2 / (2 * sig2));
      };
      const cell = 3;
      const cx0 = Math.max(0, Math.floor(toPx([-1.1 + o[0] - 1.6, 0])[0])), cx1 = Math.min(w, Math.ceil(toPx([1.1 + o[0] + 1.6, 0])[0]));
      const cy0 = Math.max(0, Math.floor(toPx([0, o[1] + 1.6])[1])), cy1 = Math.min(h, Math.ceil(toPx([0, o[1] - 1.6])[1]));
      for (let py = cy0; py < cy1; py += cell) {
        for (let px = cx0; px < cx1; px += cell) {
          const z = toWorld([px + cell / 2, py + cell / 2]);
          const d = dens(z);
          if (d < 0.012) continue;
          const truth = rule(z);
          const wrong = predict(z) !== truth;
          const a = 0.3 * Math.min(1, d) ** 0.45;
          if (wrong && ((px + py) % 12) < 4) ctx.fillStyle = withAlpha(colors.warm, 0.9 * Math.min(1, d * 1.6) ** 0.6);
          else ctx.fillStyle = withAlpha(truth ? colors.s2 : colors.s1, a);
          ctx.fillRect(px, py, cell, cell);
        }
      }

      // Training data: fixed, drawn solid.
      for (const p of train) {
        const [x, y] = toPx(p.z);
        ctx.beginPath(); ctx.arc(x, y, 2.6, 0, Math.PI * 2);
        ctx.fillStyle = p.c ? colors.s2 : colors.s1; ctx.fill();
        ctx.strokeStyle = colors.card; ctx.lineWidth = 0.8; ctx.stroke();
      }

      // Learned boundary (fixed) and true boundary of the test distribution (moves with it).
      const lp = [-lb / lw[0], 0], ln = [lw[0] / Math.hypot(lw[0], lw[1]), lw[1] / Math.hypot(lw[0], lw[1])];
      ctx.strokeStyle = colors.ink; ctx.lineWidth = 1.8;
      const lt = fullLine(ctx, lp, ln);
      const { p: tp, n: tn } = kinds[kind].line(s);
      ctx.setLineDash([7, 5]);
      ctx.strokeStyle = colors.warm; ctx.lineWidth = 2.2;
      const tt = fullLine(ctx, tp, tn);
      ctx.setLineDash([]);
      const close = Math.abs(lt[0] - tt[0]) < 40;
      chip(ctx, 'learned', lt[0] - 6, 14, colors.ink, 'right');
      chip(ctx, 'true', close ? tt[0] + 6 : tt[0] + 6, close ? 14 : 14, colors.warm, 'left');
    }

    function drawChart() {
      const { ctx, w, h } = cv;
      if (!w) return;
      ctx.clearRect(0, 0, w, h);
      const padL = 36, padR = 74, padT = 14, padB = 30;
      const pw = w - padL - padR, ph = h - padT - padB;
      const X = (t) => padL + t * pw, Y = (a) => padT + (1 - a) * ph;
      ctx.font = `400 10px ${colors.mono}`;
      ctx.textAlign = 'right';
      for (const g of [0, 0.5, 1]) {
        ctx.strokeStyle = g === 0 ? colors.axis : colors.grid; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(padL, Y(g)); ctx.lineTo(padL + pw, Y(g)); ctx.stroke();
        ctx.fillStyle = colors.faint; ctx.fillText(`${g * 100}%`, padL - 5, Y(g) + 3);
      }
      ctx.textAlign = 'center';
      ctx.font = `500 11px ${colors.sans}`;
      ctx.fillText('amount of shift →', padL + pw / 2, h - 8);

      const series = [['acc', colors.s1, [], 'accuracy'], ['conf', colors.s2, [6, 4], 'confidence'], ['ood', colors.s3, [2, 3], 'flagged OOD']];
      const data = curves[kind];
      const ends = [];
      for (const [key, col, dash, label] of series) {
        ctx.setLineDash(dash);
        ctx.strokeStyle = col; ctx.lineWidth = 2;
        ctx.beginPath();
        data.forEach((m, i) => { const x = X(i / STEPS), y = Y(m[key]); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
        ctx.stroke();
        ctx.setLineDash([]);
        ends.push([Y(data[STEPS][key]), col, label]);
      }
      ends.sort((a, c) => a[0] - c[0]);
      for (let i = 1; i < ends.length; i++) if (ends[i][0] - ends[i - 1][0] < 13) ends[i][0] = ends[i - 1][0] + 13;
      ctx.font = `500 11px ${colors.sans}`;
      ctx.textAlign = 'left';
      for (const [y, , label] of ends) { ctx.fillStyle = colors.soft; ctx.fillText(label, padL + pw + 6, y + 4); }

      const m = metrics(kind, s);
      ctx.strokeStyle = colors.ink; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(X(s), padT); ctx.lineTo(X(s), padT + ph); ctx.stroke();
      for (const [key, col] of series) {
        ctx.beginPath(); ctx.arc(X(s), Y(m[key]), 4, 0, Math.PI * 2);
        ctx.fillStyle = col; ctx.fill();
        ctx.strokeStyle = colors.card; ctx.lineWidth = 1.5; ctx.stroke();
      }
    }

    function update() {
      out.textContent = `${Math.round(s * 100)}%`;
      const m = metrics(kind, s);
      read.acc.textContent = `${Math.round(m.acc * 100)}%`;
      read.conf.textContent = `${Math.round(m.conf * 100)}%`;
      read.ood.textContent = `${Math.round(m.ood * 100)}%`;
      const ch = kinds[kind].changes;
      status.inputs.textContent = s < 0.02 ? 'unchanged' : ch.inputs;
      status.rule.textContent = s < 0.02 ? 'unchanged' : ch.rule;
      for (const el of Object.values(status)) el.classList.toggle('is-changed', el.textContent !== 'unchanged');
      drawField();
      drawChart();
    }

    function setPlaying(on) {
      play.innerHTML = (on ? PAUSE_ICON : PLAY_ICON) + (on ? 'Pause' : 'Shift');
      play.setAttribute('aria-pressed', String(on));
    }
    function stop() { if (anim) cancelAnimationFrame(anim); anim = null; setPlaying(false); }
    play.addEventListener('click', () => {
      if (anim) { stop(); return; }
      if (reduceMotion.matches) { s = 1; slider.value = 100; update(); return; }
      if (s >= 0.999) s = 0;
      let last = performance.now();
      setPlaying(true);
      const step = (now) => {
        s = Math.min(1, s + (now - last) / 3500);
        last = now;
        slider.value = Math.round(s * 100);
        update();
        if (s < 1) anim = requestAnimationFrame(step); else stop();
      };
      anim = requestAnimationFrame(step);
    });
    slider.addEventListener('input', () => { stop(); s = Number(slider.value) / 100; update(); });
    segmented(root.querySelector('.seg'), (v) => { kind = v; update(); });
    onTheme(() => { colors = palette(); update(); });
    setPlaying(false);
    update();
  }

  // ==========================================================================
  // 6. Modeling a distribution: novelty, memorization, evaluation (Research page, generation)
  // ==========================================================================
  function genViz(root) {
    const field = root.querySelector('[data-role="samples"]');
    const metricsCanvas = root.querySelector('[data-role="metrics"]');
    const slider = root.querySelector('input[type="range"]');
    const out = root.querySelector('output');
    const again = root.querySelector('[data-role="resample"]');

    // Two moons: a finite training set, plus a large held-out set for evaluation.
    const moon = (k, t, r) => {
      const p = k === 0 ? [Math.cos(t), Math.sin(t)] : [1 - Math.cos(t), 0.5 - Math.sin(t)];
      return [(p[0] - 0.5) * 1.35 + 0.07 * gaussian(r), (p[1] - 0.25) * 1.35 + 0.07 * gaussian(r)];
    };
    const r0 = mulberry32(41);
    const train = [];
    for (let k = 0; k < 2; k++) for (let i = 0; i < 40; i++) train.push(moon(k, Math.PI * r0(), r0));
    const held = [];
    for (let k = 0; k < 2; k++) for (let i = 0; i < 400; i++) held.push(moon(k, Math.PI * r0(), r0));

    // The model: a diffusion sampler whose score is exact for the training set smoothed by a
    // Gaussian of width h, p_sigma = mean_i N(x_i, (sigma^2 + h^2) I). Samples follow the
    // probability-flow ODE from noise (sigma_max) down to sigma_min. With h = 0 this is the
    // optimal denoiser for the training set itself, and every sample lands on a training point.
    const N_GEN = 180, STEPS = 36, S_MAX = 2.4, S_MIN = 0.004, RHO = 7;
    const sigmas = Array.from({ length: STEPS }, (_, i) =>
      (S_MAX ** (1 / RHO) + (i / (STEPS - 1)) * (S_MIN ** (1 / RHO) - S_MAX ** (1 / RHO))) ** RHO);
    const hOf = (v) => 0.5 * (1 - v) ** 2;

    let noise = [];
    let seed = 3;
    const redraw = () => {
      const r = mulberry32(seed++ * 7919);
      noise = Array.from({ length: N_GEN }, () => [S_MAX * gaussian(r), S_MAX * gaussian(r)]);
    };
    redraw();

    function sample(h) {
      return noise.map((x0) => {
        const path = [x0];
        let x = x0;
        for (let i = 0; i < STEPS - 1; i++) {
          const v2 = sigmas[i] ** 2 + h * h;
          let mx = -Infinity;
          const logw = train.map((t) => { const l = -((x[0] - t[0]) ** 2 + (x[1] - t[1]) ** 2) / (2 * v2); if (l > mx) mx = l; return l; });
          let Z = 0, dx = 0, dy = 0;
          for (let j = 0; j < train.length; j++) { const wj = Math.exp(logw[j] - mx); Z += wj; dx += wj * train[j][0]; dy += wj * train[j][1]; }
          const score = [(dx / Z - x[0]) / v2, (dy / Z - x[1]) / v2];
          const ds = sigmas[i + 1] - sigmas[i];
          x = [x[0] - ds * sigmas[i] * score[0], x[1] - ds * sigmas[i] * score[1]];
          path.push(x);
        }
        return path;
      });
    }

    // Evaluation: Frechet distance to held-out data (the statistic behind FID) against the share of
    // near-copies of training points.
    const moments = (zs) => {
      const m = zs.reduce((a, z) => [a[0] + z[0] / zs.length, a[1] + z[1] / zs.length], [0, 0]);
      const S = [0, 0, 0];
      for (const z of zs) { const d = [z[0] - m[0], z[1] - m[1]]; S[0] += d[0] * d[0] / zs.length; S[1] += d[0] * d[1] / zs.length; S[2] += d[1] * d[1] / zs.length; }
      return { m, S };
    };
    const frechet = (A, B) => {
      const dm = (A.m[0] - B.m[0]) ** 2 + (A.m[1] - B.m[1]) ** 2;
      const [a, b2, c] = A.S, [d, e, f] = B.S;
      const trProd = a * d + 2 * b2 * e + c * f;
      const detProd = (a * c - b2 * b2) * (d * f - e * e);
      return dm + a + c + d + f - 2 * Math.sqrt(Math.max(0, trProd + 2 * Math.sqrt(Math.max(0, detProd))));
    };
    const heldMoments = moments(held);
    const nearest = (z, set) => { let b2 = Infinity; for (const t of set) { const d = (t[0] - z[0]) ** 2 + (t[1] - z[1]) ** 2; if (d < b2) b2 = d; } return Math.sqrt(b2); };
    const COPY = 0.02;
    const isCopy = (z) => nearest(z, train) < COPY;
    const evaluate = (finals) => ({
      fd: frechet(moments(finals), heldMoments),
      copies: finals.filter(isCopy).length / finals.length,
    });

    const GRID = 20;
    let curves = [];
    const buildCurves = () => {
      curves = Array.from({ length: GRID + 1 }, (_, i) => evaluate(sample(hOf(i / GRID)).map((p) => p[p.length - 1])));
    };

    let colors = palette();
    let v = Number(slider.value) / 100;
    let paths = [];
    let progress = 1;
    let anim = null;

    const fv = surface(field, drawField);
    const mv = surface(metricsCanvas, drawMetrics);
    const view = () => {
      const { w, h } = fv;
      const s = Math.min(w / 5.4, h / 4.4);
      return { s, ox: w / 2, oy: h / 2 };
    };
    const toPx = ([x, y]) => { const q = view(); return [q.ox + x * q.s, q.oy - y * q.s]; };

    function drawField() {
      const { ctx, w, h } = fv;
      if (!w || !paths.length) return;
      ctx.clearRect(0, 0, w, h);
      const upto = progress * (STEPS - 1);
      const k = Math.floor(upto), frac = upto - k;

      // Trajectories from noise towards the data.
      ctx.strokeStyle = withAlpha(colors.accent, 0.13);
      ctx.lineWidth = 1;
      for (const p of paths) {
        ctx.beginPath();
        for (let i = 0; i <= k; i++) { const [x, y] = toPx(p[i]); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
        ctx.stroke();
      }
      for (const t of train) {
        const [x, y] = toPx(t);
        ctx.beginPath(); ctx.arc(x, y, 4.6, 0, Math.PI * 2);
        ctx.strokeStyle = colors.soft; ctx.lineWidth = 1.3; ctx.stroke();
      }
      const done = progress >= 1;
      for (const p of paths) {
        const a = p[Math.min(k, STEPS - 1)], b2 = p[Math.min(k + 1, STEPS - 1)];
        const z = [a[0] + (b2[0] - a[0]) * frac, a[1] + (b2[1] - a[1]) * frac];
        const [x, y] = toPx(z);
        ctx.beginPath(); ctx.arc(x, y, 2.8, 0, Math.PI * 2);
        ctx.fillStyle = done && isCopy(z) ? colors.warm : colors.accent;
        ctx.fill();
      }
      ctx.fillStyle = colors.faint;
      ctx.font = `500 11px ${colors.sans}`;
      ctx.textAlign = 'left';
      ctx.fillText(done ? 'noise → data' : `σ = ${sigmas[Math.min(k, STEPS - 1)].toFixed(2)}`, 8, 16);
    }

    function drawMetrics() {
      const { ctx, w, h } = mv;
      if (!w || !curves.length) return;
      ctx.clearRect(0, 0, w, h);
      const rows = [
        ['fd', 'Fréchet distance to held-out data', 'lower is better', (x) => x.toFixed(3)],
        ['copies', 'Near-copies of training points', 'lower is better', (x) => `${Math.round(x * 100)}%`],
      ];
      const rowH = (h - 16) / rows.length;
      const padL = 8, padR = 58;
      const pw = w - padL - padR;
      const xv = Math.round(v * GRID);
      ctx.fillStyle = colors.faint;
      ctx.font = `500 11px ${colors.sans}`;
      ctx.textAlign = 'left';
      ctx.fillText('heavy smoothing', padL, h - 3);
      ctx.textAlign = 'right';
      ctx.fillText('none →', padL + pw, h - 3);
      rows.forEach(([key, title, sub, fmt], r) => {
        const top = r * rowH + 6;
        const ch = rowH - 40;
        const y0 = top + 30 + ch;
        ctx.textAlign = 'left';
        ctx.fillStyle = colors.ink;
        ctx.font = `600 12px ${colors.sans}`;
        ctx.fillText(title, padL, top + 10);
        ctx.fillStyle = colors.faint;
        ctx.font = `400 11px ${colors.sans}`;
        ctx.fillText(sub, padL, top + 24);
        ctx.strokeStyle = colors.axis; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(padL, y0); ctx.lineTo(padL + pw, y0); ctx.stroke();
        const vals = curves.map((c) => c[key]);
        const hi = key === 'fd' ? Math.max(...vals) * 1.05 : 1;
        const X = (i) => padL + (i / GRID) * pw, Y = (val) => y0 - (val / (hi || 1)) * ch;
        ctx.strokeStyle = colors.soft; ctx.lineWidth = 2;
        ctx.beginPath();
        vals.forEach((val, i) => (i ? ctx.lineTo(X(i), Y(val)) : ctx.moveTo(X(i), Y(val))));
        ctx.stroke();
        ctx.beginPath(); ctx.arc(X(xv), Y(vals[xv]), 4.5, 0, Math.PI * 2);
        ctx.fillStyle = key === 'copies' ? colors.warm : colors.accent; ctx.fill();
        ctx.strokeStyle = colors.card; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.fillStyle = colors.ink;
        ctx.font = `500 12px ${colors.mono}`;
        ctx.textAlign = 'right';
        ctx.fillText(fmt(vals[xv]), w - 4, Y(vals[xv]) + 4);
      });
    }

    function render(animate) {
      paths = sample(hOf(v));
      out.textContent = `h = ${hOf(v).toFixed(3)}`;
      if (anim) cancelAnimationFrame(anim);
      if (!animate || reduceMotion.matches) { progress = 1; drawField(); drawMetrics(); return; }
      progress = 0;
      drawMetrics();
      const t0 = performance.now();
      const step = (now) => {
        progress = Math.min(1, (now - t0) / 1800);
        drawField();
        if (progress < 1) anim = requestAnimationFrame(step);
      };
      anim = requestAnimationFrame(step);
    }

    slider.addEventListener('input', () => { v = Number(slider.value) / 100; render(false); });
    again.addEventListener('click', () => { redraw(); buildCurves(); render(true); });
    onTheme(() => { colors = palette(); drawField(); drawMetrics(); });
    buildCurves();
    render(false);
  }

  const registry = {
    collapse: collapseViz, ora: oraViz, trust: trustViz,
    desiderata: desiderataViz, shift: shiftViz, generative: genViz,
  };
  for (const el of document.querySelectorAll('[data-viz]')) {
    const fn = registry[el.dataset.viz];
    if (fn) fn(el);
  }
})();
