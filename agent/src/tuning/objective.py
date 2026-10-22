"""Fonction objectif F = a*C' + b*T' + c*M' (+ pénalités) et son évaluation sur des scénarios."""
import argparse
from .evaluate import Evaluation, Evaluator
from .scenarios import Scenario, build_scenarios
from .space import Config, grid_configs

PENALTY = 1000.0
PROFILES = {                       # (a, b, c): poids de C', T', M', somme = 1
    "qualite": (0.8, 0.1, 0.1),
    "equilibre": (0.4, 0.3, 0.3),
    "rapide": (0.1, 0.5, 0.4),
}


def check_weights(weights) -> tuple:
    a, b, c = weights
    if min(a, b, c) < 0 or abs(a + b + c - 1) > 1e-9:
        raise ValueError(f"(a, b, c) doit être >= 0 et de somme 1, reçu {weights}")
    return weights


def violations(e: Evaluation) -> list[str]:
    v = []
    if not e.found:
        v.append("pas_de_chemin")
    if not e.admissible:
        v.append("h_non_admissible")
    if not e.feasible:
        v.append("seuil_mission")
    if not e.within_k:
        v.append("borne_k")
    return v


def score(e: Evaluation, weights, penalty: float = PENALTY) -> float:
    """F normalisé (Dijkstra = 1) + penalité par contrainte violée. À MINIMISER."""
    if not e.found:
        return float("inf")
    a, b, c = weights
    return a * e.c_ratio + b * e.t_ratio + c * e.m_ratio + penalty * len(violations(e))


class Objective:
    """F d'une config, moyennée sur un groupe de scénarios. Met les évaluations en cache."""

    def __init__(self, evaluator: Evaluator, scenarios: list[Scenario], weights,
                 penalty=PENALTY, cache: dict | None = None):
        self.ev, self.scenarios = evaluator, scenarios
        self.weights, self.penalty = check_weights(weights), penalty
        self._cache: dict[tuple, Evaluation] = cache if cache is not None else {}

    @property
    def n_evals(self) -> int:
        """Nombre d'évaluations (config, scénario) réellement calculées."""
        return len(self._cache)

    def evaluation(self, cfg: Config, sc: Scenario) -> Evaluation:
        key = (sc.key, cfg)
        if key not in self._cache:
            self._cache[key] = self.ev.evaluate(sc, cfg.h, cfg.w)
        return self._cache[key]

    def scores(self, cfg: Config) -> list[float]:
        return [score(self.evaluation(cfg, sc), self.weights, self.penalty) for sc in self.scenarios]

    def __call__(self, cfg: Config) -> float:
        s = self.scores(cfg)
        return sum(s) / len(s)

    def worst(self, cfg: Config) -> float:
        return max(self.scores(cfg))

    def detail(self, cfg: Config) -> list[tuple]:
        return [(sc.key, self.evaluation(cfg, sc), violations(self.evaluation(cfg, sc)))
                for sc in self.scenarios]


def main():
    ap = argparse.ArgumentParser(prog="tuning.objective")
    ap.add_argument("--scenario", nargs="+", default=["default-8-c8", "drawing-20-c8", "wall_full-20-c8"])
    ap.add_argument("--profile", choices=PROFILES, default="equilibre")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--repeats", type=int, default=3)
    args = ap.parse_args()

    by_key = {s.key: s for s in build_scenarios()}
    obj = Objective(Evaluator(repeats=args.repeats), [by_key[k] for k in args.scenario], PROFILES[args.profile])
    rows = sorted(((obj(cfg), obj.worst(cfg), cfg) for cfg in grid_configs()), key=lambda r: (r[0], r[1]))
    print(f"profil={args.profile} {PROFILES[args.profile]} | scénarios={args.scenario} | {obj.n_evals} évaluations")
    print(f"{'config':<14}{'F moyen':>10}{'F pire':>10}  violations")
    for mean, worst, cfg in rows[:args.top]:
        viol = sorted({v for _, _, vs in obj.detail(cfg) for v in vs})
        print(f"{str(cfg):<14}{mean:>10.3f}{worst:>10.3f}  {','.join(viol) or '-'}")
    mean, worst, cfg = rows[-1]
    viol = sorted({v for _, _, vs in obj.detail(cfg) for v in vs})
    print(f"... pire: {str(cfg):<10}{mean:>10.3f}{worst:>10.3f}  {','.join(viol) or '-'}")


if __name__ == "__main__":
    main()