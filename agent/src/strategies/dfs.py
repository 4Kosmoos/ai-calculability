from .base import SearchStrategy


class DFS(SearchStrategy):

    def search(self, start, target, neighbors):
        parent = {start: None}
        stack = [start]
        peak = 1
        while stack:
            node = stack.pop()
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
                    stack.append(nxt)
            peak = max(peak, len(stack))
        self._record(len(parent), peak)
        return []