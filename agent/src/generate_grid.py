"""Recrée la grille de l'API (POST /init) en grand, avec des obstacles placés aléatoirement.

Départ en haut à gauche, cible en bas à droite. La grille vit en mémoire dans l'API :
un redémarrage de l'API recharge config/default.json.
"""
import argparse
import random

import requests


def build_payload(size: int, density: float, min_weight: int, max_weight: int, seed: int) -> dict:
    rng = random.Random(seed)
    start, target = [0, 0], [size - 1, size - 1]
    obstacles = [
        {"node": [r, c], "weight": rng.randint(min_weight, max_weight)}
        for r in range(size) for c in range(size)
        if [r, c] not in (start, target) and rng.random() < density
    ]
    return {
        "size": size,
        "connectivity": 8,
        "agents": ["robot"],
        "obstacles": obstacles,
        "mission": {"start": start, "target": target, "threshold": 1e9},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=60)
    parser.add_argument("--density", type=float, default=0.25, help="proportion de cases avec obstacle")
    parser.add_argument("--min-weight", type=int, default=2)
    parser.add_argument("--max-weight", type=int, default=40)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--url", default="http://localhost:8000")
    args = parser.parse_args()

    payload = build_payload(args.size, args.density, args.min_weight, args.max_weight, args.seed)
    resp = requests.post(args.url.rstrip("/") + "/init", json=payload, timeout=60)
    resp.raise_for_status()
    print(f"Grille {args.size}x{args.size}, {len(payload['obstacles'])} obstacles "
          f"(poids {args.min_weight}-{args.max_weight}), seed {args.seed}, "
          f"mission {payload['mission']['start']} -> {payload['mission']['target']}")
