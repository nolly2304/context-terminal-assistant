import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

from cta.datasets import ctalog

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "cta-log.bash"


def _bash_ok() -> bool:
    bash = shutil.which("bash")
    if not bash:
        return False
    out = subprocess.run([bash, "-c", "echo ${BASH_VERSINFO[0]}${BASH_VERSINFO[1]}"],
                         capture_output=True, text=True).stdout.strip()
    return out.isdigit() and int(out) >= 44 and shutil.which("git") is not None


def _run_bash(tmp_path: Path, script: str) -> list[dict]:
    home = tmp_path / "home"
    home.mkdir()
    env = {"HOME": str(home), "HISTFILE": str(home / ".bash_history"), "TERM": "dumb",
           "PATH": os.environ["PATH"]}
    subprocess.run(["bash", "--norc", "--noprofile", "-i"], input=script, text=True,
                   env=env, cwd=tmp_path, capture_output=True, timeout=60)
    log = home / ".local" / "share" / "cta" / "log.jsonl"
    assert stat.S_IMODE(log.stat().st_mode) == 0o600
    return [json.loads(line) for line in log.read_text().splitlines()]


@pytest.mark.skipif(not _bash_ok(), reason="needs bash 4.4+ and git")
def test_logger_records_context_in_a_real_bash(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                    "--allow-empty", "-m", "init"], cwd=repo, check=True)
    records = _run_bash(tmp_path, f"""source {SCRIPT}
echo hello
false
cd {repo}
echo 'quote " and \\\\ backslash'
 echo skipped-with-leading-space

touch x && git add x
ls /nonexistent-path
exit
""")
    cmds = [r["cmd"] for r in records]
    assert cmds == ["echo hello", "false", f"cd {repo}", "echo 'quote \" and \\\\ backslash'",
                    "touch x && git add x", "ls /nonexistent-path"]
    assert [r["exit"] for r in records][:2] == [0, 1]
    assert records[-1]["exit"] != 0
    assert records[2]["cwd"] == str(tmp_path)  # directory when `cd` was typed
    assert records[3]["cwd"] == str(repo)
    assert records[0]["git_branch"] is None
    assert records[3]["git_branch"] and records[3]["git_dirty"] is False
    assert records[-1]["git_dirty"] is True
    assert len({r["session"] for r in records}) == 1


def test_loader_reads_log_and_tolerates_bad_lines(tmp_path):
    log = tmp_path / "log.jsonl"
    log.write_text(
        '{"t":1700000010,"host":"h","session":"s1","cwd":"/r","git_branch":"main",'
        '"git_dirty":false,"exit":1,"cmd":"make test"}\n'
        '{"t":1700000000,"host":"h","session":"s1","cwd":"/r","git_branch":null,'
        '"git_dirty":null,"exit":0,"cmd":"cd /r"}\n'
        '{"t":17000000\n'  # truncated line
        '{"t":1700000020,"host":"h","session":"s2","cwd":"/","exit":0,"cmd":"  "}\n'
    )
    h = ctalog.load(log)
    assert [e.line for e in h] == ["cd /r", "make test"]
    second = h.events[1]
    assert second.exit_status == 1 and second.git_branch == "main" and second.git_dirty is False
    assert second.cwd == "/r" and second.host == "h" and second.timestamp is not None
    assert list(ctalog.sessions(h)) == ["s1"]
