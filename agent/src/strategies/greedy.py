import heapq

from .base import SearchStrategy
from .heuristics import manhattan


class GreedyBestFirst(SearchStrategy):

    def __init__(self, heuristic=manhattan):
        self.heuristic = heuristic

    def search(self, start, target, neighbors):
        parent = {start: None}
        frontier = [(self.heuristic(start, target), start)]
        peak = 1
        while frontier:
            _, node = heapq.heappop(frontier)
            if node == target:
                self._record(len(parent), peak)
                path = []
                while node is not None:
                    path.append(node)
                    node = parent[node]
                return path[::-1]
            for nxt in neighbors(node):
                if nxt not in parent:
                    parent[nxt] = node
                    heapq.heappush(frontier, (self.heuristic(nxt, target), nxt))
            peak = max(peak, len(frontier))
        self._record(len(parent), peak)
        return []