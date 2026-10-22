import heapq

from .base import SearchStrategy


class Dijkstra(SearchStrategy):
    uses_costs = True

    def search(self, start, target, neighbors):
        dist = {start: 0}
        parent = {start: None}
        frontier = [(0, start)]
        peak = 1
        while frontier:
            cost_so_far, node = heapq.heappop(frontier)
            if cost_so_far > dist[node]:
                continue
            if node == target:
                self._record(len(dist), peak)
                path = []
                while node is not None:
                    path.append(node)
                    node = parent[node]
                return path[::-1]
            for nxt, edge_cost in neighbors(node):
                new_cost = cost_so_far + edge_cost
                if new_cost < dist.get(nxt, float("inf")):
                    dist[nxt] = new_cost
                    parent[nxt] = node
                    heapq.heappush(frontier, (new_cost, nxt))
            peak = max(peak, len(frontier))
        self._record(len(dist), peak)
        return []