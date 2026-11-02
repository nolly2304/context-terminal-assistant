import json

import pytest

from cta.datasets import kypo, schonlau, shell_history


def _write_kypo(path, records):
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def test_kypo_sorts_by_time_and_skips_metasploit(tmp_path):
    group = tmp_path / "Some game"
    group.mkdir()
    _write_kypo(group / "sandbox-7-useractions.json", [
        {"timestamp_str": "2021-02-08T14:02:52+01:00", "cmd": "nmap 10.0.0.1", "wd": "/home/u",
         "hostname": "attacker", "cmd_type": "bash-command"},
        {"timestamp_str": "2021-02-08T14:02:45+01:00", "cmd": "ls", "wd": "/home/u",
         "hostname": "attacker", "cmd_type": "bash-command"},
        {"timestamp_str": "2021-02-08T14:03:00+01:00", "cmd": "use exploit/x",
         "hostname": "attacker", "cmd_type": "msf-command"},
        {"timestamp_str": "2021-02-08T14:03:05+01:00", "cmd": "   ", "hostname": "attacker",
         "cmd_type": "bash-command"},
    ])
    [h] = kypo.load(tmp_path, prefix="t")
    assert h.user == "t/Some_game/sandbox-7"
    assert [e.line for e in h] == ["ls", "nmap 10.0.0.1"]
    assert [e.index for e in h] == [0, 1]
    assert h.events[0].cwd == "/home/u" and h.events[0].host == "attacker"

    [with_msf] = kypo.load(tmp_path, include_msf=True)
    assert len(with_msf) == 3


def test_schonlau_drops_masquerade_blocks(tmp_path):
    users, per_user = schonlau.USERS, schonlau.PER_USER
    (tmp_path / "mask.dat").write_text(
        "\n".join(f"u{u}" for u in range(users) for _ in range(per_user)) + "\n")
    rows = [["0"] * users for _ in range(100)]
    rows[0][0] = "1"  # user 1's first post-training block is a masquerade
    (tmp_path / "summary.dat").write_text("\n".join(" ".join(r) for r in rows) + "\n")

    hs = schonlau.load(tmp_path)
    assert len(hs) == users
    assert len(hs[0]) == per_user - schonlau.BLOCK
    assert len(hs[1]) == per_user
    assert {e.line for e in hs[3]} == {"u3"}


def test_schonlau_rejects_wrong_size(tmp_path):
    (tmp_path / "mask.dat").write_text("ls\n")
    (tmp_path / "summary.dat").write_text("")
    with pytest.raises(ValueError):
        schonlau.load(tmp_path)


def test_zsh_extended_history_with_multiline(tmp_path):
    f = tmp_path / "zsh_history"
    f.write_text(": 1700000000:0;git status\n"
                 ": 1700000005:2;for f in *; do\\\necho $f\\\ndone\n"
                 ": 1700000009:0;ls\n")
    h = shell_history.load(f)
    assert [e.line for e in h] == ["git status", "for f in *; do\necho $f\ndone", "ls"]
    assert h.events[0].timestamp is not None
    assert [e.index for e in h] == [0, 1, 2]


def test_bash_history_with_and_without_timestamps(tmp_path):
    f = tmp_path / "bash_history"
    f.write_text("#1700000000\nls -la\ncd /tmp\n\n")
    h = shell_history.load(f)
    assert [e.line for e in h] == ["ls -la", "cd /tmp"]
    assert h.events[0].timestamp is not None
    assert h.events[1].timestamp is None
