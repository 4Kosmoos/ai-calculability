from abc import ABC, abstractmethod
from collections import deque

Pose = tuple[int, int]


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
