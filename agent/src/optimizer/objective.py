"""Fonction objectif pour optimiser le poids w de AStarWeighted.

F = a*(coût/coût_ref) + b*(temps/temps_ref) + c*(mémoire/mémoire_ref), avec a + b + c = 1.

Chaque terme est un ratio par rapport à la référence (A* classique, w = 1) : sans unité,
donc a, b et c sont de vraies parts du score. F(w=1) = 1 ; F < 1 = mieux qu'A* classique.
Mesures : coût = somme des coûts d'arêtes du chemin, temps = secondes (médiane sur `repeats`
exécutions), mémoire = taille max du tas (nombre d'éléments).
"""
import contextlib
import io
import statistics

from agent import Agent
from strategies import AStarWeighted, euclidean

WEIGHTS = (0.45, 0.45, 0.10)  # coût, temps, mémoire


def evaluate(w: float, heuristic=euclidean, repeats: int = 3) -> dict:
    """Planifie avec AStarWeighted(heuristic, w) (sans déplacer le robot) et renvoie les métriques."""
    runs = []
    for _ in range(repeats):
        agent = Agent("robot", AStarWeighted(heuristic, w))
        with contextlib.redirect_stdout(io.StringIO()):
            agent.plan()
        runs.append(agent.metrics)
    first = runs[0]  # coût, mémoire et nœuds développés sont déterministes
    return {
        "w": w,
        "cost": first["cost"],
        "memory": first["memory"],
        "expanded": first["expanded"],
        "time": statistics.median(run["time"] for run in runs),
    }


def ratios(metrics: dict, reference: dict) -> dict:
    """Chaque métrique divisée par sa valeur de référence."""
    return {k: metrics[k] / reference[k] for k in ("cost", "time", "memory")}


def fitness(metrics: dict, reference: dict, weights=WEIGHTS) -> float:
    """F = a*coût_rel + b*temps_rel + c*mémoire_rel ; inf si aucun chemin n'a été trouvé."""
    if metrics["cost"] is None:
        return float("inf")
    a, b, c = weights
    r = ratios(metrics, reference)
    return a * r["cost"] + b * r["time"] + c * r["memory"]
