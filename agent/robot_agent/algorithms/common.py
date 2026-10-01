from time import perf_counter

from ..client import GridClient
from ..models import Node, SearchResult


def finish(algo: str, client: GridClient, parent: dict[Node, Node | None],
           target: Node, found: bool, expanded: int,
           t0: float, calls0: int) -> SearchResult:
    path: list[Node] = []
    cost = 0.0
    if found:
        node = target
        while node is not None:        
            path.append(node)
            node = parent[node]
        path.reverse()
        cost = sum(client.cost(u, v) for u, v in zip(path, path[1:]))
    return SearchResult(algo, found, path, cost, expanded,
                        client.api_calls - calls0, perf_counter() - t0)