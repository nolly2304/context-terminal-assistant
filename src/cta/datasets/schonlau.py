"""Loader for the Schonlau et al. (2001) masquerade dataset.

Format (as distributed in ``mask.dat``): 750,000 lines, one program name per line,
for 50 users in order (15,000 commands each). Each user's first 5,000 commands
are clean. The remaining 10,000 are 100 blocks of 100 commands; ``summary.dat``
has one row per block and one column per user, with 1 marking a block that
contains another user's commands ("masquerades").

We drop masquerade blocks, so every history really is one person's behaviour.
Data were collected with Unix process accounting, so they include programs started
by scripts as well as typed commands, and no arguments. That limits what this
dataset can tell us; see docs/analysis/usage-patterns.md.

Reference: Schonlau, M. et al. (2001) 'Computer intrusion: detecting masquerades',
Statistical Science, 16(1), pp. 58-74.
"""

from __future__ import annotations

from pathlib import Path

from cta.datasets.model import CommandEvent, History

USERS = 50
PER_USER = 15_000
CLEAN_PREFIX = 5_000
BLOCK = 100


def load(directory: str | Path, drop_masquerades: bool = True) -> list[History]:
    directory = Path(directory)
    commands = (directory / "mask.dat").read_text(encoding="latin-1").split("\n")
    commands = [c.strip() for c in commands if c.strip()]
    if len(commands) != USERS * PER_USER:
        raise ValueError(f"expected {USERS * PER_USER} commands, found {len(commands)}")

    masquerade = _read_summary(directory / "summary.dat") if drop_masquerades else None

    histories = []
    for u in range(USERS):
        user = f"schonlau-{u + 1:02d}"
        chunk = commands[u * PER_USER : (u + 1) * PER_USER]
        kept: list[str] = []
        for i, cmd in enumerate(chunk):
            if masquerade is not None and i >= CLEAN_PREFIX:
                block = (i - CLEAN_PREFIX) // BLOCK
                if masquerade[block][u]:
                    continue
            kept.append(cmd)
        events = [CommandEvent(user=user, index=i, line=c) for i, c in enumerate(kept)]
        histories.append(History(user=user, events=events))
    return histories


def _read_summary(path: Path) -> list[list[int]]:
    rows = [line.split() for line in path.read_text().splitlines() if line.strip()]
    if len(rows) != (PER_USER - CLEAN_PREFIX) // BLOCK or any(len(r) != USERS for r in rows):
        raise ValueError("summary.dat should be 100 rows of 50 values")
    return [[int(v) for v in r] for r in rows]
