"""Loader for a personal zsh or bash history file.

Supports zsh's EXTENDED_HISTORY format (``: <epoch>:<duration>;<command>``,
with multi-line commands continued by a trailing backslash), bash with
``HISTTIMEFORMAT`` timestamps (``#<epoch>`` lines), and plain one-command-per-line
files. Plain histories carry no context beyond order.

This is for the developer's own history only. It is read locally and never
committed (see data/README.md).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from cta.datasets.model import CommandEvent, History

_ZSH = re.compile(r"^: (\d+):(\d+);(.*)$")
_BASH_TS = re.compile(r"^#(\d{9,})$")


def load(path: str | Path, user: str = "own") -> History:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    entries: list[tuple[datetime | None, str]] = []

    pending_time: datetime | None = None
    i = 0
    while i < len(lines):
        line = lines[i]
        m = _ZSH.match(line)
        if m:
            cmd = m.group(3)
            while cmd.endswith("\\") and i + 1 < len(lines):  # zsh multi-line entry
                i += 1
                cmd = cmd[:-1] + "\n" + lines[i]
            entries.append((_epoch(m.group(1)), cmd))
        elif _BASH_TS.match(line):
            pending_time = _epoch(line[1:])
        elif line.strip():
            entries.append((pending_time, line))
            pending_time = None
        i += 1

    events = [
        CommandEvent(user=user, index=n, line=cmd.strip(), timestamp=ts)
        for n, (ts, cmd) in enumerate(entries)
        if cmd.strip()
    ]
    events = [CommandEvent(user=user, index=n, line=e.line, timestamp=e.timestamp)
              for n, e in enumerate(events)]
    return History(user=user, events=events)


def _epoch(value: str) -> datetime:
    return datetime.fromtimestamp(int(value), tz=timezone.utc)
