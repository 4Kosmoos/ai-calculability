"""Optimise le poids w de AStarWeighted : grid search macro puis recherche fine.

F = a*coût_rel + b*temps_rel + c*mémoire_rel (a+b+c = 1), chaque terme relatif à A* classique (w=1).
Nécessite l'API grid sur localhost:8000.
"""
import argparse
import csv

from optimizer import WEIGHTS, evaluate, fitness, grid_search, ratios, refine, hill_climbing
from optimizer.search import compareRandom
from strategies import manhattan

MACRO_VALUES = [1, 10, 100, 5000, 100000]

# Pondérations (coût, temps, mémoire) à comparer sur le meilleur w
CASES = {
    "Cas 1 : coût 80 %": (0.8, 0.1, 0.1),
    "Cas 2 : temps 80 %": (0.1, 0.8, 0.1),
    "Cas 3 : mémoire 80 %": (0.1, 0.1, 0.8),
}


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
    
    cache = {row["w"]: row for row in everything}
    climb = hill_climbing(best["w"], reference, cache=cache, **options)
    show(f"Hill climbing depuis w = {best['w']:g}", climb, reference)
    best_climb = min(climb, key=lambda r: r["F"])
    new_evals = sum(1 for r in climb if r["w"] not in {x["w"] for x in everything})
    print(f"\nHill climbing -> w = {best_climb['w']:g}, F = {best_climb['F']:.3f} "
          f"(départ F = {best['F']:.3f}, {new_evals} nouvelles évaluations)")

    simple = compareRandom(reference, seed=args.seed, weights=weights, repeats=args.repeats)
    show("Random simple (20 tirages dans [1, 500])", simple, reference)
    best_simple = min(simple, key=lambda r: r["F"])
    print(f"\nComparaison : refine -> w = {best['w']:g}, F = {best['F']:.3f} ({len(macro) + len(fine)} évaluations)"
          f" | random simple -> w = {best_simple['w']:g}, F = {best_simple['F']:.3f} ({len(simple)} évaluations)")

    # Comparaison à Dijkstra
    referenceDjik = evaluate(0, repeats=args.repeats)  # Dijkstra : w = 0 (f = g)
    djikstra = {**referenceDjik, "F": fitness(referenceDjik, reference, weights)}
    show("Référence Dijkstra (w = 0)", [djikstra], reference)

    # Comparaison en changeant l'heuristique
    metrics_manhattan = evaluate(best["w"], heuristic=manhattan, repeats=args.repeats)
    row_manhattan = {**metrics_manhattan, "F": fitness(metrics_manhattan, reference, weights)}
    show(f"h = euclidien, w = {best['w']:g}", [best], reference)
    show(f"h = manhattan, w = {best['w']:g}", [row_manhattan], reference)
    print(f"\nHeuristique au meilleur w : euclidien F = {best['F']:.3f} | manhattan F = {row_manhattan['F']:.3f}")

    # Comparaison en changeant les poids
    pool = list({row["w"]: row for row in [*everything, *simple]}.values())
    print(f"\nComparaison de 3 pondérations (points déjà évalués : {len(pool)}), w actuel = {best['w']:g}")
    print(f"{'cas':<24}{'meilleur w':>12}{'F':>8}{'coût':>8}{'temps (ms)':>12}{'tas':>6}   F du w actuel")
    for name, case_weights in CASES.items():
        scored = [{**row, "F": fitness(row, reference, case_weights)} for row in pool]
        best_case = min(scored, key=lambda r: r["F"])
        current = fitness(best, reference, case_weights)
        print(f"{name:<24}{best_case['w']:>12g}{best_case['F']:>8.3f}{best_case['cost']:>8.1f}"
              f"{best_case['time']*1000:>12.1f}{best_case['memory']:>6}   {current:.3f}")

    everything = {row["w"]: row for row in [*everything, *climb]}.values()
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["w", "F", "cost", "time", "memory", "expanded"])
        writer.writeheader()
        for row in sorted([djikstra, *everything], key=lambda r: r["w"]):
            writer.writerow({k: row[k] for k in writer.fieldnames})
    print(f"Résultats écrits dans {args.out}")
