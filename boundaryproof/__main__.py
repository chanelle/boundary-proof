"""BoundaryProof v0.1 CLI.

Usage:
  python -m boundaryproof assess fixtures/f02_observed_exceeds_intended.json
  python -m boundaryproof assess <input.json> --policy policies/auto.json --out report.md
  python -m boundaryproof assess <input.json> --human policies/human.json --out report.md

Input: one JSON document (see fixtures/ for the canonical format):
  stated agent intent + deployment/configuration + authorized test target.
Output: evidence-backed I/C/O assessment (markdown report + JSON).
"""
from __future__ import annotations

import argparse
import json
import sys

from . import engine


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="boundaryproof",
                                 description="BoundaryProof v0.1 — agent authority assessment")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("assess", help="run one assessment")
    a.add_argument("input", help="input JSON document (intent + config + test target)")
    a.add_argument("--policy", default=None, help="policy pre-authorizations JSON")
    a.add_argument("--human", default=None, help="simulated human gate decisions JSON")
    a.add_argument("--out", default=None, help="write markdown report to file")
    a.add_argument("--json-out", default=None, help="write assessment JSON to file")

    args = ap.parse_args(argv)
    assessment = engine.run_file(args.input, policy_path=args.policy,
                                 human_path=args.human)
    md = engine.render_markdown(assessment)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(md)
        print(f"report written to {args.out}")
    else:
        print(md)
    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(assessment.to_dict(), fh, indent=2)
        print(f"assessment JSON written to {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
