"""Random search: tire des configs au hasard jusqu'à épuiser le budget."""
from .space import random_config


def random_search(tracker, rng):
    attempts = 0
    while tracker.n < tracker.budget and attempts < 50 * tracker.budget:
        tracker(random_config(rng))
        attempts += 1
    return tracker.result("random")