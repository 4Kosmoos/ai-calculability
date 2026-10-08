from .scenarios import Scenario

ORTHO = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))


class LocalGridClient:
    def __init__(self, sc: Scenario):
        self.n, self.conn, self.obs = sc.size, sc.connectivity, sc.obstacles
        self.api_calls = 0
        self._cache = {}

    def neighbors(self, node):
        if node not in self._cache:
            self.api_calls += 1                 
            r, c = node
            moves = [(d, 1.0) for d in ORTHO]
            if self.conn == 8:
                moves += [(d, 1.5) for d in DIAG]
            out = []
            for (dr, dc), w in moves:
                v = (r + dr, c + dc)
                if 0 <= v[0] < self.n and 0 <= v[1] < self.n:
                    out.append((v, w * self.obs.get(v, 1)))  
            out.sort()                       
            self._cache[node] = out
        return self._cache[node]
    
    def cost(self, u, v):
        return dict(self.neighbors(u))[v]

    def visited(self) -> set:
        return set(self._cache)