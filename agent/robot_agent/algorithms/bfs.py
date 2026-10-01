from collections import deque
from time import perf_counter

from ..client import GridClient
from ..models import Problem, SearchResult
from .common import finish


def bfs(client: GridClient, problem: Problem) -> SearchResult:
    """FIFO: O(V + E)."""
    t0, calls0 = perf_counter(), client.api_calls
    start, target = problem.start, problem.target

    frontier = deque([start])
    parent = {start: None}
    expanded, found = 0, False

    while frontier and not found:
        node = frontier.popleft()
        expanded += 1
        for nxt, _cost in client.neighbors(node):
            if nxt in parent:
                continue
            parent[nxt] = node
            if nxt == target:
                found = True
                break
            frontier.append(nxt)

    return finish("bfs", client, parent, target, found, expanded, t0, calls0)