"""Compare toutes les stratégies sur la mission courante (planification seule, sans déplacement)."""
import contextlib
import io

from agent import Agent
from strategies import BFS, DFS, GreedyBestFirst, Dijkstra, AStar, manhattan, euclidean

STRATEGIES = [
    ("BFS", BFS()),
    ("DFS", DFS()),
    ("Greedy (manhattan)", GreedyBestFirst(manhattan)),
    ("Dijkstra", Dijkstra()),
    ("A* (euclidean)", AStar(euclidean)),
    ("A* (manhattan)", AStar(manhattan)),
]

if __name__ == "__main__":
    rows = []
    for name, strategy in STRATEGIES:
        agent = Agent("robot", strategy)
        with contextlib.redirect_stdout(io.StringIO()):
            agent.plan()
        rows.append((name, agent.metrics))
    best = min(metrics["cost"] for _, metrics in rows if metrics["cost"] is not None)
    print(f"{'algo':<20}{'nœuds dév.':>11}{'temps (ms)':>12}{'pas':>5}{'coût':>8}  optimal")
    for name, metrics in sorted(rows, key=lambda entry: (entry[1]["cost"] is None, entry[1]["cost"], entry[1]["expanded"])):
        cost = "-" if metrics["cost"] is None else f"{metrics['cost']:.1f}"
        opt = "oui" if metrics["cost"] is not None and abs(metrics["cost"] - best) < 1e-9 else "non"
        print(f"{name:<20}{metrics['expanded']:>11}{metrics['time']*1000:>12.1f}{metrics['steps']:>5}{cost:>8}  {opt}")
