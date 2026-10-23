"""Trace la courbe F en fonction de w à partir de results.csv (écrit par optimize.py)."""
import argparse
import csv

import matplotlib.pyplot as plt


def load(path):
    with open(path, newline="") as f:
        rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
    return sorted(rows, key=lambda row: row["w"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="results.csv")
    parser.add_argument("--out", default="results.png")
    args = parser.parse_args()

    all_rows = load(args.csv)
    dijkstra = next((row for row in all_rows if row["w"] == 0), None)  # w = 0 : pas sur l'axe log
    rows = [row for row in all_rows if row["w"] > 0]
    ws = [row["w"] for row in rows]
    fs = [row["F"] for row in rows]
    best = min(rows, key=lambda row: row["F"])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ws, fs, "o-", label="F(w)")
    ax.axhline(1, color="gray", linestyle="--", label="A* classique (F = 1)")
    if dijkstra:
        ax.axhline(dijkstra["F"], color="green", linestyle=":", label=f"Dijkstra (w = 0) : F = {dijkstra['F']:.3f}")
    ax.plot(best["w"], best["F"], "r*", markersize=15, label=f"meilleur : w = {best['w']:g}, F = {best['F']:.3f}")
    ax.set_xscale("log")
    ax.set_xlabel("w (poids de l'heuristique, échelle log)")
    ax.set_ylabel("F (relatif à A* classique)")
    ax.set_title("Fonction objectif F en fonction de w")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(args.out, dpi=120)
    print(f"Graphique écrit dans {args.out}")
    plt.show()
