import argparse
import os
from itertools import cycle

import matplotlib
matplotlib.use("Agg")                      
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

from ..algorithms import ALGORITHMS
from .local_client import LocalGridClient
from .scenarios import build_scenarios


def _weights(sc):
    w = np.ones((sc.size, sc.size))
    for (r, c), val in sc.obstacles.items():
        w[r, c] = val
    return w


def _base(ax, sc):
    """Fond commun: poids en gris (échelle log), grille fine, départ et arrivée."""
    w = _weights(sc)
    ax.imshow(w, cmap="Greys", norm=LogNorm(vmin=1, vmax=max(w.max(), 2)))
    if sc.size <= 25:
        ax.set_xticks(np.arange(-.5, sc.size, 1), minor=True)
        ax.set_yticks(np.arange(-.5, sc.size, 1), minor=True)
        ax.grid(which="minor", color="lightgray", lw=0.4)
    ax.tick_params(which="both", length=0, labelbottom=False, labelleft=False)
    (sr, scol), (tr, tcol) = sc.start, sc.target
    ax.scatter([scol], [sr], marker="*", s=160, c="limegreen", edgecolors="k", zorder=5)
    ax.scatter([tcol], [tr], marker="X", s=110, c="crimson", edgecolors="k", zorder=5)


def _title(algo, res):
    steps = max(len(res.path) - 1, 0)
    return f"{algo}\n{steps} pas · coût {res.cost:g} · {res.expanded} développés"


def draw_panels(sc, out_dir, explored=True):
    problem = sc.problem()
    fig, axes = plt.subplots(1, len(ALGORITHMS), figsize=(4.2 * len(ALGORITHMS), 4.8),
                             squeeze=False)
    for ax, (algo, fn) in zip(axes[0], ALGORITHMS.items()):
        client = LocalGridClient(sc)
        res = fn(client, problem)
        _base(ax, sc)
        if explored:
            mask = np.zeros((sc.size, sc.size), dtype=bool)
            for r, c in client.visited():
                mask[r, c] = True
            ax.imshow(np.ma.masked_where(~mask, mask.astype(float)),
                      cmap="Blues", vmin=0, vmax=2, alpha=0.45)
        if res.found:
            ax.plot([p[1] for p in res.path], [p[0] for p in res.path],
                    color="red", lw=2.2, marker="o", ms=2.5, zorder=4)
        ax.set_title(_title(algo, res), fontsize=10)
    fig.suptitle(f"{sc.name} · {sc.size}x{sc.size} · connectivité {sc.connectivity}")
    return _save(fig, sc, out_dir, "panels")


def draw_overlay(sc, out_dir):
    problem = sc.problem()
    fig, ax = plt.subplots(figsize=(6.2, 6.8))
    _base(ax, sc)
    styles = cycle([("tab:red", "-", 3.2), ("tab:blue", "--", 2.4), ("tab:green", ":", 2.4),
                    ("tab:orange", "-.", 2.0), ("tab:purple", "-", 1.6)])
    for (algo, fn), (color, ls, lw) in zip(ALGORITHMS.items(), styles):
        res = fn(LocalGridClient(sc), problem)
        if res.found:
            ax.plot([p[1] for p in res.path], [p[0] for p in res.path], color=color,
                    ls=ls, lw=lw, alpha=0.9, zorder=4,
                    label=f"{algo}: {len(res.path) - 1} pas, coût {res.cost:g}")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), fontsize=9)
    ax.set_title(f"{sc.name} · {sc.size}x{sc.size} · connectivité {sc.connectivity}")
    return _save(fig, sc, out_dir, "overlay")


def _save(fig, sc, out_dir, kind):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{sc.name}_{sc.size}_c{sc.connectivity}_{kind}.png")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def main():
    ap = argparse.ArgumentParser(prog="robot_agent.bench.viz")
    ap.add_argument("--name", help="une disposition (ex: drawing); sinon toutes")
    ap.add_argument("--size", type=int, default=20)
    ap.add_argument("--conn", type=int, nargs="+", default=[4, 8])
    ap.add_argument("--overlay", action="store_true", help="tous les chemins sur une grille")
    ap.add_argument("--no-explored", action="store_true", help="masque les nœuds explorés")
    ap.add_argument("--out", default="results/viz")
    args = ap.parse_args()

    for sc in build_scenarios([args.size]):
        if args.name and sc.name != args.name:
            continue
        if sc.connectivity not in args.conn:
            continue
        path = (draw_overlay(sc, args.out) if args.overlay
                else draw_panels(sc, args.out, explored=not args.no_explored))
        print("écrit:", path)


if __name__ == "__main__":
    main()