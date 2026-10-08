import argparse

from .run import print_report, run_all, save_csv


def main():
    ap = argparse.ArgumentParser(prog="robot_agent.bench")
    ap.add_argument("--sizes", type=int, nargs="+", default=[20, 40])
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--out", default="results/bench.csv")
    args = ap.parse_args()

    rows = run_all(args.sizes, args.repeats)
    save_csv(rows, args.out)
    print_report(rows)
    print(f"\nCSV écrit dans {args.out}")


if __name__ == "__main__":
    main()