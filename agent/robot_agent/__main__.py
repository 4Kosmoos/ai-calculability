import argparse
import os

from .algorithms import ALGORITHMS
from .client import GridClient
from .runner import run


def main():
    ap = argparse.ArgumentParser(prog="robot_agent")
    ap.add_argument("algo", choices=ALGORITHMS)
    ap.add_argument("--url", default=os.environ.get("GRID_URL", "http://localhost:8000"))
    ap.add_argument("--plan-only", action="store_true")
    args = ap.parse_args()

    result, outcome = run(GridClient(args.url), args.algo, execute=not args.plan_only)
    print(f"[{result.algo}] trouvé={result.found} pas={max(len(result.path) - 1, 0)} "
          f"coût={result.cost:g} développés={result.expanded} "
          f"appels_api={result.api_calls} temps={result.elapsed * 1000:.1f}ms")
    if outcome:
        print(outcome["mission"]["message"])


if __name__ == "__main__":
    main()