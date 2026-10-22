"""Suivi d'une recherche: configs évaluées (= budget consommé), meilleur score, historique."""
from dataclasses import dataclass

from .space import Config


@dataclass
class SearchResult:
    method: str
    best: Config
    best_score: float
    n_configs: int
    history: list            


class Tracker:
    def __init__(self, objective, budget: int):
        self.obj, self.budget = objective, budget
        self.seen: dict[Config, float] = {}
        self.best, self.best_score = None, float("inf")
        self.history: list = []

    @property
    def n(self) -> int:
        return len(self.seen)

    def can_eval(self, cfg: Config) -> bool:
        return cfg in self.seen or self.n < self.budget

    def __call__(self, cfg: Config) -> float:
        if cfg not in self.seen:
            f = self.obj(cfg)
            self.seen[cfg] = f
            if self.best is None or f < self.best_score:
                self.best, self.best_score = cfg, f
            self.history.append((self.n, self.best_score))
        return self.seen[cfg]

    def result(self, method: str) -> SearchResult:
        return SearchResult(method, self.best, self.best_score, self.n, self.history)