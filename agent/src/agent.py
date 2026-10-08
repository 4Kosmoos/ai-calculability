"""Agent that talks to grid_api over HTTP and plans its path with a search strategy."""
import time

import requests

from strategies import SearchStrategy

Pose = tuple[int, int]


class Agent:
    def __init__(self, agent_id: str, strategy: SearchStrategy,
                 url: str = "http://localhost:8000") -> None:
        self.agent_id = agent_id
        self.strategy = strategy
        self.url = url.rstrip("/")
        self.expanded = 0
        self._edge_cost: dict[tuple[Pose, Pose], float] = {}
        self.metrics: dict = {}

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
        mission = self._call("GET", "/mission")
        self._call("POST", "/mission", {"start": mission["start"], "target": mission["target"],
                                        "threshold": mission["threshold"], "agent": mission["agent"]})

    '''Affiche la grid'''
    def viz(self) -> str:
        return self._call("GET", "/viz/grid")

    '''Un appel api voisins : compte l'expansion et mémorise les coûts'''
    def _neighbor_info(self, node: Pose) -> list[tuple[Pose, float]]:
        row, col = node
        self.expanded += 1
        result = []
        for neighbor in self._call("GET", f"/nodes/{row}/{col}/neighbors"):
            nxt = tuple(neighbor["node"])
            self._edge_cost[(node, nxt)] = neighbor["cost"]
            result.append((nxt, neighbor["cost"]))
        return result

    '''Renvoie la liste des adjacences'''
    def _neighbors(self, node: Pose) -> list[Pose]:
        return [nxt for nxt, _ in self._neighbor_info(node)]

    '''Renvoie la liste des adjacences avec leur coût'''
    def _weighted_neighbors(self, node: Pose) -> list[tuple[Pose, float]]:
        return self._neighbor_info(node)

    '''Appel le calcul du chemin'''
    def plan(self) -> list[Pose]:
        mission = self._call("GET", "/mission")
        start, target = tuple(mission["start"]), tuple(mission["target"])
        neighbors = self._weighted_neighbors if getattr(self.strategy, "weighted", False) else self._neighbors
        self.expanded = 0
        self._edge_cost = {}
        t0 = time.perf_counter()
        path = self.strategy.search(start, target, neighbors)
        elapsed = time.perf_counter() - t0
        self.metrics = {
            "algo": type(self.strategy).__name__,
            "expanded": self.expanded,
            "time": elapsed,
            "steps": max(len(path) - 1, 0),
            "cost": sum(self._edge_cost[edge] for edge in zip(path, path[1:])) if path else None,
        }
        return path

    '''Lance le calcul du chemin, appel l'action de grid et affiche le retour de l'api grid'''
    def run(self, verbose: bool = False) -> dict:
        path = self.plan()
        if not path:
            raise RuntimeError("no path found")
        metrics = self.metrics
        print(f"[{metrics['algo']}] nœuds développés: {metrics['expanded']} | temps: {metrics['time']*1000:.1f} ms | "
              f"pas: {metrics['steps']} | coût: {metrics['cost']}")
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
