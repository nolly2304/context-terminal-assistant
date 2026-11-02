"""Loader for command logs from the KYPO Cyber Range (Masaryk University).

Two public datasets share this format (one JSON object per line, one file per
trainee's sandbox):

* Švábenský, V. et al. (2021) 'Dataset of shell commands used by participants of
  hands-on cybersecurity training', Data in Brief. 175 trainees, 13,446 records.
* Ošlejšek, R. et al. (2023) 'Dataset: behavior of participants in hands-on
  cybersecurity training suitable for process mining', Zenodo (data1). 52 trainees.

Each record has ``cmd``, ``timestamp_str`` and ``hostname``. Bash records also
have ``wd`` (working directory) and ``username``. ``cmd_type`` is either
``bash-command`` or ``msf-command`` (typed inside the Metasploit console, not a
shell). Both are CC BY 4.0.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from cta.datasets.model import CommandEvent, History


def load(
    directory: str | Path, prefix: str = "kypo", include_msf: bool = False
) -> list[History]:
    """Load every ``*-useractions.json`` file under ``directory`` (recursively).

    One file is one trainee's sandbox, so it becomes one :class:`History`.
    Events are sorted by timestamp, keeping file order for ties.
    """
    histories = []
    for path in sorted(Path(directory).rglob("*-useractions.json")):
        group = path.parent.name.replace(" ", "_")
        user = f"{prefix}/{group}/{path.stem.removesuffix('-useractions')}"
        records = []
        for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines()):
            if not raw.strip():
                continue
            r = json.loads(raw)
            if not include_msf and r.get("cmd_type") != "bash-command":
                continue
            cmd = (r.get("cmd") or "").strip()
            if not cmd:
                continue
            records.append((_parse_time(r.get("timestamp_str")), n, cmd, r))
        records.sort(key=lambda t: (t[0] or datetime.min, t[1]))
        events = [
            CommandEvent(
                user=user,
                index=i,
                line=cmd,
                session=user,  # each sandbox is a single training session
                cwd=r.get("wd"),
                timestamp=ts,
                host=r.get("hostname"),
            )
            for i, (ts, _, cmd, r) in enumerate(records)
        ]
        if events:
            histories.append(History(user=user, events=events))
    return histories


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None
