from robot_agent.algorithms.dfs import dfs
from tests.test_bfs import FakeClient
from robot_agent.models import Problem


def test_dfs_finds_a_valid_path():
    p = Problem("robot", (0, 0), (3, 4), 100.0, 5, 4)
    res = dfs(FakeClient(5), p)
    assert res.found
    assert res.path[0] == (0, 0) and res.path[-1] == (3, 4)
    for (r1, c1), (r2, c2) in zip(res.path, res.path[1:]):
        assert abs(r1 - r2) + abs(c1 - c2) == 1    
    assert len(res.path) - 1 >= 7                  