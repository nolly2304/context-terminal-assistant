"""Loader for logs written by scripts/cta-log.bash.

Each line is a JSON object recorded after a command finished:
``t`` (Unix time), ``host``, ``session``, ``cwd`` and ``git_branch``/``git_dirty``
(the state when the command was typed), ``exit`` (the command's exit status) and
``cmd``. The exit status of the *previous* command, which is the context signal
C5, is the ``exit_status`` of the event before it in the same session.

These logs are personal data. They are read locally and never committed.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from cta.datasets.model import CommandEvent, History


def load(path: str | Path, user: str = "own-logged") -> History:
    """Load one log file as a single user's history, in time order."""
    records = []
    for n, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines()):
        if not raw.strip():
            continue
        try:
            r = json.loads(raw)
        except json.JSONDecodeError:
            continue  # a line cut short by a crash or full disk
        cmd = (r.get("cmd") or "").strip()
        if cmd:
            records.append((r.get("t") or 0, n, r, cmd))
    records.sort(key=lambda x: (x[0], x[1]))
    events = [
        CommandEvent(
            user=user,
            index=i,
            line=cmd,
            session=r.get("session"),
            cwd=r.get("cwd"),
            timestamp=datetime.fromtimestamp(t, tz=timezone.utc) if t else None,
            host=r.get("host"),
            exit_status=r.get("exit"),
            git_branch=r.get("git_branch"),
            git_dirty=r.get("git_dirty"),
        )
        for i, (t, _, r, cmd) in enumerate(records)
    ]
    return History(user=user, events=events)


def sessions(history: History) -> dict[str | None, list[CommandEvent]]:
    """Group events by shell session, keeping order."""
    out: dict[str | None, list[CommandEvent]] = defaultdict(list)
    for e in history:
        out[e.session].append(e)
    return dict(out)
