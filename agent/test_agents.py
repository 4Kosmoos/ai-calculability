"""Run each grid agent in turn, resetting the grid to the default config."""
# Imports standard pour les arguments, le JSON, les chemins de fichiers et les requêtes HTTP.
import argparse
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Import des cinq algorithmes à comparer.
from A_star_agent import AStarAgent
from BFS_agent import BFSAgent
from DFS_agent import DFSAgent
from Dijkstra_agent import DijkstraAgent
from Greedy_agent import GreedyAgent


# Envoie une requête HTTP à l'API et transforme sa réponse JSON en dictionnaire.
def api_request(
	base_url: str, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
	# Prépare le corps JSON uniquement pour les requêtes qui transportent des données.
	data = json.dumps(payload).encode("utf-8") if payload is not None else None
	request = Request(
		f"{base_url.rstrip('/')}{path}",
		data=data,
		headers={"Content-Type": "application/json"} if data is not None else {},
	)
	# Exécute la requête et convertit les erreurs HTTP ou de connexion en messages lisibles.
	try:
		with urlopen(request, timeout=5) as response:
			return json.loads(response.read().decode("utf-8"))
	except HTTPError as error:
		try:
			detail = json.loads(error.read().decode("utf-8")).get("error", str(error))
		except (ValueError, AttributeError):
			detail = str(error)
		raise RuntimeError(f"API error {error.code}: {detail}") from error
	except URLError as error:
		raise RuntimeError(
			f"cannot connect to grid API at {base_url}: {error.reason}"
		) from error


# Crée une figure comparative avec un panneau par algorithme et enregistre l'image PNG.
def plot_paths(
		config: dict[str, Any],
		paths: dict[str, list[tuple[int, int]]],
		summaries: dict[str, str],
		output_path: Path,
) -> None:
		# Charge Matplotlib à la demande pour que le reste du script puisse tourner sans lui.
		try:
			import matplotlib.pyplot as plt
		except ImportError as error:
			raise RuntimeError(
				"Matplotlib is required to draw the comparison graph; "
				"install it with 'python -m pip install -r "
				"grid\\grid_api\\requirements-viz.txt'."
			) from error

		# Associe chaque algorithme à un nom et à une couleur pour distinguer ses chemins.
		labels = ("BFS", "DFS", "Greedy", "Dijkstra", "A*")
		colors = {
			"BFS": "#2563eb",
			"DFS": "#dc2626",
			"Greedy": "#16a34a",
			"Dijkstra": "#9333ea",
			"A*": "#ea580c",
		}
		# Lit la taille de grille et convertit les obstacles en coordonnées (ligne, colonne).
		size = config["size"]
		obstacles = {
			tuple(item["node"]): item["weight"] for item in config["obstacles"]
		}
		# Prépare cinq panneaux, en réservant le sixième emplacement vide.
		figure, axes = plt.subplots(2, 3, figsize=(15, 10), constrained_layout=True)

		# Dessine dans chaque panneau les obstacles, le chemin, le départ et la cible.
		for axis, label in zip(axes.flat, labels):
			# Représente chaque obstacle par une case grise portant son poids.
			for (row, column), weight in obstacles.items():
				axis.scatter(
					column,
					row,
					marker="s",
					s=260,
					color="#555555",
					zorder=2,
				)
				axis.text(
					column,
					row,
					str(weight),
					color="white",
					ha="center",
					va="center",
					fontsize=8,
					zorder=3,
				)

			# Trace le chemin calculé, ou affiche un message si l'algorithme n'en a pas trouvé.
			path = paths.get(label)
			if path:
				axis.plot(
					[node[1] for node in path],
					[node[0] for node in path],
					"-o",
					color=colors[label],
					linewidth=2,
					markersize=4,
					label="Chemin",
					zorder=4,
				)
			else:
				axis.text(
					0.5,
					0.5,
					"Aucun chemin calculé",
					transform=axis.transAxes,
					ha="center",
					va="center",
					color="#b91c1c",
				)

			# Marque le départ et la cible, puis configure les axes comme une grille de jeu.
			start = config["mission"]["start"]
			target = config["mission"]["target"]
			axis.scatter(start[1], start[0], marker="s", s=100, color="#2563eb",
						 label="Départ", zorder=5)
			axis.scatter(target[1], target[0], marker="*", s=180, color="#16a34a",
						 label="Cible", zorder=5)
			axis.set_title(f"{label} — {summaries.get(label, 'non exécuté')}")
			axis.set_xlim(-0.5, size - 0.5)
			axis.set_ylim(size - 0.5, -0.5)
			axis.set_xticks(range(size))
			axis.set_yticks(range(size))
			axis.set_aspect("equal")
			axis.grid(True, color="#cccccc", linewidth=0.5)
			axis.set_xlabel("Colonne")
			axis.set_ylabel("Ligne")

		# Masque le panneau inutilisé, ajoute le titre, sauvegarde le graphique et l'affiche.
		axes.flat[-1].axis("off")
		figure.suptitle("Comparaison des chemins des cinq algorithmes")
		figure.savefig(output_path, dpi=150, bbox_inches="tight")
		print(f"\nGraph saved to: {output_path}")
		plt.show()


# Configure le script, exécute les cinq agents et produit le graphique comparatif.
def main() -> int:
	# Détermine le chemin de la configuration par défaut à partir de l'emplacement du script.
	project_root = Path(__file__).resolve().parents[1]
	default_config = (
		project_root / "grid" / "grid_api" / "config" / "default.json"
	)
	# Définit les options de ligne de commande pour l'URL de l'API et le fichier de grille.
	parser = argparse.ArgumentParser(
		description="Run BFS, DFS, Greedy, Dijkstra, and A* with a fresh grid each time."
	)
	parser.add_argument("--url", default="http://127.0.0.1:8000", help="grid API base URL")
	parser.add_argument(
		"--config",
		type=Path,
		default=default_config,
		help="grid configuration JSON used to reset the API before each agent",
	)
	args = parser.parse_args()

	# Charge le JSON qui servira à recréer la même grille avant chaque algorithme.
	try:
		config = json.loads(args.config.read_text(encoding="utf-8"))
	except (OSError, json.JSONDecodeError) as error:
		parser.error(f"cannot read grid config {args.config}: {error}")

	# Associe les noms affichés aux classes des agents à tester.
	agents = (
		("BFS", BFSAgent),
		("DFS", DFSAgent),
		("Greedy", GreedyAgent),
		("Dijkstra", DijkstraAgent),
		("A*", AStarAgent),
	)
	# Prépare les compteurs et les résultats nécessaires au récapitulatif et au graphique.
	failures = 0
	paths: dict[str, list[tuple[int, int]]] = {}
	summaries: dict[str, str] = {}

	# Réinitialise la grille, calcule le chemin et exécute chaque agent l'un après l'autre.
	for label, agent_type in agents:
		print(f"\n=== {label} ===")
		try:
			# Recharge la configuration complète afin que chaque algorithme parte du même état.
			api_request(args.url, "/init", config)
			agent = agent_type(args.url, config["agents"][0])
			path = agent.find_path()
			paths[label] = path
			print("Path:", " -> ".join(map(str, path)))
			# Effectue les déplacements et vérifie que la mission a bien été terminée.
			result = agent.run(path)
			mission = result.get("mission") or {}
			if mission.get("status") != "success":
				raise RuntimeError(
					mission.get("message", "agent did not complete the mission")
				)
			summaries[label] = (
				f"cost {mission['total_weight']}, {mission['steps']} moves"
			)
			print(
				f"Success | cost: {mission['total_weight']} | "
				f"moves: {mission['steps']}"
			)
		except (HTTPError, RuntimeError, ValueError, KeyError) as error:
			# Enregistre l'échec pour le bilan et poursuit avec l'algorithme suivant.
			failures += 1
			summaries[label] = "échec"
			print(f"FAILED: {error}")

	# Affiche le nombre de réussites, puis génère et sauvegarde le graphique des chemins.
	print(f"\nResults: {len(agents) - failures}/{len(agents)} agents succeeded.")
	try:
		plot_paths(
			config,
			paths,
			summaries,
			Path(__file__).with_name("agent_paths.png"),
		)
	except RuntimeError as error:
		# Signale une erreur de visualisation, par exemple si Matplotlib n'est pas installé.
		failures += 1
		print(f"Could not create comparison graph: {error}")
	return 1 if failures else 0


# Lance le programme uniquement si ce fichier est exécuté directement.
if __name__ == "__main__":
	raise SystemExit(main())
