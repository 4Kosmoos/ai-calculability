from ..models import Node


def make_heuristic(connectivity: int, diagonal_weight: float = 1.5):
    diag = min(diagonal_weight, 2.0)

    def h(a: Node, b: Node) -> float:
        dr, dc = abs(a[0] - b[0]), abs(a[1] - b[1])
        if connectivity == 4:
            return float(dr + dc)
        small, big = min(dr, dc), max(dr, dc)
        return diag * small + (big - small)

    return h