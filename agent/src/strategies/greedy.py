import heapq

from .base import SearchStrategy
from .heuristics import manhattan


class GreedyBestFirst(SearchStrategy):

    def __init__(self, heuristic=manhattan):
        self.heuristic = heuristic

    def search(self, start, target, neighbors):
        print("Start GreedyBestFirst")
        parent = {start: None}
        frontier = [(self.heuristic(start, target), start)]
        print(f"parent : {parent}")
        print(f"frontier : {frontier}")
        while frontier:
            print("-- new tour --")
            estimate, node = heapq.heappop(frontier)
            print(f"-- node : {node} (estimate = {estimate})")
            if node == target:
                path = []
                while node is not None:
                    path.append(node)
                    node = parent[node]
                return path[::-1]
            for nxt in neighbors(node):
                if nxt not in parent:
                    parent[nxt] = node
                    heapq.heappush(frontier, (self.heuristic(nxt, target), nxt))
            print(f"-- frontier size : {len(frontier)}")
        return []
