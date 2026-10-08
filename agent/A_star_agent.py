"""A* controller that drives an agent through the grid API."""
import argparse
import heapq
import itertools
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

Pose = tuple[int, int]


class AStarAgent:
	"""Find a minimum-cost path with A* and send moves to the grid API."""

	def __init__(self, base_url: str = "http://127.0.0.1:8000",
				 agent_name: str = "robot", timeout: float = 5):
		self.base_url = base_url.rstrip("/")
		self.agent_name = agent_name
		self.timeout = timeout
		self.path_cost: float | None = None

	def _request(self, path: str, payload: dict | None = None) -> dict:
		data = json.dumps(payload).encode("utf-8") if payload is not None else None
		request = Request(
			f"{self.base_url}{path}",
			data=data,
			headers={"Content-Type": "application/json"} if data is not None else {},
		)
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

	def find_path(self) -> list[Pose]:
		"""Return a minimum-cost path using an admissible grid-distance heuristic."""
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

		agents = {agent["name"]: agent for agent in state["agents"]}
		if self.agent_name not in agents:
			raise ValueError(f"agent {self.agent_name!r} is not registered in the grid")
		start = tuple(agents[self.agent_name]["pose"])
		target = tuple(mission["target"])
		connectivity = state["connectivity"]

		def heuristic(node: Pose) -> float:
			row_delta = abs(target[0] - node[0])
			column_delta = abs(target[1] - node[1])
			if connectivity == 8:
				diagonal_steps = min(row_delta, column_delta)
				straight_steps = max(row_delta, column_delta) - diagonal_steps
				return 1.5 * diagonal_steps + straight_steps
			return row_delta + column_delta

		distances: dict[Pose, float] = {start: 0.0}
		previous: dict[Pose, Pose] = {}
		order = itertools.count()
		frontier = [(heuristic(start), 0.0, next(order), start)]

		while frontier:
			_, current_cost, _, current = heapq.heappop(frontier)
			if current_cost > distances[current]:
				continue
			if current == target:
				break

			neighbors = self._request(
				f"/nodes/{current[0]}/{current[1]}/neighbors"
			)
			for info in neighbors:
				neighbor = tuple(info["node"])
				new_cost = current_cost + info["cost"]
				if new_cost < distances.get(neighbor, float("inf")):
					distances[neighbor] = new_cost
					previous[neighbor] = current
					heapq.heappush(
						frontier,
						(new_cost + heuristic(neighbor), new_cost, next(order), neighbor),
					)

		if target not in distances:
			raise ValueError(f"no path from {start} to {target}")

		path = [target]
		while path[-1] != start:
			path.append(previous[path[-1]])
		path.reverse()
		self.path_cost = distances[target]
		return path

	def run(self, path: list[Pose] | None = None) -> dict:
		"""Move the mission agent along the planned path and return its final response."""
		path = self.find_path() if path is None else path
		if not path:
			raise ValueError("path cannot be empty")
		name = quote(self.agent_name, safe="")
		if len(path) == 1:
			return {"mission": self._request("/state")["mission"]}

		result = {}
		for node in path[1:]:
			result = self._request(
				f"/agents/{name}/move", {"to": list(node)}
			)
			mission = result.get("mission") or {}
			if mission.get("status") == "failed":
				raise RuntimeError(mission.get("message", "mission failed during A*"))
			if mission.get("status") == "success":
				return result
		raise RuntimeError("path ended while the mission is still running")


def main() -> int:
	parser = argparse.ArgumentParser(
		description="Drive a grid agent to its target with A*."
	)
	parser.add_argument("--url", default="http://127.0.0.1:8000", help="grid API base URL")
	parser.add_argument("--agent", default="robot", help="registered mission agent name")
	parser.add_argument("--dry-run", action="store_true", help="show the path without moving")
	args = parser.parse_args()

	try:
		agent = AStarAgent(args.url, args.agent)
		path = agent.find_path()
		print("A* path:", " -> ".join(map(str, path)))
		print(f"Total path cost: {agent.path_cost}")
		if args.dry_run:
			return 0
		result = agent.run(path)
		print(result.get("mission", {}).get("message", "Agent moved."))
		return 0
	except (RuntimeError, ValueError) as error:
		print(f"A* agent: {error}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
