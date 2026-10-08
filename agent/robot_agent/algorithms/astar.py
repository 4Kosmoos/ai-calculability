import heapq
from itertools import count
from time import perf_counter

from ..client import GridClient
from ..models import Problem, SearchResult
from .common import finish
from .heuristics import make_heuristic


def astar(client: GridClient, problem: Problem, heuristic=None) -> SearchResult:
    t0, calls0 = perf_counter(), client.api_calls
    start, target = problem.start, problem.target
    h = heuristic or make_heuristic(problem.connectivity)

    tie = count()                    
    g = {start: 0.0}
    parent = {start: None}                   
    open_heap = [(h(start, target), next(tie), start)]
    closed: set = set()
    expanded, found = 0, False

    while open_heap:
        _f, _, node = heapq.heappop(open_heap)
        if node in closed:      
            continue
        if node == target:       
            found = True
            break
        closed.add(node)
        expanded += 1
        for nxt, cost in client.neighbors(node):
            if nxt in closed:
                continue
            new_g = g[node] + cost
            if new_g < g.get(nxt, float("inf")):   
                g[nxt] = new_g
                parent[nxt] = node
                heapq.heappush(open_heap, (new_g + h(nxt, target), next(tie), nxt))

    return finish("astar", client, parent, target, found, expanded, t0, calls0)