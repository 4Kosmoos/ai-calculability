import random
from dataclasses import dataclass

from ..models import Node, Problem

WALL = 100               
LIGHT, HEAVY = (2, 3), (5, 9)


@dataclass(frozen=True)
class Scenario:
    name: str
    size: int
    connectivity: int
    obstacles: dict       
    start: Node = (0, 0)

    @property
    def target(self) -> Node:
        return (self.size - 1, self.size - 1)

    def problem(self) -> Problem:
        return Problem("robot", self.start, self.target, 1e12,
                       self.size, self.connectivity)

    def init_payload(self) -> dict:
        return {"size": self.size, "connectivity": self.connectivity,
                "agents": ["robot"],
                "obstacles": [{"node": list(k), "weight": w}
                              for k, w in self.obstacles.items()],
                "mission": {"start": list(self.start), "target": list(self.target),
                            "threshold": 1e9, "agent": "robot"}}


def random_cells(n, density, weights, seed=42):
    rnd = random.Random(seed)        
    cells = [(r, c) for r in range(n) for c in range(n)]
    return {cell: rnd.randint(*weights)
            for cell in rnd.sample(cells, int(density * n * n))}


def swamp(n, w=4):
    lo, hi = n // 4, 3 * n // 4
    return {(r, c): w for r in range(lo, hi + 1) for c in range(lo, hi + 1)}


def u_shape(r0, r1, c0, c1, w=WALL):
    cells = {}
    for r in range(r0, r1 + 1):
        cells[(r, c0)] = w
        cells[(r, c1)] = w
    for c in range(c0, c1 + 1):
        cells[(r1, c)] = w
    return cells


def wall_col(n, col, gap_rows=(), w=WALL):
    return {(r, col): w for r in range(n) if r not in gap_rows}


def serpentine(n, w=WALL):
    cells = {}
    for i, r in enumerate((n // 4, n // 2, 3 * n // 4)):
        gap = n - 1 if i % 2 == 0 else 0    
        cells.update({(r, c): w for c in range(n) if c != gap})
    return cells


def build_scenarios(sizes):
    out = []
    for n in sizes:
        layouts = {
            "empty": {},
            "random_light": random_cells(n, 0.2, LIGHT),
            "random_heavy": random_cells(n, 0.3, HEAVY),
            "swamp": swamp(n),
            "u_trap": u_shape(n // 4, 3 * n // 4, n // 4, 3 * n // 4),
            "wall_full": wall_col(n, 3 * n // 4),
            "wall_gap": wall_col(n, n // 2, gap_rows=(0, 1)),
            "serpentine": serpentine(n),
            "drawing": {**u_shape(n // 4, 3 * n // 4, max(1, n // 8), n // 2),
                        **wall_col(n, 3 * n // 4)},
        }
        for conn in (4, 8):
            for name, obs in layouts.items():
                keep = {k: v for k, v in obs.items()
                        if k not in ((0, 0), (n - 1, n - 1))}  
                out.append(Scenario(name, n, conn, keep))
    return out