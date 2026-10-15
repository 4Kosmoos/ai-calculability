"""Greedy Best-First Search controller for the grid API."""
# Imports pour la file de priorité, les requêtes HTTP et l'estimation géométrique.
import argparse
import heapq
import itertools
import json
import math
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

# Type représentant une case par son indice de ligne et de colonne.
Pose = tuple[int, int]


class GreedyAgent:
	"""Find a heuristic-guided path and send moves to the running grid API."""

	# Garde en mémoire l'URL, le nom du robot et le délai des échanges avec l'API.
	def __init__(self, base_url: str = "http://127.0.0.1:8000",
				 agent_name: str = "robot", timeout: float = 5):
		self.base_url = base_url.rstrip("/")
		self.agent_name = agent_name
		self.timeout = timeout

	# Envoie une requête JSON à l'API et convertit les erreurs de réseau en erreurs explicites.
	def _request(self, path: str, payload: dict | None = None) -> dict:
		# Encode les données à envoyer, lorsqu'elles sont présentes.
		data = json.dumps(payload).encode("utf-8") if payload is not None else None
		request = Request(
			f"{self.base_url}{path}",
			data=data,
			headers={"Content-Type": "application/json"} if data is not None else {},
		)
		# Lit la réponse ou signale une erreur HTTP ou réseau.
		try:
			with urlopen(request, timeout=self.timeout) as response:
				return json.loads(response.read().decode("utf-8"))
		except HTTPError as error:
			try:
				detail = json.loads(error.read().decode("utf-8")).get("error", str(error))
			except (ValueError, AttributeError):
				detail = str(error)
			raise RuntimeError(f"API error {error.code}: {detail}") from error
		except URLError as error:
			raise RuntimeError(
				f"cannot connect to grid API at {self.base_url}: {error.reason}"
			) from error

	# Récupère la mission et utilise Greedy Best-First Search pour choisir le chemin.
	def find_path(self) -> list[Pose]:
		"""Return a path guided by straight-line distance to the target."""
		# Vérifie la présence de la mission, son état et l'identité de l'agent assigné.
		state = self._request("/state")
		mission = state.get("mission")
		if mission is None:
			raise ValueError("there is no active mission")
		if mission["status"] != "running":
			raise ValueError(f"mission is not running: {mission['message']}")
		if mission["agent"] != self.agent_name:
			raise ValueError(
				f"mission belongs to {mission['agent']!r}, not {self.agent_name!r}"
			)

		# Détermine la position de départ et la cible à partir de l'état renvoyé par l'API.
		agents = {agent["name"]: agent for agent in state["agents"]}
		if self.agent_name not in agents:
			raise ValueError(f"agent {self.agent_name!r} is not registered in the grid")
		start = tuple(agents[self.agent_name]["pose"])
		target = tuple(mission["target"])

		# Estime la distance en ligne droite entre une case et la cible.
		def heuristic(node: Pose) -> float:
			return math.hypot(target[0] - node[0], target[1] - node[1])

		# Trie les cases à explorer selon l'heuristique et mémorise leurs prédécesseurs.
		def search(avoid_weighted: bool) -> list[Pose] | None:
			order = itertools.count()
			frontier = [(heuristic(start), next(order), start)]
			previous: dict[Pose, Pose | None] = {start: None}
			while frontier:
				_, _, current = heapq.heappop(frontier)
				if current == target:
					path = []
					while current is not None:
						path.append(current)
						current = previous[current]
					return list(reversed(path))

				# Récupère les voisins accessibles de la case la plus prometteuse.
				neighbors = self._request(
					f"/nodes/{current[0]}/{current[1]}/neighbors"
				)
				for info in neighbors:
					neighbor = tuple(info["node"])
					# Ignore les cases déjà découvertes et les obstacles au premier essai.
					if neighbor in previous:
						continue
					if avoid_weighted and info["obstacle_weight"] > 1 and neighbor != target:
						continue
					previous[neighbor] = current
					heapq.heappush(
						frontier, (heuristic(neighbor), next(order), neighbor)
					)
			return None

		# Tente d'abord d'éviter les obstacles pondérés, puis les accepte si aucun chemin n'existe.
		path = search(avoid_weighted=True) or search(avoid_weighted=False)
		if path is None:
			raise ValueError(f"no path from {start} to {target}")
		return path

	# Demande à l'API de déplacer l'agent sur chaque nœud du chemin.
	def run(self, path: list[Pose] | None = None) -> dict:
		"""Move the mission agent along the planned path and return its final response."""
		# Calcule le trajet automatiquement si l'appelant n'en fournit pas.
		path = path or self.find_path()
		result = {}
		name = quote(self.agent_name, safe="")
		# Arrête les déplacements si la mission échoue ou est accomplie.
		for node in path[1:]:
			result = self._request(
				f"/agents/{name}/move", {"to": list(node)}
			)
			mission = result.get("mission") or {}
			if mission.get("status") == "failed":
				raise RuntimeError(
					mission.get("message", "mission failed during Greedy Best-First Search")
				)
			if mission.get("status") == "success":
				break
		return result


# Lit les options CLI puis affiche le trajet ou exécute la mission.
def main() -> int:
	# Définit l'URL de l'API, l'agent à utiliser et le mode sans déplacement.
	parser = argparse.ArgumentParser(
		description="Drive a grid agent to its target with Greedy Best-First Search."
	)
	parser.add_argument("--url", default="http://127.0.0.1:8000", help="grid API base URL")
	parser.add_argument("--agent", default="robot", help="registered mission agent name")
	parser.add_argument("--dry-run", action="store_true", help="show the path without moving")
	args = parser.parse_args()

	# Calcule et affiche le chemin, puis exécute les mouvements si le mode simulation est désactivé.
	try:
		agent = GreedyAgent(args.url, args.agent)
		path = agent.find_path()
		print("Greedy Best-First Search path:", " -> ".join(map(str, path)))
		if args.dry_run:
			return 0
		result = agent.run(path)
		print(result.get("mission", {}).get("message", "Agent moved."))
		return 0
	except (RuntimeError, ValueError) as error:
		# Signale l'erreur sur stderr et renvoie un code d'échec.
		print(f"Greedy agent: {error}", file=sys.stderr)
		return 1


# Exécute main uniquement si le script est lancé directement.
if __name__ == "__main__":
	raise SystemExit(main())
