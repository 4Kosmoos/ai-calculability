# Projet fil rouge

Recherche de chemin sur une grille avec plusieurs algorithmes (BFS, DFS, Greedy, Dijkstra, A*, A* pondérée).

## Commandes

```bash
# 1. Lancer l'API de la grille (Docker, port 8000)
bash ./grid/launch.sh

# 2. Générer une grande grille aléatoire (taille, densité d'obstacles, seed)
python ./agent/src/generate_grid.py --size 60 --density 0.25 --seed 42

# 3. Lancer l'agent (algorithme choisi dans main.py)
python ./agent/src/main.py

# 4. Comparer tous les algorithmes (nœuds, temps, coût)
python ./agent/src/compare.py

# 5. Chercher le meilleur poids w de l'A* pondérée -> results.csv
python ./agent/src/optimize.py

# 6. Tracer F en fonction de w -> results.png
python ./agent/src/plot_results.py

# 7. Tester w sur plusieurs grilles différentes -> robustness.csv
python ./agent/src/robustness.py
```

