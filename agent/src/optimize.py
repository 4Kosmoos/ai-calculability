"""Optimise le poids w de AStarWeighted : grid search macro puis recherche fine.

F = a*coût_rel + b*temps_rel + c*mémoire_rel (a+b+c = 1), chaque terme relatif à A* classique (w=1).
Nécessite l'API grid sur localhost:8000.
"""
import argparse
import csv

from optimizer import WEIGHTS, evaluate, fitness, grid_search, ratios, refine
from optimizer.search import compareRandom

MACRO_VALUES = [1, 10, 100, 5000, 100000]


def show(title, rows, reference):
    print(f"\n{title}")
    print(f"{'w':>12}{'F':>9}{'coût':>9}{'temps (ms)':>12}{'tas':>7}{'nœuds':>7}   coût/réf  temps/réf  tas/réf")
    for row in sorted(rows, key=lambda r: r["F"]):
        cost = "-" if row["cost"] is None else f"{row['cost']:.1f}"
        rel = "" if row["cost"] is None else "".join(f"{v:>10.2f}" for v in ratios(row, reference).values())
        print(f"{row['w']:>12g}{row['F']:>9.3f}{cost:>9}{row['time']*1000:>12.1f}{row['memory']:>7}{row['expanded']:>7}   {rel}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--a", type=float, default=WEIGHTS[0], help="part du coût")
    parser.add_argument("--b", type=float, default=WEIGHTS[1], help="part du temps")
    parser.add_argument("--c", type=float, default=WEIGHTS[2], help="part de la mémoire")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default="results.csv")
    args = parser.parse_args()

    total = args.a + args.b + args.c
    weights = (args.a / total, args.b / total, args.c / total)
    print(f"Parts de F : coût {weights[0]:.0%}, temps {weights[1]:.0%}, mémoire {weights[2]:.0%}")

    reference = evaluate(1, repeats=args.repeats)  # A* classique : F(1) = 1
    options = dict(weights=weights, repeats=args.repeats)

    macro = grid_search(MACRO_VALUES, reference, **options)
    show("Grid search macro", macro, reference)

    (grid_range, random_range), fine = refine(macro, reference, seed=args.seed, **options)
    show(f"Recherche fine : grid dans [{grid_range[0]:g}, {grid_range[1]:g}], "
         f"random dans [{random_range[0]:g}, {random_range[1]:g}]", fine, reference)

    everything = {row["w"]: row for row in macro + fine}.values()
    best = min(everything, key=lambda r: r["F"])
    print(f"\nMeilleur w = {best['w']:g} (F = {best['F']:.3f}, A* classique = 1.000)")

    simple = compareRandom(reference, seed=args.seed, weights=weights, repeats=args.repeats)
    show("Random simple (20 tirages dans [1, 500])", simple, reference)
    best_simple = min(simple, key=lambda r: r["F"])
    print(f"\nComparaison : refine -> w = {best['w']:g}, F = {best['F']:.3f} ({len(macro) + len(fine)} évaluations)"
          f" | random simple -> w = {best_simple['w']:g}, F = {best_simple['F']:.3f} ({len(simple)} évaluations)")

    referenceDjik = evaluate(0, repeats=args.repeats)  # Dijkstra : w = 0 (f = g)
    djikstra = {**referenceDjik, "F": fitness(referenceDjik, reference, weights)}
    show("Référence Dijkstra (w = 0)", [djikstra], reference)

    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["w", "F", "cost", "time", "memory", "expanded"])
        writer.writeheader()
        for row in sorted([djikstra, *everything], key=lambda r: r["w"]):
            writer.writerow({k: row[k] for k in writer.fieldnames})
    print(f"Résultats écrits dans {args.out}")
