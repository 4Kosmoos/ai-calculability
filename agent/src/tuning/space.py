"""Espace de recherche de (h, w): les variables de décision du problème d'optimisation."""
import random
from dataclasses import dataclass

H_NAMES = ("L1", "L2", "Linf")
W_GRID = (1, 1.25, 1.5, 2, 3, 5, 10)         # valeurs testées par le grid search
W_MIN, W_MAX, W_STEP = 1.0, 10.0, 0.25       # espace continu: random search et hill climbing
W_STEPS = round((W_MAX - W_MIN) / W_STEP)

@dataclass(frozen=True)
class Config:
    h: str
    w: float

    def __str__(self) -> str:
        return f"{self.h}/w={self.w:g}"


def normalize_w(w: float) -> float:
    """Borne w dans [W_MIN, W_MAX] et l'arrondit: évite les doublons de configs."""
    return round(min(max(w, W_MIN), W_MAX), 2)


def grid_configs() -> list[Config]:
    return [Config(h, float(w)) for h in H_NAMES for w in W_GRID]


def random_config(rng: random.Random) -> Config:
    """Tirage sur le réseau w = 1, 1.25, ..., 10 (pas W_STEP): mêmes valeurs que le hill climbing."""
    return Config(rng.choice(H_NAMES), normalize_w(W_MIN + rng.randint(0, W_STEPS) * W_STEP))


def neighbors(cfg: Config, step: float = W_STEP) -> list[Config]:
    """Voisins pour le hill climbing: w -/+ step (même h), ou un autre h (même w)."""
    out = []
    for w in (cfg.w - step, cfg.w + step):
        w2 = normalize_w(w)
        if w2 != cfg.w:
            out.append(Config(cfg.h, w2))
    out += [Config(h, cfg.w) for h in H_NAMES if h != cfg.h]
    return out