import sys

from agent import Agent
from strategies import BFS, DFS, GreedyBestFirst, Dijkstra, AStar

if __name__ == "__main__":
    agent_id = sys.argv[1] if len(sys.argv) > 1 else "robot"
    #agent = Agent(agent_id, BFS())
    #agent = Agent(agent_id, DFS())
    #agent = Agent(agent_id, GreedyBestFirst())
    #agent = Agent(agent_id, Dijkstra())
    agent = Agent(agent_id, AStar())
    agent.reset_mission()
    agent.run(verbose=True)