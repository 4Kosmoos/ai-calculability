import heapq
from itertools import count
from time import perf_counter

from ..client import GridClient
from ..models import Problem, SearchResult
from .common import finish


def dijkstra(client: GridClient, problem: Problem) -> SearchResult:
    t0, calls0 = perf_counter(), client.api_calls
    start, target = problem.start, problem.target

    tie = count()                          
    dist = {start: 0.0}                    
    parent = {start: None}
    heap = [(0.0, next(tie), start)]
    done: set = set()                      
    expanded, found = 0, False

    while heap:
        d, _, node = heapq.heappop(heap)
        if node in done:                   
            continue
        if node == target:                
            found = True
            break
        done.add(node)
        expanded += 1
        for nxt, cost in client.neighbors(node):
            if nxt in done:
                continue
            new_d = d + cost
            if new_d < dist.get(nxt, float("inf")):     
                dist[nxt] = new_d
                parent[nxt] = node
                heapq.heappush(heap, (new_d, next(tie), nxt))

    return finish("dijkstra", client, parent, target, found, expanded, t0, calls0)