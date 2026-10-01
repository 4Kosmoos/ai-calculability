from time import perf_counter

from ..client import GridClient
from ..models import Problem, SearchResult
from .common import finish


def dfs(client: GridClient, problem: Problem) -> SearchResult:
    """LIFO: O(V + E)."""
    t0, calls0 = perf_counter(), client.api_calls
    start, target = problem.start, problem.target

    stack = [(start, None)]      
    parent = {}                  
    expanded, found = 0, False

    while stack:
        node, par = stack.pop()
        if node in parent:        
            continue
        parent[node] = par
        expanded += 1
        if node == target:
            found = True
            break
        # reversed
        for nxt, _cost in reversed(client.neighbors(node)):
            if nxt not in parent:
                stack.append((nxt, node))

    return finish("dfs", client, parent, target, found, expanded, t0, calls0)