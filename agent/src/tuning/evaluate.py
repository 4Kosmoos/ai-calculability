"""Évalue une configuration (heuristique h, poids w) sur un scénario, sans réseau.
Mesure C' (coût), T' (temps), M' (mémoire) relatifs à Dijkstra, et les contraintes."""
import argparse
import heapq
import statistics
import tracemalloc
from dataclasses import dataclass
from time import perf_counter

from strategies import AStarWeighted, Dijkstra, chebyshev, euclidean, manhattan

from .scenarios import Scenario, build_scenarios

HEURISTICS = {"L1": manhattan, "L2": euclidean, "Linf": chebyshev}
ORTHO = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))
THRESHOLD_FACTOR = 1.5      # seuil de mission = 1.5 x coût optimal (si le scénario n'en fixe pas)
K_QUALITY = 1.25            # contrainte de qualité: coût <= k x coût optimal
EPS = 1e-9


class LocalGrid:
    """Mêmes règles de coût que grid_api, sans HTTP. Compte les nœuds développés."""

    def __init__(self, sc: Scenario):
        self.n, self.conn, self.obs = sc.size, sc.connectivity, sc.obstacles
        self.expanded = 0

    def adjacent(self, node):
        r, c = node
        out = []
        for dr, dc in ORTHO + (DIAG if self.conn == 8 else ()):
            v = (r + dr, c + dc)
            if 0 <= v[0] < self.n and 0 <= v[1] < self.n:
                out.append(v)
        return sorted(out)

    def edge_cost(self, u, v):
        base = 1.0 if (u[0] == v[0] or u[1] == v[1]) else 1.5
        return base * self.obs.get(v, 1)

    def neighbors_cost(self, node):
        self.expanded += 1
        return [(v, self.edge_cost(node, v)) for v in self.adjacent(node)]

    def neighbors(self, node):
        return [v for v, _ in self.neighbors_cost(node)]

    def path_cost(self, path):
        return sum(self.edge_cost(u, v) for u, v in zip(path, path[1:]))

    def for_strategy(self, strategy):
        """Même choix que Agent.plan: avec ou sans coûts selon uses_costs."""
        return self.neighbors_cost if getattr(strategy, "uses_costs", False) else self.neighbors


def cost_to_go(sc: Scenario) -> dict:
    """Coût optimal exact de chaque case vers la cible (Dijkstra inversé)."""
    g = LocalGrid(sc)
    dist = {sc.target: 0.0}
    heap = [(0.0, sc.target)]
    while heap:
        d, v = heapq.heappop(heap)
        if d > dist[v]:
            continue
        for u in g.adjacent(v):
            nd = d + g.edge_cost(u, v)          # coût du déplacement u -> v
            if nd < dist.get(u, float("inf")):
                dist[u] = nd
                heapq.heappush(heap, (nd, u))
    return dist


@dataclass(frozen=True)
class Raw:
    path: list
    cost: float
    expanded: int
    time_s: float
    peak_bytes: int
    stats: dict


def measure(sc: Scenario, strategy, repeats: int = 5) -> Raw:
    times = []
    for _ in range(repeats):                    # temps: médiane, sans suivi mémoire
        grid = LocalGrid(sc)
        t0 = perf_counter()
        path = strategy.search(sc.start, sc.target, grid.for_strategy(strategy))
        times.append(perf_counter() - t0)
    grid = LocalGrid(sc)                        # mémoire: run séparé (tracemalloc ralentit)
    fn = grid.for_strategy(strategy)
    tracemalloc.start()
    strategy.search(sc.start, sc.target, fn)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    cost = grid.path_cost(path) if path else float("inf")
    return Raw(path, cost, grid.expanded, statistics.median(times), peak, dict(strategy.stats or {}))


@dataclass(frozen=True)
class Reference:
    cost: float
    time_s: float
    peak_bytes: int
    to_go: dict


