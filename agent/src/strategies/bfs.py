from .base import SearchStrategy


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
