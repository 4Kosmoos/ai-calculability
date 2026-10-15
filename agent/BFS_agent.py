"""BFS controller that drives an agent through the grid API."""
# Imports pour les arguments de commande, la file BFS, le JSON et les échanges HTTP.
import argparse
from collections import deque
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

# Une position de la grille est un couple (ligne, colonne).
Pose = tuple[int, int]


class BFSAgent:
	"""Find a BFS path and send moves to the running grid API."""

	# Mémorise l'adresse de l'API, le nom du robot et le délai maximal des requêtes.
	def __init__(self, base_url: str = "http://127.0.0.1:8000",
				 agent_name: str = "robot", timeout: float = 5):
		self.base_url = base_url.rstrip("/")
		self.agent_name = agent_name
		self.timeout = timeout

	# Envoie une requête JSON à l'API et convertit les erreurs réseau en erreurs explicites.
	def _request(self, path: str, payload: dict | None = None) -> dict:
		# Prépare le corps de la requête uniquement lorsqu'une donnée doit être envoyée.
		data = json.dumps(payload).encode("utf-8") if payload is not None else None
		request = Request(
			f"{self.base_url}{path}",
			data=data,
			headers={"Content-Type": "application/json"} if data is not None else {},
		)
		# Lit la réponse de l'API et traduit les erreurs HTTP ou de connexion.
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
			raise RuntimeError(f"cannot connect to grid API at {self.base_url}: {error.reason}") from error

	# Lit la mission puis cherche un chemin avec la recherche en largeur (BFS).
	def find_path(self) -> list[Pose]:
		"""Return a path with the fewest moves; cell weights do not affect the search."""
		# Vérifie que la mission existe, est active et appartient à cet agent.
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

		# Récupère les positions de départ et d'arrivée à partir de l'état de la grille.
		agents = {agent["name"]: agent for agent in state["agents"]}
		if self.agent_name not in agents:
			raise ValueError(f"agent {self.agent_name!r} is not registered in the grid")
		start = tuple(agents[self.agent_name]["pose"])
		target = tuple(mission["target"])

		# Explore les cases par couches; les coûts et poids renvoyés par l'API sont ignorés.
		frontier = deque([start])
		previous: dict[Pose, Pose | None] = {start: None}
		while frontier:
			current = frontier.popleft()
			if current == target:
				path = []
				while current is not None:
					path.append(current)
					current = previous[current]
				return list(reversed(path))

			# Récupère les positions voisines; seul leur emplacement est utilisé par BFS.
			neighbors = self._request(f"/nodes/{current[0]}/{current[1]}/neighbors")
			for info in neighbors:
				neighbor = tuple(info["node"])
				# Ignore uniquement les cases déjà découvertes, sans tester leur poids.
				if neighbor in previous:
					continue
				previous[neighbor] = current
				frontier.append(neighbor)

		# Si la file est vide, aucune route ne relie le départ à la cible.
		raise ValueError(f"no path from {start} to {target}")

	# Envoie au serveur les déplacements prévus et surveille l'état de la mission.
	def run(self, path: list[Pose] | None = None) -> dict:
		"""Move the mission agent along the planned path and return its final response."""
		# Calcule le chemin si l'appelant n'en a pas fourni.
		path = path or self.find_path()
		result = {}
		name = quote(self.agent_name, safe="")
		# Saute la position de départ et déplace le robot case par case.
		for node in path[1:]:
			result = self._request(
				f"/agents/{name}/move", {"to": list(node)}
			)
			mission = result.get("mission") or {}
			if mission.get("status") == "failed":
				raise RuntimeError(mission.get("message", "mission failed during BFS"))
			if mission.get("status") == "success":
				break
		return result


# Configure les options CLI, affiche le chemin et lance les déplacements si demandé.
def main() -> int:
	# Lit l'adresse de l'API, le nom du robot et l'option de simulation sans mouvement.
	parser = argparse.ArgumentParser(description="Drive a grid agent to its target with BFS.")
	parser.add_argument("--url", default="http://127.0.0.1:8000", help="grid API base URL")
	parser.add_argument("--agent", default="robot", help="registered mission agent name")
	parser.add_argument("--dry-run", action="store_true", help="show the path without moving")
	args = parser.parse_args()

	# Calcule le chemin, l'affiche, puis exécute la mission sauf en mode dry-run.
	try:
		agent = BFSAgent(args.url, args.agent)
		path = agent.find_path()
		print("BFS path:", " -> ".join(map(str, path)))
		if args.dry_run:
			return 0
		result = agent.run(path)
		print(result.get("mission", {}).get("message", "Agent moved."))
		return 0
	except (RuntimeError, ValueError) as error:
		# Écrit l'erreur sur stderr et renvoie un code de sortie non nul.
		print(f"BFS agent: {error}", file=sys.stderr)
		return 1


# N'exécute main que lorsque ce fichier est lancé directement.
if __name__ == "__main__":
	raise SystemExit(main())
