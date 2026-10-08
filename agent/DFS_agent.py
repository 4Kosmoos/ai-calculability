"""DFS controller that drives an agent through the grid API."""
import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

Pose = tuple[int, int]


class DFSAgent:
	"""Find a DFS path and send moves to the running grid API."""

	def __init__(self, base_url: str = "http://127.0.0.1:8000",
				 agent_name: str = "robot", timeout: float = 5):
		self.base_url = base_url.rstrip("/")
		self.agent_name = agent_name
		self.timeout = timeout

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
			raise RuntimeError(f"cannot connect to grid API at {self.base_url}: {error.reason}") from error

	def find_path(self) -> list[Pose]:
		"""Return a path found by depth-first search, avoiding weighted cells when possible."""
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

		def search(avoid_weighted: bool) -> list[Pose] | None:
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

				neighbors = self._request(f"/nodes/{current[0]}/{current[1]}/neighbors")
				for info in neighbors:
					neighbor = tuple(info["node"])
					if neighbor in previous:
						continue
					if avoid_weighted and info["obstacle_weight"] > 1 and neighbor != target:
						continue
					previous[neighbor] = current
					frontier.append(neighbor)
			return None

		path = search(avoid_weighted=True) or search(avoid_weighted=False)
		if path is None:
			raise ValueError(f"no path from {start} to {target}")
		return path

	def run(self, path: list[Pose] | None = None) -> dict:
		"""Move the mission agent along the planned path and return its final response."""
		path = path or self.find_path()
		result = {}
		name = quote(self.agent_name, safe="")
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


def main() -> int:
	parser = argparse.ArgumentParser(description="Drive a grid agent to its target with DFS.")
	parser.add_argument("--url", default="http://127.0.0.1:8000", help="grid API base URL")
	parser.add_argument("--agent", default="robot", help="registered mission agent name")
	parser.add_argument("--dry-run", action="store_true", help="show the path without moving")
	args = parser.parse_args()

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
		print(f"DFS agent: {error}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
