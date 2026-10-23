"""Teste le w trouvé sur la configuration fixe (60x60, 25 %, seed 42) sur des configurations variables.

Pour chaque configuration (taille, densité d'obstacles, seed), la référence est A* classique (w = 1)
mesuré sur cette même configuration ; F est calculé comme dans optimize.py. Compare w_best à quelques
w repères. Recrée la grille de l'API à chaque configuration, puis restaure la configuration fixe.
"""
import argparse
import csv
import itertools
import statistics

from generate_grid import init_grid
from optimizer import WEIGHTS, evaluate, fitness, ratios

SIZES = [30, 60, 80]
DENSITIES = [0.10, 0.25, 0.40]
SEEDS = [1, 2]
FIXED = dict(size=60, density=0.25, seed=42)  # configuration utilisée pour l'optimisation

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--w-best", type=float, default=2.3189, help="w trouvé sur la configuration fixe")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--out", default="robustness.csv")
    args = parser.parse_args()

    landmarks = [1, args.w_best, 5, 10, 100]
    rows = []
    try:
        for size, density, seed in itertools.product(SIZES, DENSITIES, SEEDS):
            init_grid(size, density, seed)
            ref = evaluate(1, repeats=args.repeats)
            for w in landmarks:
                m = ref if w == 1 else evaluate(w, repeats=args.repeats)
                r = ratios(m, ref)
                rows.append({"size": size, "density": density, "seed": seed, "w": w,
                             "F": fitness(m, ref, WEIGHTS), "cost": m["cost"], "time": m["time"],
                             "memory": m["memory"], "expanded": m["expanded"],
                             "cost_ratio": r["cost"], "time_ratio": r["time"], "memory_ratio": r["memory"],
                             "expanded_ratio": m["expanded"] / ref["expanded"]})
            print(f"  fait : {size}x{size}, densité {density:.0%}, seed {seed} (A* classique : {ref['expanded']} nœuds)", flush=True)
    finally:
        init_grid(**FIXED)  # restaure la configuration fixe

    keys = ["size", "density", "seed", "w", "F", "cost", "time", "memory", "expanded",
            "cost_ratio", "time_ratio", "memory_ratio", "expanded_ratio"]
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nw_best = {args.w_best:g} ; repères = {[round(w, 2) for w in landmarks]}")
    print(f"{'config':<22}{'nœuds A*':>9}{'F(w_best)':>10}{'coût/réf':>10}{'nœuds/réf':>10}{'temps/réf':>10}   meilleur repère (F)")
    for size, density, seed in itertools.product(SIZES, DENSITIES, SEEDS):
        group = [r for r in rows if (r["size"], r["density"], r["seed"]) == (size, density, seed)]
        ref = next(r for r in group if r["w"] == 1)
        wb = next(r for r in group if r["w"] == args.w_best)
        bestr = min(group, key=lambda r: r["F"])
        print(f"{f'{size}x{size} {density:.0%} s{seed}':<22}{ref['expanded']:>9}{wb['F']:>10.3f}{wb['cost_ratio']:>10.2f}"
              f"{wb['expanded_ratio']:>10.3f}{wb['time_ratio']:>10.3f}   w = {bestr['w']:g} ({bestr['F']:.3f})")

    print("\nMoyennes de F(w_best) :")
    for label, key, values in (("taille", "size", SIZES), ("densité", "density", DENSITIES)):
        for v in values:
            sel = [r for r in rows if r["w"] == args.w_best and r[key] == v]
            cost = statistics.mean(r["cost_ratio"] for r in sel)
            nodes = statistics.mean(r["expanded_ratio"] for r in sel)
            print(f"  {label} {v:g}: F = {statistics.mean(r['F'] for r in sel):.3f} | coût/réf = {cost:.3f} | nœuds/réf = {nodes:.3f}")
    print(f"Résultats écrits dans {args.out}")
