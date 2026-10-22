"""Compare toutes les stratégies sur la mission courante (planification seule, sans déplacement).

Contrainte F <= δ : un chemin est accepté si son coût F ne dépasse pas δ = K x coût de Dijkstra,
la référence (Dijkstra est certain de trouver l'optimal).
"""
import contextlib
import io

from agent import Agent
from strategies import BFS, DFS, GreedyBestFirst, Dijkstra, AStar, AStarWeighted, manhattan, euclidean

K = 1.10  # tolérance : jusqu'à 10 % au-dessus de l'optimal

STRATEGIES = [
    ("BFS", BFS()),
    ("DFS", DFS()),
    ("Greedy (manhattan)", GreedyBestFirst(manhattan)),
    ("Dijkstra", Dijkstra()),
    ("A* (euclidean)", AStar(euclidean)),
    ("A* (manhattan)", AStar(manhattan)),
    ("WA* (eucl., w=2)", AStarWeighted(euclidean, 2)),
    ("WA* (eucl., w=5)", AStarWeighted(euclidean, 5)),
]

if __name__ == "__main__":
    rows = []
    for name, strategy in STRATEGIES:
        agent = Agent("robot", strategy)
        with contextlib.redirect_stdout(io.StringIO()):
            agent.plan()
        rows.append((name, agent.metrics))
        if isinstance(strategy, Dijkstra):
            reference = agent.metrics["cost"]
    delta = K * reference
    print(f"Référence Dijkstra : coût {reference:.1f} -> delta = {K:.2f} x {reference:.1f} = {delta:.2f}\n")
    print(f"{'algo':<20}{'nœuds dév.':>11}{'temps (ms)':>12}{'pas':>5}{'coût':>8}  optimal  F<=delta")
    for name, metrics in sorted(rows, key=lambda entry: (entry[1]["cost"] is None, entry[1]["cost"], entry[1]["expanded"])):
        cost = "-" if metrics["cost"] is None else f"{metrics['cost']:.1f}"
        opt = "true" if metrics["cost"] is not None and abs(metrics["cost"] - reference) < 1e-9 else "false"
        accepted = "true" if metrics["cost"] is not None and metrics["cost"] <= delta + 1e-9 else "false"
        print(f"{name:<20}{metrics['expanded']:>11}{metrics['time']*1000:>12.1f}{metrics['steps']:>5}{cost:>8}  {opt:<7}  {accepted}")
