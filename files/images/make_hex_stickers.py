#!/usr/bin/env python3
"""
make_hex_stickers.py — draw hex stickers for each course.

Usage:
    python make_hex_stickers.py [output_dir]

Writes hex-<course>.jpg to output_dir (default: .).
Standard hex-sticker proportions: pointy top, 2in tall x 1.73in wide.
"""

import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyArrowPatch, Rectangle
from matplotlib.transforms import Affine2D

SQ3 = np.sqrt(3)
INNER = 0.91          # inner hex radius (outer = 1); the gap is the border
DPI = 600
FONT_BOLD = "Avenir Next"
FONT_REG = "Avenir"


def hex_xy(r=1.0):
    ang = np.deg2rad(90 + 60 * np.arange(6))
    return np.c_[r * np.cos(ang), r * np.sin(ang)]


def new_sticker(fill, border):
    pad = 0.02
    w, h = 2 * (SQ3 / 2 + pad), 2 * (1 + pad)
    fig = plt.figure(figsize=(1.73 * w / SQ3, 2.0 * h / 2))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-w / 2, w / 2)
    ax.set_ylim(-h / 2, h / 2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.add_patch(Polygon(hex_xy(1.0), closed=True, fc=border, ec="none", zorder=0))
    inner = Polygon(hex_xy(INNER), closed=True, fc=fill, ec="none", zorder=1)
    ax.add_patch(inner)
    return fig, ax, inner


def half_width(y, r=INNER):
    """Half the width of the (pointy-top) inner hexagon at height y."""
    return np.minimum(SQ3 / 2 * r, SQ3 * (r - np.abs(y)))


def add_text(ax, code, subtitle, color="white", sub_color=None):
    ax.text(0, -0.30, code, ha="center", va="center", color=color,
            fontsize=18, fontfamily=FONT_BOLD, fontweight="bold", zorder=5)
    ax.text(0, -0.53, subtitle, ha="center", va="center", color=sub_color or color,
            fontsize=7.2, fontfamily=FONT_REG, linespacing=1.15, zorder=5)


# ── STAT 486: classification with a nonlinear boundary ──────────────────────
def motif_classification(ax, clip, accent, light):
    rng = np.random.default_rng(486)
    # jittered grid -> evenly spread points with no overlaps
    gx, gy = np.meshgrid(np.linspace(-0.56, 0.56, 8), np.linspace(0.04, 0.60, 6))
    x = gx.ravel() + rng.uniform(-0.035, 0.035, gx.size)
    y = gy.ravel() + rng.uniform(-0.03, 0.03, gy.size)
    boundary = lambda t: 0.32 + 0.15 * np.sin(4.2 * t + 0.3)
    side = y > boundary(x)
    keep = (np.abs(y - boundary(x)) > 0.06) & (np.abs(x) < half_width(y) - 0.09)
    keep &= rng.random(x.size) > 0.25                # thin out a little
    x, y, side = x[keep], y[keep], side[keep]
    ax.scatter(x[side], y[side], s=26, c=light, edgecolors="none", zorder=3, clip_path=clip)
    ax.scatter(x[~side], y[~side], s=26, facecolors="none", edgecolors=light,
               linewidths=1.3, zorder=3, clip_path=clip)
    t = np.linspace(-0.8, 0.8, 200)
    (ln,) = ax.plot(t, boundary(t), color=accent, lw=2.4, zorder=4, solid_capstyle="round")
    ln.set_clip_path(clip)


# ── MSDS 534: a small neural network ────────────────────────────────────────
def motif_network(ax, clip, accent, light):
    layers = [3, 4, 4, 2]
    xs = np.linspace(-0.52, 0.52, len(layers))
    pos = []
    for xi, n in zip(xs, layers):
        ys = 0.33 + (np.arange(n) - (n - 1) / 2) * 0.17
        pos.append([(xi, yi) for yi in ys])
    for a, b in zip(pos[:-1], pos[1:]):
        for (x0, y0) in a:
            for (x1, y1) in b:
                ax.plot([x0, x1], [y0, y1], color=light, lw=0.6, alpha=0.55, zorder=2)
    for li, layer in enumerate(pos):
        for (xi, yi) in layer:
            fc = accent if li in (0, len(pos) - 1) else light
            ax.add_patch(Circle((xi, yi), 0.052, fc=fc, ec="none", zorder=3))


# ── MSDS 597: messy cells → tidy table ──────────────────────────────────────
def motif_wrangling(ax, clip, accent, light):
    rng = np.random.default_rng(597)
    cw, ch = 0.105, 0.075
    # messy pile on the left: a loose 2x4 grid, jittered and rotated
    slots = [(cx, cy) for cy in np.linspace(0.14, 0.50, 4) for cx in (-0.53, -0.37)]
    for k, (cx, cy) in enumerate(slots):
        if k in (1, 6):                              # a couple of "missing" cells
            continue
        cx += rng.uniform(-0.03, 0.03)
        cy += rng.uniform(-0.02, 0.02)
        ang = rng.choice([-1, 1]) * rng.uniform(12, 35)
        r = Rectangle((cx - cw / 2, cy - ch / 2), cw, ch, fc=accent if k in (0, 5) else light,
                      ec="none", zorder=3)
        r.set_transform(Affine2D().rotate_deg_around(cx, cy, ang) + ax.transData)
        ax.add_patch(r)
    # arrow
    ax.add_patch(FancyArrowPatch((-0.25, 0.33), (-0.04, 0.33), arrowstyle="-|>",
                                 mutation_scale=16, lw=2.6, color=light, zorder=3))
    # tidy table on the right: header row in accent
    ncol, nrow, gap = 3, 5, 0.018
    x0, ytop = 0.02, 0.58
    for i in range(nrow):
        for j in range(ncol):
            fc = accent if i == 0 else light
            ax.add_patch(Rectangle((x0 + j * (cw + gap), ytop - (i + 1) * (ch + gap)), cw, ch,
                                   fc=fc, ec="none", zorder=3))


COURSES = [
    dict(slug="stat486", code="STAT 486", subtitle="Applied\nStatistical Learning",
         fill="#CC0033", border="#7A001F", accent="#FFE08A", light="white",
         motif=motif_classification),
    dict(slug="msds534", code="MSDS 534", subtitle="Statistical Learning\nfor Data Science",
         fill="#2E3A87", border="#161D4A", accent="#FFC857", light="white",
         motif=motif_network),
    dict(slug="msds597", code="MSDS 597", subtitle="Data Wrangling\nwith Python",
         fill="#127C74", border="#09453F", accent="#FFD43B", light="white",
         motif=motif_wrangling),
]


def main(out_dir="."):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for c in COURSES:
        fig, ax, clip = new_sticker(c["fill"], c["border"])
        c["motif"](ax, clip, c["accent"], c["light"])
        add_text(ax, c["code"], c["subtitle"])
        jpg = out / f"hex-{c['slug']}.jpg"
        fig.savefig(jpg, dpi=DPI, facecolor="white", pil_kwargs={"quality": 92})
        plt.close(fig)
        print("wrote", jpg)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
