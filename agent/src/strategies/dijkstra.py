import heapq

from .base import SearchStrategy


class Dijkstra(SearchStrategy):
    uses_costs = True

    def search(self, start, target, neighbors):
        print("Start Dijkstra")
        dist = {start: 0}
        parent = {start: None}
        frontier = [(0, start)]
        while frontier:
            cost_so_far, node = heapq.heappop(frontier)
            if cost_so_far > dist[node]:
                continue
            print(f"-- node : {node} (cost_so_far = {cost_so_far})")
            if node == target:
                path = []
                print(f"-- dist : {len(dist)}")
                print(f"-- parent : {len(parent)}")
                print(f"-- frontier : {len(frontier)}")
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
        return []
