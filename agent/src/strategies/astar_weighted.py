from .astar import AStar
from .heuristics import euclidean


class AStarWeighted(AStar):
    """A* avec f(n) = g(n) + w * h(n)

    w = 1 -> A* classique ; 
    w grand -> comportement proche de Greedy.
    w = 0 -> comportement de Djikstra.
    Avec h admissible, le coût du chemin est <= w * coût optimal.
    
    """

    def __init__(self, heuristic=euclidean, weight=1.5):
        super().__init__(heuristic, weight)
