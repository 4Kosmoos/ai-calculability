import math
import networkx as nx
import matplotlib.pyplot as plt


class Grid:
    def __init__(self, rows, cols, walls=(), start=(0, 0), goal=None,
                 connectivity=4):
        if connectivity not in (4, 8):
            raise ValueError("connectivity doit valoir 4 ou 8")
        self.rows, self.cols = rows, cols
        self.start = start
        self.goal = goal or (rows - 1, cols - 1)
        self.walls = set(walls)
        self.connectivity = connectivity
        self.graph = self._build()

    def _build(self):
        if self.connectivity == 4:
            G = nx.grid_2d_graph(self.rows, self.cols)
        else:
            # Produit fort de deux chemins = grille avec diagonales
            G = nx.strong_product(nx.path_graph(self.rows),
                                  nx.path_graph(self.cols))
        # Poids: 1 si déplacement orthogonal, sqrt(2) si diagonal
        for (r1, c1), (r2, c2) in G.edges:
            diagonal = (r1 != r2) and (c1 != c2)
            G[(r1, c1)][(r2, c2)]["weight"] = math.sqrt(2) if diagonal else 1
        G.remove_nodes_from(self.walls)
        return G

    def neighbors(self, node):
        return list(self.graph.neighbors(node))

    def draw(self, path=None):
        pos = {(r, c): (c, -r) for r, c in self.graph.nodes}
        path = set(path or [])
        colors = ["green" if n == self.start else
                  "red" if n == self.goal else
                  "gold" if n in path else "lightblue"
                  for n in self.graph.nodes]
        nx.draw(self.graph, pos, node_color=colors, node_size=400,
                with_labels=False)
        for r, c in self.walls:
            plt.scatter(c, -r, c="black", marker="s", s=400)
        plt.title(f"{self.connectivity}-voisins")
        plt.axis("equal")
        plt.show()


if __name__ == "__main__":
    walls = [(1, 1), (1, 3), (3, 2)]
    for k in (4, 8):
        g = Grid(4, 5, walls=walls, goal=(3, 4), connectivity=k)
        path = nx.shortest_path(g.graph, g.start, g.goal, weight="weight")
        cost = nx.shortest_path_length(g.graph, g.start, g.goal,
                                       weight="weight")
        print(f"[{k}] nœuds={g.graph.number_of_nodes()} "
              f"arêtes={g.graph.number_of_edges()} "
              f"voisins de (0,0)={g.neighbors((0, 0))} "
              f"coût={cost:.2f} pas={len(path) - 1}")
        g.draw(path)