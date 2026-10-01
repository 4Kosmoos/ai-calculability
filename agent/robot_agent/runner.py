from .algorithms import ALGORITHMS
from .client import GridClient
from .models import SearchResult


def run(client: GridClient, algo: str, execute: bool = True):
    """Reset -> Plan (read only) -> Excute the way on the grid"""
    problem = client.problem()
    client.reset_mission(problem)     
    result: SearchResult = ALGORITHMS[algo](client, problem)

    outcome = None
    if execute and result.found:
        for node in result.path[1:]:      
            outcome = client.move(problem.agent, node)
            if outcome["mission"]["status"] != "running":
                break                        # success or failed 
    return result, outcome