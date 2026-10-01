from robot_agent.algorithms.bfs import bfs
from robot_agent.models import Problem


class FakeClient:
    """Grid 4-neighbors n x n without api, algorithm test"""
    def __init__(self, n):
        self.n, self.api_calls = n, 0

    def neighbors(self, node):
        r, c = node
        out = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
               if 0 <= r + dr < self.n and 0 <= c + dc < self.n]
        return [(v, 1.0) for v in out]

    def cost(self, u, v):
        return 1.0


def test_bfs_shortest_path_4_connectivity():
    p = Problem("robot", (0, 0), (3, 4), 100.0, 5, 4)
    res = bfs(FakeClient(5), p)
    assert res.found
    assert len(res.path) - 1 == 7       # Manhattan distance
    assert res.path[0] == (0, 0) and res.path[-1] == (3, 4)