@dataclass(frozen=True)
class Evaluation:
    scenario: str
    heuristic: str
    w: float
    found: bool
    admissible: bool
    feasible: bool          # coût < seuil de la mission
    within_k: bool          # coût <= K x optimal
    cost: float
    steps: int
    expanded: int
    c_ratio: float
    t_ratio: float
    m_ratio: float
    time_ms: float
    peak_kib: float
    stored: int
    peak_frontier: int
    threshold: float


class Evaluator:
    def __init__(self, repeats: int = 5, k: float = K_QUALITY):
        self.repeats, self.k = repeats, k
        self._refs: dict[str, Reference] = {}
        self._adm: dict[tuple, bool] = {}

    def reference(self, sc: Scenario) -> Reference:
        if sc.key not in self._refs:
            raw = measure(sc, Dijkstra(), self.repeats)
            to_go = cost_to_go(sc)
            if abs(raw.cost - to_go[sc.start]) > 1e-6:       # garde-fou sur Dijkstra 
                raise RuntimeError(f"{sc.key}: Dijkstra={raw.cost} != exact={to_go[sc.start]}")
            self._refs[sc.key] = Reference(raw.cost, raw.time_s, raw.peak_bytes, to_go)
        return self._refs[sc.key]

    def admissible(self, sc: Scenario, h_name: str) -> bool:
        key = (sc.key, h_name)
        if key not in self._adm:
            h, to_go = HEURISTICS[h_name], self.reference(sc).to_go
            self._adm[key] = all(h(u, sc.target) <= d + EPS for u, d in to_go.items())
        return self._adm[key]

    def threshold(self, sc: Scenario) -> float:
        return sc.threshold if sc.threshold is not None else THRESHOLD_FACTOR * self.reference(sc).cost

    def evaluate(self, sc: Scenario, h_name: str, w: float) -> Evaluation:
        ref = self.reference(sc)
        raw = measure(sc, AStarWeighted(HEURISTICS[h_name], w), self.repeats)
        found = bool(raw.path)
        thr = self.threshold(sc)
        return Evaluation(
            scenario=sc.key, heuristic=h_name, w=w, found=found,
            admissible=self.admissible(sc, h_name),
            feasible=found and raw.cost < thr,                # la mission échoue dès cost >= seuil
            within_k=found and raw.cost <= self.k * ref.cost + EPS,
            cost=round(raw.cost, 3), steps=max(len(raw.path) - 1, 0), expanded=raw.expanded,
            c_ratio=round(raw.cost / ref.cost, 4),
            t_ratio=round(raw.time_s / ref.time_s, 3),
            m_ratio=round(raw.peak_bytes / ref.peak_bytes, 3),
            time_ms=round(raw.time_s * 1000, 3), peak_kib=round(raw.peak_bytes / 1024, 1),
            stored=raw.stats.get("stored", 0), peak_frontier=raw.stats.get("peak_frontier", 0),
            threshold=round(thr, 2))


def main():
    ap = argparse.ArgumentParser(prog="tuning.evaluate")
    ap.add_argument("--scenario", default="drawing-20-c8")
    ap.add_argument("--w", type=float, nargs="+", default=[1, 2, 5])
    ap.add_argument("--repeats", type=int, default=5)
    args = ap.parse_args()

    sc = {s.key: s for s in build_scenarios()}[args.scenario]
    ev = Evaluator(repeats=args.repeats)
    ref = ev.reference(sc)
    print(f"== {sc.key} | C*={ref.cost:g} | seuil={ev.threshold(sc):g} ==")
    print(f"{'h':<5}{'w':>5}{'adm':>5}{'faisable':>9}{'<=k':>5}{'coût':>8}{'C':>7}{'T':>7}{'M':>7}{'dév.':>6}")
    for h_name in HEURISTICS:
        for w in args.w:
            e = ev.evaluate(sc, h_name, w)
            print(f"{h_name:<5}{w:>5g}{'oui' if e.admissible else 'NON':>5}"
                  f"{'oui' if e.feasible else 'non':>9}{'oui' if e.within_k else 'non':>5}"
                  f"{e.cost:>8g}{e.c_ratio:>7.2f}{e.t_ratio:>7.2f}{e.m_ratio:>7.2f}{e.expanded:>6}")


if __name__ == "__main__":
    main()