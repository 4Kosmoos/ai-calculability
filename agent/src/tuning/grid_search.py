"""Grid search: évalue toutes les configs de la grille (7 valeurs de w x 3 heuristiques)."""
from .space import grid_configs


def grid_search(tracker, rng=None):
    for cfg in grid_configs():
        tracker(cfg)
    return tracker.result("grid")