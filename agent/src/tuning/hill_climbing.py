"""Hill climbing (plus forte descente) avec pas décroissant et redémarrages aléatoires.
Départ aléatoire; on évalue les voisins à pas w = 2, on passe au meilleur s'il améliore F;
au minimum local on affine (pas 1, 0.5, 0.25); puis nouveau départ tant qu'il reste du budget."""
from .space import neighbors, random_config

STEPS = (2.0, 1.0, 0.5, 0.25)


def hill_climbing(tracker, rng, steps=STEPS, max_restarts: int = 200):
    restarts = 0
    while tracker.n < tracker.budget and restarts < max_restarts:
        restarts += 1
        cur = random_config(rng)
        cur_f = tracker(cur)
        for step in steps:                
            while True:
                cands = [(tracker(n), n) for n in neighbors(cur, step) if tracker.can_eval(n)]
                if not cands:
                    break
                f, nxt = min(cands, key=lambda t: t[0])
                if f < cur_f:
                    cur, cur_f = nxt, f
                else:
                    break                      # minimum local pour ce pas
    return tracker.result("hill")