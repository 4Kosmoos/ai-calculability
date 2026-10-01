import requests

from .models import Node, Problem

class GridApiError(Exception):
    """Error from the api"""
    
class GridClient:
    def __init__(self, base_url="http://localhost:8000", timout=5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.api_calls = 0
        self._neighbors: dict[Node, list[tuple[Node, float]]] = {}
        
    def _request(self, method, path, **kwargs):
        resp = self.session.request(method, self.base_url + path, 
                                    timeout=self.timeout, **kwargs)
        self.api_calls += 1
        data = resp.json()
        if resp.status_code >= 400:
            raise GridApiError(f"{resp.status_code}: {data.get('error', data)}")
        return data
    
    def problem(self) -> Problem:
        s = self._request("GET", "state")
        m = s["mission"]
        if m is None:
            raise GridApiError("no mission: first do -> POST /init or POST /mission")
        return Problem(agent=m["agent"], start=tuple(m["start"]),
                       target=tuple(m["target"]), threshold=m["threshold"],
                       size=s["size"], connectivity=s["connectivity"])
        
    def reset_mission(self, p: Problem) -> None:
        """Start from the begining, nedeed between two runs."""
        self._request("POST", "/mission", json={
            "start": list(p.start), "target": list(p.target),
            "threshold": p.threshold, "agent": p.agent})
        self._neighbors.clear() 
    
    def neighbors(self, node: Node) -> list[tuple[Node, float]]:
        """Neighbors(node, cost). Cached"""
        if node not in self._neighbors:
            r, c = node
            data = self._request("GET", f"/nodes/{r}/{c}/neighbors")
            self._neighbors[node] = [(tuple(n["node"]), n["cost"]) for n in data]
        return self._neighbors[node]
    
    def cost(self, u: Node, v: Node) -> float:
        """Cost u -> v. u"""
        return dict(self.neighbors(u))[v]
    
    def move(self, agent: str, to: Node) -> dict:
        return self._request("POST", f"/agents/{agent}/move", json={"to": list(to)})
        