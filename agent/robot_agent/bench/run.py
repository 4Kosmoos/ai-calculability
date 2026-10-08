import csv
import statistics
import tracemalloc
from itertools import groupby

from ..algorithms import ALGORITHMS
from .local_client import LocalGridClient
from .scenarios import build_scenarios


def measure(fn, sc, repeats):
    problem = sc.problem()
    times = []
    for _ in range(repeats):
        res = fn(LocalGridClient(sc), problem)        
        times.append(res.elapsed)
    client = LocalGridClient(sc)                      
    tracemalloc.start()
    fn(client, problem)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return res, statistics.median(times), peak


def run_all(sizes, repeats):
    rows = []
    for sc in build_scenarios(sizes):
        group = []
        for algo, fn in ALGORITHMS.items():
            res, t, peak = measure(fn, sc, repeats)
            group.append({
                "scenario": sc.name, "size": sc.size, "conn": sc.connectivity,
                "algo": algo, "found": res.found,
                "steps": max(len(res.path) - 1, 0),
                "cost": round(res.cost, 2) if res.found else float("nan"),
                "expanded": res.expanded, "api_calls": res.api_calls,
                "time_ms": round(t * 1000, 3), "peak_kib": round(peak / 1024, 1)})
        best = min((g["cost"] for g in group if g["found"]), default=None)
        for g in group:
            g["cost_ratio"] = round(g["cost"] / best, 2) if g["found"] and best else ""
        rows += group
    return rows


def save_csv(rows, path):
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def print_report(rows):
    key = lambda r: (r["size"], r["conn"], r["scenario"])
    head = f"{'algo':<7}{'pas':>5}{'coût':>9}{'ratio':>7}{'dév.':>7}{'appels':>8}{'ms':>9}{'KiB':>9}"
    for (size, conn, name), grp in groupby(rows, key=key):
        print(f"\n== {name} | {size}x{size} | connectivité {conn} ==")
        print(head)
        for r in grp:
            print(f"{r['algo']:<7}{r['steps']:>5}{r['cost']:>9}{r['cost_ratio']:>7}"
                  f"{r['expanded']:>7}{r['api_calls']:>8}{r['time_ms']:>9}{r['peak_kib']:>9}")

    print("\n== MOYENNES PAR ALGO ==")
    print(f"{'algo':<7}{'conn':>5}{'ratio':>8}{'dév.':>8}{'ms (méd.)':>11}{'KiB':>9}")
    for algo in ALGORITHMS:
        for conn in (4, 8):
            sel = [r for r in rows if r["algo"] == algo and r["conn"] == conn
                   and r["cost_ratio"] != ""]
            print(f"{algo:<7}{conn:>5}"
                  f"{statistics.mean(r['cost_ratio'] for r in sel):>8.2f}"
                  f"{statistics.mean(r['expanded'] for r in sel):>8.0f}"
                  f"{statistics.median(r['time_ms'] for r in sel):>11.2f}"
                  f"{statistics.mean(r['peak_kib'] for r in sel):>9.1f}")