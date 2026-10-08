from abc import ABC, abstractmethod
import heapq
import math
from collections import deque

Pose = tuple[int, int]


def manhattan(a: Pose, b: Pose) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def euclidean(a: Pose, b: Pose) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


class SearchStrategy(ABC):
    @abstractmethod
    def search(self, start: Pose, target: Pose, neighbors) -> list[Pose]:
        pass


class BFS(SearchStrategy):

    def search(self, start, target, neighbors):
        print("Start BFS")
        parent = {start: None}
        queue = [start]
        print(f"parent : {parent}")
        print(f"queue : {queue}")
        while queue:
            print("---- new tour ----")
            node = queue.pop(0)
            print(f"-- node : {node}")
            if node == target:
                print(f"#### target trouvé ####")
                print(f"-- parent : {parent}")
                path = []
                while node is not None:
                    path.append(node)
                    node = parent[node]
                    print(f"-- path : {path}")
                return path[::-1]
            for nxt in neighbors(node):
                if nxt not in parent:
                    parent[nxt] = node
                    queue.append(nxt)
            print(f"-- parent size : {len(parent)}")
            print(f"-- queue size : {len(queue)}")
            print(f"-- queue : {queue}")
            
        return []

class DFS(SearchStrategy):

    def search(self, start, target, neighbors):
        print("Start DFS")
        parent = {start: None} 
        stack = [start]
        print(f"parent : {parent}")
        print(f"stack : {stack}")
        while stack:
            print("---- new tour ----")
            node = stack.pop()
            print(f"-- node : {node}")
            if node == target:
                print(f"#### target trouvé ####")
                print(f"-- parent : {parent}")
                path = []
                while node is not None:
                    path.append(node)
                    node = parent[node]
                    print(f"-- path : {path}")
                return path[::-1]
            for nxt in neighbors(node):
                if nxt not in parent:
                    parent[nxt] = node
                    stack.append(nxt)
            print(f"-- parent size : {len(parent)}")
            print(f"-- stack size : {len(stack)}")
            print(f"-- stack : {stack}")
        return []


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
            h, node = heapq.heappop(frontier)
            print(f"-- node : {node} (h = {h})")
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


class Dijkstra(SearchStrategy):
    weighted = True

    def search(self, start, target, neighbors):
        print("Start Dijkstra")
        dist = {start: 0}
        parent = {start: None}
        frontier = [(0, start)]
        while frontier:
            d, node = heapq.heappop(frontier)
            if d > dist[node]:
                continue
            print(f"-- node : {node} (cost = {d})")
            if node == target:
                path = []
                while node is not None:
                    path.append(node)
                    node = parent[node]
                return path[::-1]
            for nxt, cost in neighbors(node):
                nd = d + cost
                if nd < dist.get(nxt, float("inf")):
                    dist[nxt] = nd
                    parent[nxt] = node
                    heapq.heappush(frontier, (nd, nxt))
        return []


class AStar(SearchStrategy):
    weighted = True

    def __init__(self, heuristic=euclidean):
        self.heuristic = heuristic

    def search(self, start, target, neighbors):
        print("Start AStar")
        g = {start: 0}
        parent = {start: None}
        frontier = [(self.heuristic(start, target), 0, start)]
        while frontier:
            f, d, node = heapq.heappop(frontier)
            if d > g[node]:
                continue
            print(f"-- node : {node} (g = {d}, f = {f})")
            if node == target:
                path = []
                while node is not None:
                    path.append(node)
                    node = parent[node]
                return path[::-1]
            for nxt, cost in neighbors(node):
                nd = d + cost
                if nd < g.get(nxt, float("inf")):
                    g[nxt] = nd
                    parent[nxt] = node
                    heapq.heappush(frontier, (nd + self.heuristic(nxt, target), nd, nxt))
        return []
