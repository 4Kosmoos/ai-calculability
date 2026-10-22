"""Scénarios de test pour le réglage de (w, h).
Un scénario = une grille (taille, connectivité, obstacles pondérés) + une mission A -> B.
Format compatible avec POST /init de grid_api."""
import argparse
import random
from dataclasses import dataclass

Node = tuple[int, int]

W_MED, W_HIGH = 5, 8        
W_WALL = 30                 # franchissable mais très cher
DEFAULT_THRESHOLD = 50      # seuil du default.json


@dataclass(frozen=True)
class Scenario:
    name: str
    size: int
    connectivity: int
    obstacles: dict                      
    start: Node = (0, 0)
    threshold: float | None = None        

    @property
    def target(self) -> Node:
        return (self.size - 1, self.size - 1)

    @property
    def key(self) -> str:
        return f"{self.name}-{self.size}-c{self.connectivity}"

    def validate(self) -> None:
        n = self.size
        if self.connectivity not in (4, 8):
            raise ValueError(f"{self.key}: connectivité invalide")
        for (r, c), w in self.obstacles.items():
            if not (0 <= r < n and 0 <= c < n):
                raise ValueError(f"{self.key}: obstacle hors grille {(r, c)}")
            if not isinstance(w, int) or isinstance(w, bool) or w <= 1:
                raise ValueError(f"{self.key}: poids invalide en {(r, c)}: {w!r}")
        if self.start == self.target:
            raise ValueError(f"{self.key}: départ == arrivée")
        if self.start in self.obstacles or self.target in self.obstacles:
            raise ValueError(f"{self.key}: départ ou arrivée sur un obstacle")

    def init_payload(self, agent: str = "robot") -> dict:
        thr = self.threshold if self.threshold is not None else 1e9
        return {"size": self.size, "connectivity": self.connectivity, "agents": [agent],
                "obstacles": [{"node": list(k), "weight": w}
                              for k, w in sorted(self.obstacles.items())],
                "mission": {"start": list(self.start), "target": list(self.target),
                            "threshold": thr, "agent": agent}}

    def render(self) -> str:
        rows = []
        for r in range(self.size):
            line = []
            for c in range(self.size):
                node = (r, c)
                if node == self.start:
                    ch = "S"
                elif node == self.target:
                    ch = "E"
                else:
                    w = self.obstacles.get(node, 1)
                    ch = "." if w == 1 else (str(w) if w < 10 else "#")
                line.append(ch)
            rows.append(" ".join(line))
        return "\n".join(rows)


def random_cells(n, density, weights, seed=42):
    rnd = random.Random(seed)
    cells = [(r, c) for r in range(n) for c in range(n)]
    return {cell: rnd.randint(*weights) for cell in rnd.sample(cells, int(density * n * n))}


def swamp(n, w=3):
    lo, hi = n // 4, 3 * n // 4
    return {(r, c): w for r in range(lo, hi + 1) for c in range(lo, hi + 1)}


def u_shape(r0, r1, c0, c1, w=W_WALL):
    cells = {}
    for r in range(r0, r1 + 1):
        cells[(r, c0)] = w
        cells[(r, c1)] = w
    for c in range(c0, c1 + 1):
        cells[(r1, c)] = w
    return cells


def wall_col(n, col, gap_rows=(), w=W_WALL):
    return {(r, col): w for r in range(n) if r not in gap_rows}


def serpentine(n, w=W_WALL):
    cells = {}
    for i, r in enumerate((n // 4, n // 2, 3 * n // 4)):
        gap = n - 1 if i % 2 == 0 else 0
        cells.update({(r, c): w for c in range(n) if c != gap})
    return cells


DEFAULT_8 = {**{p: W_MED for p in [(0, 5), (0, 6), (0, 7), (1, 5), (1, 6), (1, 7), (2, 6),
                                   (5, 0), (5, 1), (6, 0), (6, 1), (7, 0), (7, 1), (6, 2)]},
             **{p: W_HIGH for p in [(2, 2), (2, 3), (2, 4), (3, 2), (4, 2), (5, 2), (5, 3),
                                    (5, 4), (4, 5), (3, 5), (2, 5)]}}


def layouts(n: int) -> dict:
    return {
        "empty": {},
        "random_light": random_cells(n, 0.2, (2, 3)),
        "random_heavy": random_cells(n, 0.3, (W_MED, W_HIGH)),
        "swamp": swamp(n),
        "u_trap": u_shape(n // 4, 3 * n // 4, n // 4, 3 * n // 4),
        "wall_full": wall_col(n, 3 * n // 4),
        "wall_gap": wall_col(n, n // 2, gap_rows=(0, 1)),
        "serpentine": serpentine(n),
        "drawing": {**u_shape(n // 4, 3 * n // 4, max(1, n // 8), n // 2),
                    **wall_col(n, 3 * n // 4)},
    }


def build_scenarios(sizes=(20, 40), include_default=True) -> list[Scenario]:
    out = []
    if include_default:
        for conn in (4, 8):
            thr = DEFAULT_THRESHOLD if conn == 8 else None
            out.append(Scenario("default", 8, conn, dict(DEFAULT_8), threshold=thr))
    for n in sizes:
        for conn in (4, 8):
            for name, obs in layouts(n).items():
                free = {k: v for k, v in obs.items() if k not in ((0, 0), (n - 1, n - 1))}
                out.append(Scenario(name, n, conn, free))
    for s in out:
        s.validate()
    return out


def main():
    ap = argparse.ArgumentParser(prog="tuning.scenarios")
    ap.add_argument("--sizes", type=int, nargs="+", default=[20, 40])
    ap.add_argument("--show", help="clé d'un scénario, ex: drawing-20-c8")
    ap.add_argument("--push", help="envoie ce scénario à grid_api (POST /init)")
    ap.add_argument("--url", default="http://localhost:8000")
    args = ap.parse_args()
    scenarios = {s.key: s for s in build_scenarios(args.sizes)}
    if args.show:
        print(scenarios[args.show].render())
    elif args.push:
        import requests
        r = requests.post(args.url + "/init", json=scenarios[args.push].init_payload(), timeout=10)
        print(r.status_code, r.text[:200])
    else:
        print(f"{len(scenarios)} scénarios")
        for key, s in scenarios.items():
            print(f"{key:<28}{len(s.obstacles):>5} cases pondérées")


if __name__ == "__main__":
    main()