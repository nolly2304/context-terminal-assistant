"""Baseline predictors used in the usage-pattern analysis.

These are deliberately simple heuristics from the literature (Greenberg, 1993;
Davison and Hirsh, 1998; Korvemaker and Greiner, 2000). They exist to measure
how predictable the data is and which context signals carry information, which
decides what the real engine (objective P4) should be built around.

Every predictor is *online*: it ranks candidates using only events it has already
seen, then is told the true command. The context passed to :meth:`rank` has its
command line removed, so a predictor cannot peek at the answer.
"""

from __future__ import annotations

import dataclasses
from collections import Counter, defaultdict
from collections.abc import Callable

from cta.datasets.model import CommandEvent

Key = Callable[[CommandEvent], str]


def by_line(e: CommandEvent) -> str:
    return e.line


def by_program(e: CommandEvent) -> str:
    return e.program


def hide_command(e: CommandEvent) -> CommandEvent:
    """The context a predictor is allowed to see: everything except the command."""
    return dataclasses.replace(e, line="")


class Predictor:
    name = "base"

    def __init__(self, key: Key = by_line) -> None:
        self.key = key

    def rank(self, context: CommandEvent) -> list[str]:
        """All known candidates, best first."""
        raise NotImplementedError

    def update(self, event: CommandEvent) -> None:
        raise NotImplementedError


class MostRecent(Predictor):
    """Recency: the most recently used distinct commands first."""

    name = "recency"

    def __init__(self, key: Key = by_line) -> None:
        super().__init__(key)
        self._order: dict[str, int] = {}
        self._t = 0

    def rank(self, context: CommandEvent) -> list[str]:
        return sorted(self._order, key=self._order.__getitem__, reverse=True)

    def update(self, event: CommandEvent) -> None:
        self._t += 1
        self._order[self.key(event)] = self._t


class MostFrequent(Predictor):
    """Frequency: the commands used most often so far, ties broken by recency."""

    name = "frequency"

    def __init__(self, key: Key = by_line) -> None:
        super().__init__(key)
        self._counts: Counter[str] = Counter()
        self._last: dict[str, int] = {}
        self._t = 0

    def rank(self, context: CommandEvent) -> list[str]:
        return sorted(self._counts, key=lambda c: (self._counts[c], self._last[c]), reverse=True)

    def update(self, event: CommandEvent) -> None:
        self._t += 1
        k = self.key(event)
        self._counts[k] += 1
        self._last[k] = self._t


class Frecency(Predictor):
    """Frequency with exponential decay, so old habits fade (a common shell-tool heuristic)."""

    name = "frecency"

    def __init__(self, key: Key = by_line, half_life: float = 50.0) -> None:
        super().__init__(key)
        self._decay = 0.5 ** (1.0 / half_life)
        self._score: dict[str, float] = {}
        self._at: dict[str, int] = {}
        self._t = 0

    def rank(self, context: CommandEvent) -> list[str]:
        t, d = self._t, self._decay

        def score(c: str) -> float:
            return self._score[c] * d ** (t - self._at[c])

        return sorted(self._score, key=score, reverse=True)

    def update(self, event: CommandEvent) -> None:
        self._t += 1
        k = self.key(event)
        old = self._score.get(k, 0.0) * self._decay ** (self._t - self._at.get(k, self._t))
        self._score[k] = old + 1.0
        self._at[k] = self._t


class Markov(Predictor):
    """Sequence: what usually follows the previous ``order`` commands, backing off to frecency."""

    def __init__(self, key: Key = by_line, order: int = 1) -> None:
        super().__init__(key)
        self.order = order
        self.name = f"markov-{order}"
        self._next: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
        self._recent: list[str] = []
        self._fallback = Frecency(key)

    def rank(self, context: CommandEvent) -> list[str]:
        state = tuple(self._recent[-self.order :])
        primary = []
        if len(state) == self.order:
            primary = [c for c, _ in self._next[state].most_common()]
        return _merge(primary, self._fallback.rank(context))

    def update(self, event: CommandEvent) -> None:
        k = self.key(event)
        state = tuple(self._recent[-self.order :])
        if len(state) == self.order:
            self._next[state][k] += 1
        self._recent.append(k)
        self._fallback.update(event)


class ContextFrequency(Predictor):
    """Frequency conditioned on a context attribute (e.g. working directory).

    Backs off to frecency when the current context value has not been seen.
    """

    def __init__(self, attribute: str, key: Key = by_line) -> None:
        super().__init__(key)
        self.attribute = attribute
        self.name = f"context:{attribute}"
        self._counts: dict[object, Counter[str]] = defaultdict(Counter)
        self._fallback = Frecency(key)

    def rank(self, context: CommandEvent) -> list[str]:
        value = getattr(context, self.attribute)
        primary = [c for c, _ in self._counts[value].most_common()] if value is not None else []
        return _merge(primary, self._fallback.rank(context))

    def update(self, event: CommandEvent) -> None:
        value = getattr(event, self.attribute)
        if value is not None:
            self._counts[value][self.key(event)] += 1
        self._fallback.update(event)


def _merge(primary: list[str], fallback: list[str]) -> list[str]:
    seen = set(primary)
    return primary + [c for c in fallback if c not in seen]
