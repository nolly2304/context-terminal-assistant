import math

import pytest

from cta.analysis import patterns as P
from cta.analysis import predictors as R
from cta.datasets.model import CommandEvent, History


def hist(*lines, cwd=None):
    return History("u", [CommandEvent("u", i, line, cwd=cwd) for i, line in enumerate(lines)])


def test_recurrence_rate():
    assert P.recurrence_rate(hist("ls", "ls", "pwd", "ls")) == pytest.approx(0.5)
    assert P.recurrence_rate(hist("ls -l", "ls -a"), R.by_program) == pytest.approx(0.5)
    assert math.isnan(P.recurrence_rate(hist()))


def test_mru_coverage_counts_novel_commands_as_misses():
    # a b a c b: predictions for b(novel) a(pos 2) c(novel) b(pos 3)
    cov = P.mru_coverage(hist("a", "b", "a", "c", "b"), depth=3)
    assert cov == pytest.approx([0.0, 0.25, 0.5])


def test_predictors_never_see_the_answer():
    class Spy(R.Predictor):
        name = "spy"

        def rank(self, context):
            assert context.line == ""
            return []

        def update(self, event):
            pass

    P.top_k_accuracy(hist("a", "b", "c"), lambda: Spy())
    P.keystroke_savings(hist("a", "b"), lambda: Spy(), word_completion=True)


def test_markov_learns_sequences():
    h = hist(*(["git add .", "git commit", "ls"] * 5))
    markov = P.top_k_accuracy(h, lambda: R.Markov(order=1), ks=(1,))[1]
    recency = P.top_k_accuracy(h, R.MostRecent, ks=(1,))[1]
    assert markov > 0.7
    assert recency == 0.0  # the next command is never the previous one


def test_context_frequency_uses_directory():
    events = []
    for i in range(10):
        d = "/repo" if i % 2 == 0 else "/srv"
        events.append(CommandEvent("u", i, "git pull" if d == "/repo" else "tail log", cwd=d))
    h = History("u", events)
    ctx = P.top_k_accuracy(h, lambda: R.ContextFrequency("cwd"), ks=(1,))[1]
    assert ctx > 0.8


def test_keystroke_savings_hand_checked():
    # Worked by hand in docs/analysis/method.md
    h = hist("git status", "git status", "git push origin main", "git push origin dev")
    assert P.keystroke_savings(h, R.Frecency) == pytest.approx(9 / 59)
    assert P.keystroke_savings(h, R.Frecency, word_completion=True) == pytest.approx(20 / 59)


def test_keystroke_savings_never_negative():
    h = hist("a", "b", "c")
    assert P.keystroke_savings(h, R.Frecency, accept_cost=5, word_completion=True) >= 0


def test_paired_difference_and_points():
    d = P.paired_difference([0.5, 0.6, 0.7], [0.4, 0.5, 0.6])
    assert d.mean == pytest.approx(0.1)
    assert "significant" in d.points()
    s = P.summarise([0.2, 0.4])
    assert 0 <= s.low <= s.mean <= s.high <= 1
