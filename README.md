# Context-based Terminal Assistant

Honours Stage Project **LBS-26-1112** · Oluwapelumi Adunola · BSc Computer Science with Industrial Placement · Supervisor: Jan Springer

A terminal assistant that suggests commands as you type in bash and zsh, on Linux (including remote servers over SSH) and macOS. It learns from your command history and local context (working directory, Git state, the last command and its exit status), and keeps everything on your machine. Traditional prediction techniques (heuristic frequency and recency ranking, POSIX-based command parsing, sequence models) are combined with an AI component, and the project measures how much each technique and each kind of context actually helps.

## Status

| Phase | Objective | Due | Status |
|---|---|---|---|
| Usage-pattern analysis and requirements | P1 | 13 Nov 2026 | In progress: [analysis](docs/analysis/usage-patterns.md), [requirements draft](docs/requirements.md) |
| Technique and technology selection | P2 | 27 Nov 2026 | Not started |
| Evaluation dataset and replay harness | P3 | 18 Dec 2026 | Not started |
| Traditional prediction engine | P4 | 5 Feb 2027 | Not started |
| AI component and hybrid ranking | P5 | 19 Feb 2027 | Not started |
| Shell integration and privacy controls | P6 | 26 Feb 2027 | Not started |
| Offline evaluation | P7 | 26 Mar 2027 | Not started |
| Heuristic evaluation and user study | P8 | 9 Apr 2027 | Not started |

## Repository layout

```
src/cta/datasets/   loaders that convert each dataset into one common format
src/cta/analysis/   usage-pattern analysis and baseline predictors (P1)
tests/              unit tests, run by CI on every push
scripts/            dataset download helpers
docs/               requirements, analysis results, decision log
retros/             a short retrospective at the end of each two-week iteration
data/               local datasets only — ignored by Git, never committed
```

## Getting started

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest

sh scripts/fetch_schonlau.sh          # then download the KYPO data, see data/README.md
cta-analyse                           # regenerates docs/analysis/usage-patterns.md
cta-analyse --own ~/.zsh_history      # optionally include your own history (output stays local)
```

## Data and privacy

This repository is public, so it contains code and aggregate results only. Command histories, participant data and consent forms are never committed (`.gitignore` enforces this). See [data/README.md](data/README.md) for the datasets used and their licences.
