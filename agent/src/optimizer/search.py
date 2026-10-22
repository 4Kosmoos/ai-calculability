"""Recherches du meilleur poids w : grid search, random search, puis raffinement autour du meilleur point."""
import math
import random

from .objective import WEIGHTS, evaluate, fitness


def _score(w, reference, weights, repeats, cache):
    if w not in cache:
        metrics = evaluate(w, repeats=repeats)
        cache[w] = {**metrics, "F": fitness(metrics, reference, weights)}
    return cache[w]


def grid_search(values, reference, weights=WEIGHTS, repeats=3, cache=None):
    cache = {} if cache is None else cache
    return [_score(w, reference, weights, repeats, cache) for w in values]


def random_search(low, high, n, reference, seed=0, weights=WEIGHTS, repeats=3, cache=None):
    """Tire n valeurs de w dans [low, high] (log-uniforme si la plage couvre plus d'une décade)."""
    rng = random.Random(seed)
    cache = {} if cache is None else cache
    log_scale = low > 0 and high / low > 10
    values = [
        math.exp(rng.uniform(math.log(low), math.log(high))) if log_scale else rng.uniform(low, high)
        for _ in range(n)
    ]
    return [_score(round(w, 4), reference, weights, repeats, cache) for w in values]


def narrow_range(rows):
    """Plage [w_gauche, w_droite] entourant le meilleur w d'un grid search macro."""
    by_w = sorted(rows, key=lambda row: row["w"])
    best = min(range(len(by_w)), key=lambda i: by_w[i]["F"])
    return by_w[max(best - 1, 0)]["w"], by_w[min(best + 1, len(by_w) - 1)]["w"]


def refine(rows, reference, n_grid=5, n_random=10, seed=0, weights=WEIGHTS, repeats=3):
    """Grid fin autour du meilleur w de `rows`, puis random search autour du meilleur w du grid fin.

    La plage du random est resserrée une seconde fois, sur l'ensemble des résultats (macro + grid fin).
    Renvoie ((plage du grid fin, plage du random), nouvelles lignes).
    """
    grid_range = narrow_range(rows)
    low, high = grid_range
    cache = {row["w"]: row for row in rows}
    step = (high - low) / (n_grid - 1)
    fine = grid_search([low + i * step for i in range(n_grid)], reference, weights, repeats, cache)
    random_range = narrow_range(list(cache.values()))  # sans doublons de w
    rand = []
    if random_range[0] < random_range[1]:
        rand = random_search(*random_range, n_random, reference, seed, weights, repeats, cache)
    return (grid_range, random_range), fine + rand


def compareRandom(reference, n=20, low=1, high=500, seed=0, weights=WEIGHTS, repeats=3):
    """Baseline : recherche aléatoire simple de n tirages dans [low, high], sans grid ni resserrement.

    Sert à comparer les résultats de `refine` avec une recherche aléatoire pure (cache vide : aucun
    point réutilisé du grid macro).
    """
    return random_search(low, high, n, reference, seed, weights, repeats, cache={})
