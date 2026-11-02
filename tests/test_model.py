import pytest

from cta.datasets.model import CommandEvent, History, program_name


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("git push origin main", "git"),
        ("sudo apt install nmap", "apt"),
        ("FOO=1 BAR=2 make test", "make"),
        ("/usr/bin/python3 -m venv .venv", "python3"),
        ("echo 'unbalanced", "echo"),
        ("", ""),
        ("   ", ""),
    ],
)
def test_program_name(line, expected):
    assert program_name(line) == expected


def test_history_reports_available_context():
    h = History("u", [CommandEvent("u", 0, "ls"), CommandEvent("u", 1, "pwd", cwd="/tmp")])
    assert h.has("cwd")
    assert not h.has("host")
    assert len(h) == 2
