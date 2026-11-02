"""Measures of how repetitive and predictable command histories are.

All functions work per user and are summarised across users with a mean and a
95% confidence interval, so one heavy user cannot dominate the result.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from cta.analysis.predictors import Key, Predictor, by_line, hide_command
from cta.datasets.model import History


@dataclass(frozen=True)
class Summary:
    mean: float
    low: float
    high: float
    n: int

    def __str__(self) -> str:
        return f"{self.mean:.1%} ({self.low:.1%}–{self.high:.1%})"

    def points(self) -> str:
        """Format a difference of rates in percentage points, e.g. ``+2.1 pp (0.4 to 3.8)``."""
        verdict = "significant" if self.low > 0 or self.high < 0 else "not significant"
        return (f"{self.mean * 100:+.1f} pp (95% CI {self.low * 100:+.1f} to "
                f"{self.high * 100:+.1f}; {verdict}, n={self.n})")


def summarise(values: Sequence[float], clip: bool = True) -> Summary:
    """Mean across users with a 95% confidence interval (normal approximation).

    Use ``clip=False`` for paired differences, which can be negative.
    """
    values = [v for v in values if not math.isnan(v)]
    n = len(values)
    if n == 0:
        return Summary(math.nan, math.nan, math.nan, 0)
    mean = statistics.fmean(values)
    if n < 2:
        return Summary(mean, mean, mean, n)
    half = 1.96 * statistics.stdev(values) / math.sqrt(n)
    low, high = mean - half, mean + half
    if clip:
        low, high = max(0.0, low), min(1.0, high)
    return Summary(mean, low, high, n)


def paired_difference(a: Sequence[float], b: Sequence[float]) -> Summary:
    """Mean per-user difference ``a - b`` with a 95% CI. Significant if the CI excludes 0."""
    pairs = [(x, y) for x, y in zip(a, b, strict=True) if not (math.isnan(x) or math.isnan(y))]
    return summarise([x - y for x, y in pairs], clip=False)


def recurrence_rate(history: History, key: Key = by_line) -> float:
    """Share of commands that repeat an earlier command (Greenberg's recurrence rate)."""
    keys = [key(e) for e in history]
    if not keys:
        return math.nan
    return (len(keys) - len(set(keys))) / len(keys)


def vocabulary(history: History, key: Key = by_line) -> int:
    return len({key(e) for e in history})


def mru_coverage(history: History, key: Key = by_line, depth: int = 10) -> list[float]:
    """For k = 1..depth: share of commands found among the k most recent distinct commands.

    This is the hit rate of simply showing the user their last k distinct commands.
    """
    hits = [0] * depth
    total = 0
    recent: list[str] = []
    for e in history:
        k = key(e)
        if recent:
            total += 1
            if k in recent[:depth]:
                pos = recent.index(k)
                for d in range(pos, depth):
                    hits[d] += 1
        if k in recent:
            recent.remove(k)
        recent.insert(0, k)
    return [h / total if total else math.nan for h in hits]


def top_k_accuracy(history: History, make: Callable[[], Predictor], ks: Iterable[int] = (1, 3)
                   ) -> dict[int, float]:
    """Online next-command accuracy: is the true command in the predictor's top k?"""
    ks = tuple(ks)
    predictor = make()
    hits = Counter()
    total = 0
    for i, e in enumerate(history):
        if i > 0:
            ranking = predictor.rank(hide_command(e))
            truth = predictor.key(e)
            total += 1
            for k in ks:
                if truth in ranking[:k]:
                    hits[k] += 1
        predictor.update(e)
    return {k: hits[k] / total if total else math.nan for k in ks}


def keystroke_savings(history: History, make: Callable[[], Predictor], accept_cost: int = 1,
                      word_completion: bool = False) -> float:
    """Share of keystrokes saved by inline suggestions, simulated character by character.

    Before each keystroke, the best-ranked known command that starts with what has
    been typed so far is shown. As soon as it equals the command the user wanted,
    the user accepts it, paying ``accept_cost`` keystrokes. Enter is ignored, since
    it is pressed either way. The predictor must rank full command lines.

    With ``word_completion``, when no whole-line suggestion is right, the current
    word is also completed from words previously seen in the same position for the
    same program (e.g. the options and arguments of ``nmap``). This approximates
    POSIX-style parsing into program, options and arguments.
    """
    predictor = make()
    words: WordModel | None = WordModel() if word_completion else None
    typed_total = 0
    needed_total = 0
    for e in history:
        line = e.line
        needed_total += len(line)
        ranking = predictor.rank(hide_command(e))
        cost = 0
        pos = 0
        line_possible = True
        while pos < len(line):
            prefix = line[:pos]
            if line_possible:
                suggestion = next((c for c in ranking if c.startswith(prefix)), None)
                if suggestion is None:
                    line_possible = False  # no known line has this prefix; that will not change
                elif suggestion == line:
                    cost += accept_cost
                    pos = len(line)
                    break
            if words is not None:
                end = words.accepted_word_end(line, pos)
                if end is not None:
                    cost += accept_cost
                    pos = end
                    continue
            cost += 1
            pos += 1
        typed_total += min(cost, len(line))
        predictor.update(e)
        if words is not None:
            words.update(line)
    return 1 - typed_total / needed_total if needed_total else math.nan


class WordModel:
    """Counts which words appear at each position of each program's command lines."""

    def __init__(self) -> None:
        self._at: dict[tuple[str, int], Counter[str]] = {}

    def update(self, line: str) -> None:
        tokens = line.split()
        if not tokens:
            return
        for i, tok in enumerate(tokens[1:], start=1):
            self._at.setdefault((tokens[0], i), Counter())[tok] += 1
        self._at.setdefault(("", 0), Counter())[tokens[0]] += 1

    def accepted_word_end(self, line: str, pos: int) -> int | None:
        """If the top suggestion for the word at ``pos`` is correct, return where the word ends.

        Only offered when the suggestion would save more than the cost of accepting it.
        """
        start = line.rfind(" ", 0, pos) + 1
        end = line.find(" ", start)
        end = len(line) if end == -1 else end
        if pos > end:
            return None
        before = line[:start].split()
        program = before[0] if before else ""
        index = len(before)
        counts = self._at.get((program, index)) if before else self._at.get(("", 0))
        if not counts:
            return None
        partial = line[start:pos]
        target = line[start:end]
        best = next((w for w, _ in counts.most_common() if w.startswith(partial)), None)
        if best == target and end - pos > 1:
            return end
        return None


def most_common(histories: Iterable[History], key: Key = by_line, n: int = 15
                ) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for h in histories:
        counts.update(key(e) for e in h)
    return counts.most_common(n)
