"""Benchmark server for Task 4: a resident engine answering prefix queries over a Unix socket.

Loads a history of command lines (default: the KYPO public datasets), keeps a frecency
ranking, and answers each request (one line: the typed prefix) with the best matching
command line. It is a measurement harness, not the real engine.

Usage: python bench/engine_server.py SOCKET_PATH [--repeat N]
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cta.analysis.predictors import Frecency, hide_command  # noqa: E402
from cta.datasets import kypo  # noqa: E402


def build(repeat: int) -> tuple[Frecency, int]:
    hs = kypo.load(ROOT / "data/raw/svabensky", "s") + kypo.load(ROOT / "data/raw/oslejsek", "o")
    p = Frecency()
    n = 0
    for _ in range(repeat):
        for h in hs:
            for e in h:
                p.update(e)
                n += 1
    return p, n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("socket")
    ap.add_argument("--repeat", type=int, default=1, help="replay the history N times")
    args = ap.parse_args()
    predictor, n = build(args.repeat)
    ranking = predictor.rank(hide_command(_dummy()))
    print(f"loaded {n} commands, {len(ranking)} distinct", flush=True)

    if os.path.exists(args.socket):
        os.unlink(args.socket)
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    srv.bind(args.socket)
    srv.listen(8)
    while True:
        conn, _ = srv.accept()
        with conn, conn.makefile("rwb", buffering=0) as f:
            for raw in f:
                prefix = raw.decode("utf-8", "replace").rstrip("\n")
                best = next((c for c in ranking if c.startswith(prefix)), "") if prefix else ""
                f.write(best.encode() + b"\n")


def _dummy():
    from cta.datasets.model import CommandEvent
    return CommandEvent("u", 0, "")


if __name__ == "__main__":
    main()
