from collections import deque

from .base import SearchStrategy


class BFS(SearchStrategy):

    def search(self, start, target, neighbors):
        parent = {start: None}
        queue = deque([start])     
        peak = 1
        while queue:
            node = queue.popleft()
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
                    queue.append(nxt)
            peak = max(peak, len(queue))
        self._record(len(parent), peak)
        return []