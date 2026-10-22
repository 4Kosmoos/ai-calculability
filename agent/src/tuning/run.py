"""Un config (h, w) par connectivité et par profil: lance grid / random / hill climbing et compare."""
import argparse
import csv
import os
import random
import statistics
from time import perf_counter

from .evaluate import Evaluator
from .grid_search import grid_search
from .hill_climbing import hill_climbing
from .objective import PROFILES, Objective
from .random_search import random_search
from .scenarios import build_scenarios
from .tracker import Tracker

METHODS = {"grid": grid_search, "random": random_search, "hill": hill_climbing}
TOLERANCE = 0.05         

def run_method(name, objective, budget, seed):
    tracker = Tracker(objective, budget)
    return METHODS[name](tracker, random.Random(seed))


def main():
    ap = argparse.ArgumentParser(prog="tuning.run")
    ap.add_argument("--sizes", type=int, nargs="+", default=[20, 40])
    ap.add_argument("--repeats", type=int, default=3, help="répétitions de mesure du temps")
    ap.add_argument("--seeds", type=int, default=10, help="graines pour random et hill")
    ap.add_argument("--budget", type=int, default=21, help="configs évaluables par méthode")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    scenarios = build_scenarios(args.sizes)
    evaluator, cache = Evaluator(repeats=args.repeats), {}
    runs, recos = [], []
    t0 = perf_counter()

    for conn in (4, 8):
        group = [s for s in scenarios if s.connectivity == conn]
        for profile, weights in PROFILES.items():
            obj = Objective(evaluator, group, weights, cache=cache)
            results = [run_method("grid", obj, args.budget, 0)]
            for name in ("random", "hill"):
                results += [run_method(name, obj, args.budget, seed) for seed in range(args.seeds)]

            ref = results[0].best_score
            print(f"\n== connectivité {conn} | profil {profile} {weights} | {len(group)} scénarios ==")
            print(f"{'méthode':<8}{'configs':>8}{'F meilleur':>12}{'F médian':>10}{'écart/grid':>12}{'proche':>8}  config")
            for name in METHODS:
                rs = [r for r in results if r.method == name]
                best = min(rs, key=lambda r: r.best_score)
                med = statistics.median(r.best_score for r in rs)
                close = sum(r.best_score <= ref * (1 + TOLERANCE) for r in rs) / len(rs)
                print(f"{name:<8}{best.n_configs:>8}{best.best_score:>12.3f}{med:>10.3f}"
                      f"{best.best_score - ref:>+12.3f}{close:>8.0%}  {best.best}")
            for i, r in enumerate(results):
                runs.append({"conn": conn, "profile": profile, "method": r.method, "run": i,
                             "config": str(r.best), "F_mean": round(r.best_score, 4),
                             "n_configs": r.n_configs})

            winner = min(results, key=lambda r: (r.best_score, r.n_configs))
            det = obj.detail(winner.best)
            n = len(det)
            recos.append({"conn": conn, "profile": profile, "config": str(winner.best),
                          "found_by": winner.method, "F_mean": round(winner.best_score, 4),
                          "F_worst": round(obj.worst(winner.best), 4),
                          "C_ratio": round(sum(e.c_ratio for _, e, _ in det) / n, 3),
                          "T_ratio": round(sum(e.t_ratio for _, e, _ in det) / n, 3),
                          "M_ratio": round(sum(e.m_ratio for _, e, _ in det) / n, 3),
                          "violations": sum(len(v) for _, _, v in det)})

    print("\n== CONFIGURATION RECOMMANDÉE (une par connectivité et par profil) ==")
    print(f"{'conn':>4} {'profil':<10}{'config':<14}{'F moy.':>8}{'F pire':>8}{'C':>7}{'T':>7}{'M':>7}{'viol.':>6}  trouvée par")
    for r in recos:
        print(f"{r['conn']:>4} {r['profile']:<10}{r['config']:<14}{r['F_mean']:>8.3f}{r['F_worst']:>8.3f}"
              f"{r['C_ratio']:>7.2f}{r['T_ratio']:>7.2f}{r['M_ratio']:>7.2f}{r['violations']:>6}  {r['found_by']}")

    os.makedirs(args.out, exist_ok=True)
    for fname, rows in (("tuning_runs.csv", runs), ("tuning_reco.csv", recos)):
        with open(os.path.join(args.out, fname), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print(f"\n{len(cache)} évaluations (config, scénario) en {perf_counter() - t0:.0f} s -> {args.out}/")


if __name__ == "__main__":
    main()