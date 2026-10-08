from abc import ABC, abstractmethod
import heapq
import math
from collections import deque

Pose = tuple[int, int]


def manhattan(pose_a: Pose, pose_b: Pose) -> int:
    return abs(pose_a[0] - pose_b[0]) + abs(pose_a[1] - pose_b[1])


def euclidean(pose_a: Pose, pose_b: Pose) -> float:
    return math.hypot(pose_a[0] - pose_b[0], pose_a[1] - pose_b[1])


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


class Dijkstra(SearchStrategy):
    weighted = True

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


class AStar(SearchStrategy):
    weighted = True

    def __init__(self, heuristic=euclidean):
        self.heuristic = heuristic

    def search(self, start, target, neighbors):
        print("Start AStar")
        best_cost = {start: 0}
        parent = {start: None}
        frontier = [(self.heuristic(start, target), 0, start)]
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
                    heapq.heappush(frontier, (new_cost + self.heuristic(nxt, target), new_cost, nxt))
        return []
