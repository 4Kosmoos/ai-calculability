import sys

from agent import Agent
from strategies import BFS, DFS

if __name__ == "__main__":
    agent_id = sys.argv[1] if len(sys.argv) > 1 else "robot"
    agent = Agent(agent_id, BFS())
    #agent = Agent(agent_id, DFS())
    agent.reset_mission()
    agent.run(verbose=True)