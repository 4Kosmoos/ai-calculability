from collections import deque
from time import perf_counter

from ..client import GridClient
from ..models import Problem, SearchResult

def bfs(client:GridClient, problem: Problem)-> SearchResult:
    t0 = perf_counter()
    calls0 = client.api_calls
    start, target = problem.start, problem.target
    
    frontier = deque([start]) # FIFO
    parent={start:None}
    expanded = 0
    found = False
    
    while frontier and not found:
        node = frontier.popleft()
        expanded += 1
        for nxt, _cost in client.neighbors(node):
            if nxt in parent:          # already viewed
                continue
            parent[nxt] = node
            if nxt == target:          
                found = True
                break
            frontier.append(nxt)

    path, cost = [], 0.0
    if found:
        node = target
        while node is not None:        # go to the target from the start 
            path.append(node)
            node = parent[node]
        path.reverse()
        cost = sum(client.cost(u, v) for u, v in zip(path, path[1:]))

    return SearchResult("bfs", found, path, cost, expanded,
                        client.api_calls - calls0, perf_counter() - t0)