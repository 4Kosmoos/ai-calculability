import heapq

from .base import SearchStrategy
from .heuristics import euclidean

'''
    h admissible -> h <= poids reel

    heapq: f(n) = g(n) + h(n, sortie)

    A* = f(n) = g(n) + h(n)
    Djikstra = f(n) = g(n)
    Greedy = f(n) = h(n)
    A* pondérée = f(n) = g(n) + w * h(n)

'''


class AStar(SearchStrategy):
    uses_costs = True

    def __init__(self, heuristic=euclidean, weight=1.0):
        self.heuristic = heuristic
        self.weight = weight

    def search(self, start, target, neighbors):
        print("Start AStar")
        best_cost = {start: 0}
        parent = {start: None}
        frontier = [(self.weight * self.heuristic(start, target), 0, start)]
        while frontier:
            priority, cost_so_far, node = heapq.heappop(frontier)
            if cost_so_far > best_cost[node]:
                continue
            print(f"-- node : {node} (cost_so_far = {cost_so_far}, priority = {priority})")
            if node == target:
                print(f"-- best_cost : {len(best_cost)}")
                print(f"-- parent : {len(parent)}")
                print(f"-- frontier : {len(frontier)}")
                path = []
                while node is not None:
                    path.append(node)
                    node = parent[node]
                return path[::-1]
            for nxt, edge_cost in neighbors(node):
                new_cost = cost_so_far + edge_cost
                if new_cost < best_cost.get(nxt, float("inf")):
                    best_cost[nxt] = new_cost
                    parent[nxt] = node
                    heapq.heappush(frontier, (new_cost + self.weight * self.heuristic(nxt, target), new_cost, nxt))
        return []
