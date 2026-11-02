"""Common representation of a command history.

Every dataset is converted into a list of :class:`CommandEvent` per user, so the
analysis (and later the replay harness) never needs to know where data came from.
Context fields are optional because datasets record different things: Schonlau
has only program names, while Švábenský et al. add working directory and time.
"""

from __future__ import annotations

import shlex
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CommandEvent:
    """One command a user ran, plus whatever context the dataset recorded."""

    user: str
    index: int  # position in this user's history, starting at 0
    line: str  # full command line, or just the program name if that is all we have
    session: str | None = None
    cwd: str | None = None
    timestamp: datetime | None = None
    host: str | None = None
    exit_status: int | None = None

    @property
    def program(self) -> str:
        return program_name(self.line)


@dataclass
class History:
    """All events for one user, in the order they happened."""

    user: str
    events: list[CommandEvent] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.events)

    def __iter__(self) -> Iterator[CommandEvent]:
        return iter(self.events)

    def has(self, attribute: str) -> bool:
        """True if any event records this context attribute (e.g. ``"cwd"``)."""
        return any(getattr(e, attribute) is not None for e in self.events)


def program_name(line: str) -> str:
    """Return the program a command line invokes, e.g. ``"git"`` for ``"sudo git push"``.

    Leading environment assignments (``FOO=1 cmd``) and ``sudo`` are skipped,
    following the POSIX shell grammar for simple commands.
    """
    try:
        words = shlex.split(line, comments=False, posix=True)
    except ValueError:  # unbalanced quotes: fall back to whitespace splitting
        words = line.split()
    for word in words:
        if "=" in word and not word.startswith("=") and word.split("=", 1)[0].isidentifier():
            continue
        if word == "sudo":
            continue
        return word.rsplit("/", 1)[-1]
    return ""
