"""DFS controller that drives an agent through the grid API."""
# Imports pour les options de commande, les échanges JSON/HTTP et l'encodage du nom du robot.
import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

# Type représentant une position (ligne, colonne) dans la grille.
Pose = tuple[int, int]


class DFSAgent:
	"""Find a DFS path and send moves to the running grid API."""

	# Enregistre l'adresse de l'API, l'agent concerné et le délai maximal des requêtes.
	def __init__(self, base_url: str = "http://127.0.0.1:8000",
				 agent_name: str = "robot", timeout: float = 5):
		self.base_url = base_url.rstrip("/")
		self.agent_name = agent_name
		self.timeout = timeout

	# Envoie une requête à l'API et rend ses réponses JSON accessibles sous forme de dictionnaire.
	def _request(self, path: str, payload: dict | None = None) -> dict:
		# Sérialise le contenu de la requête s'il y en a un.
		data = json.dumps(payload).encode("utf-8") if payload is not None else None
		request = Request(
			f"{self.base_url}{path}",
			data=data,
			headers={"Content-Type": "application/json"} if data is not None else {},
		)
		# Traite les réponses normales, les erreurs HTTP et les problèmes de connexion.
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

	# Vérifie la mission, puis trouve un chemin en explorant en profondeur (DFS).
	def find_path(self) -> list[Pose]:
		"""Return the first path found by depth-first search, ignoring cell weights."""
		# Récupère la mission et vérifie qu'elle est active et assignée à cet agent.
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

		# Identifie la case de départ du robot et la destination de la mission.
		agents = {agent["name"]: agent for agent in state["agents"]}
		if self.agent_name not in agents:
			raise ValueError(f"agent {self.agent_name!r} is not registered in the grid")
		start = tuple(agents[self.agent_name]["pose"])
		target = tuple(mission["target"])

		# Explore avec une pile LIFO; seuls les nœuds sont considérés, pas leurs poids.
		frontier = [start]
		previous: dict[Pose, Pose | None] = {start: None}
		while frontier:
			current = frontier.pop()
			if current == target:
				path = []
				while current is not None:
					path.append(current)
					current = previous[current]
				return list(reversed(path))

			# Récupère les voisins de la case courante.
			neighbors = self._request(f"/nodes/{current[0]}/{current[1]}/neighbors")
			for info in neighbors:
				neighbor = tuple(info["node"])
				# Ignore seulement les cases déjà découvertes; le poids n'influence pas DFS.
				if neighbor in previous:
					continue
				previous[neighbor] = current
				frontier.append(neighbor)

		# La pile vide signifie qu'aucun chemin ne permet d'atteindre la cible.
		raise ValueError(f"no path from {start} to {target}")

	# Suit le chemin en envoyant à l'API un déplacement pour chaque case après le départ.
	def run(self, path: list[Pose] | None = None) -> dict:
		"""Move the mission agent along the planned path and return its final response."""
		# Calcule le chemin si aucun chemin n'a été passé en argument.
		path = path or self.find_path()
		result = {}
		name = quote(self.agent_name, safe="")
		# Exécute les mouvements et arrête le parcours si la mission se termine.
		for node in path[1:]:
			result = self._request(
				f"/agents/{name}/move", {"to": list(node)}
			)
			mission = result.get("mission") or {}
			if mission.get("status") == "failed":
				raise RuntimeError(mission.get("message", "mission failed during DFS"))
			if mission.get("status") == "success":
				break
		return result


# Définit les options du programme et lance le calcul puis l'exécution de la mission.
def main() -> int:
	# Permet de choisir l'URL, l'agent et le mode qui affiche le chemin sans bouger.
	parser = argparse.ArgumentParser(description="Drive a grid agent to its target with DFS.")
	parser.add_argument("--url", default="http://127.0.0.1:8000", help="grid API base URL")
	parser.add_argument("--agent", default="robot", help="registered mission agent name")
	parser.add_argument("--dry-run", action="store_true", help="show the path without moving")
	args = parser.parse_args()

	# Affiche le chemin calculé et l'exécute à moins que l'option dry-run soit activée.
	try:
		agent = DFSAgent(args.url, args.agent)
		path = agent.find_path()
		print("DFS path:", " -> ".join(map(str, path)))
		if args.dry_run:
			return 0
		result = agent.run(path)
		print(result.get("mission", {}).get("message", "Agent moved."))
		return 0
	except (RuntimeError, ValueError) as error:
		# Affiche l'erreur sur la sortie dédiée et signale l'échec avec le code 1.
		print(f"DFS agent: {error}", file=sys.stderr)
		return 1


# Lance le point d'entrée seulement lors d'une exécution directe du fichier.
if __name__ == "__main__":
	raise SystemExit(main())
