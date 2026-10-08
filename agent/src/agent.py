"""Agent that talks to grid_api over HTTP and plans its path with a search strategy."""
import requests

from strategies import SearchStrategy

Pose = tuple[int, int]


class Agent:
    def __init__(self, agent_id: str, strategy: SearchStrategy,
                 url: str = "http://localhost:8000") -> None:
        self.agent_id = agent_id
        self.strategy = strategy
        self.url = url.rstrip("/")

    '''Méthode utilitaire pour les appel api'''
    def _call(self, method: str, path: str, body: dict | None = None):
        resp = requests.request(method, self.url + path, json=body, timeout=10)
        if not resp.ok:
            raise RuntimeError(resp.json().get("error", resp.text))
        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return resp.text

    '''Reset de la mission'''
    def reset_mission(self) -> None:
        m = self._call("GET", "/mission")
        self._call("POST", "/mission", {"start": m["start"], "target": m["target"],
                                        "threshold": m["threshold"], "agent": m["agent"]})

    '''Affiche la grid'''
    def viz(self) -> str:
        return self._call("GET", "/viz/grid")

    '''Renvoie la liste des adjacences'''
    def _neighbors(self, node: Pose) -> list[Pose]:
        r, c = node
        return [tuple(n["node"]) for n in self._call("GET", f"/nodes/{r}/{c}/neighbors")]

    '''Renvoie la liste des adjacences avec leur coût'''
    def _weighted_neighbors(self, node: Pose) -> list[tuple[Pose, float]]:
        r, c = node
        return [(tuple(n["node"]), n["cost"]) for n in self._call("GET", f"/nodes/{r}/{c}/neighbors")]

    '''Appel le calcul du chemin'''
    def plan(self) -> list[Pose]:
        mission = self._call("GET", "/mission")
        start, target = tuple(mission["start"]), tuple(mission["target"])
        neighbors = self._weighted_neighbors if getattr(self.strategy, "weighted", False) else self._neighbors
        return self.strategy.search(start, target, neighbors)

    '''Lance le calcul du chemin, appel l'action de grid et affiche le retour de l'api grid'''
    def run(self, verbose: bool = False) -> dict:
        path = self.plan()
        if not path:
            raise RuntimeError("no path found")
        print(f"[{self.agent_id}] path ({len(path) - 1} steps): {path}")
        result = None
        for node in path[1:]:
            result = self._call("POST", f"/agents/{self.agent_id}/move", {"to": list(node)})
            if verbose:
                print(f"--- step to {node} ---\n{self.viz()}")
            if result["mission"]["status"] != "running":
                break
        print(result["mission"]["message"])
        return result
