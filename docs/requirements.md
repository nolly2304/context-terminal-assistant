# Requirements specification (draft for supervisor review)

**Project:** LBS-26-1112 Context-based Terminal Assistant · **Objective:** P1 · **Status:** draft v0.1, 2 Nov 2026, to be agreed with Jan Springer by 13 Nov 2026

Priorities use MoSCoW: **Must** (needed for the project to succeed), **Should** (expected, but the project still succeeds without it), **Could** (only if time allows), **Won't** (out of scope). Each requirement traces to a PDD objective. Evidence refers to the [usage-pattern analysis](analysis/usage-patterns.md).

## 1. Users and situations

| Situation | Example | What it needs |
|---|---|---|
| Developer on their own machine | Long-term use in many project folders on a Mac or Linux laptop | Learns personal habits; directory and Git context |
| Engineer on a remote Linux server over SSH | Running `systemctl`, `journalctl`, `docker`, `kubectl` on a server | Works in a plain POSIX environment; nothing leaves the server |
| Newcomer to a system | First hour on an unfamiliar server (closest to the KYPO data) | Useful with little history; completes options and arguments, not just whole lines |

## 2. Functional requirements

| ID | Requirement | Priority | Objective |
|---|---|---|---|
| F1 | Record each command with its context (§4) into a local store, as it is run | Must | P6 |
| F2 | Show an inline suggestion while the user types, in zsh and bash | Must | P6 |
| F3 | Accept a suggestion only with an explicit key; never run anything automatically | Must | P6 |
| F4 | Suggest whole command lines matching what has been typed | Must | P4 |
| F5 | Complete the current word (program, option or argument) when no whole line fits, using POSIX utility syntax to separate options from operands | Must | P4 |
| F6 | Suggest a likely next command at an empty prompt | Should | P4 |
| F7 | Combine traditional predictors and the AI component into one ranked list (hybrid ranking) | Must | P5 |
| F8 | AI component runs locally by default; a hosted model can be used only after the user opts in, and only after secrets are redacted | Must | P5 |
| F9 | Let the user exclude directories or commands from recording, and delete all stored data with one command | Must | P6 |
| F10 | Each predictor and context signal can be switched on or off by configuration, for evaluation | Must | P3, P7 |
| F11 | On-demand mode (suggest on a key press) as a fallback where inline suggestions are too slow or unsupported | Should | P6 |
| F12 | Import existing shell history so suggestions are useful from day one | Should | P4 |
| F13 | Work in any POSIX shell for recording and on-demand suggestions; full inline integration for zsh and bash | Should | P6 |
| F14 | Warn before accepting a destructive or high-risk command (e.g. `rm -rf /`, `dd`, `mkfs`) | Could | S1 |
| F15 | Natural-language mode: describe a task, get a command | Could | S2 |
| F16 | fish shell support; installable package | Could | S4 |
| F17 | Windows support | Won't | — |

## 3. Non-functional requirements

| ID | Requirement | Priority | How it is checked |
|---|---|---|---|
| N1 | Traditional suggestions: median ≤ 50 ms, 95th percentile ≤ 100 ms from keystroke to suggestion, on the development laptop | Must | Timing in the replay harness and in the shell |
| N2 | AI suggestions never block typing; they arrive within 1 s or are dropped | Must | Timing; manual test |
| N3 | No network traffic in the default configuration | Must | Network monitoring during a scripted session |
| N4 | Secrets are redacted before anything is stored or sent (passwords in flags, tokens, keys, credentials in URLs) | Must | Test suite of seeded secrets: all must be redacted |
| N5 | Local store readable only by the user (file mode 0600) | Must | Automated test |
| N6 | Works on macOS and on Linux, including a remote Linux server over SSH | Must | CI on both; manual SSH test |
| N7 | Resident memory of the background process ≤ 200 MB without a local model | Should | Measured |
| N8 | All core modules covered by unit tests; CI runs on every push | Must | CI |

## 4. Candidate context signals

The PDD asks for at least six. Evidence so far comes from the public datasets; signals the datasets do not record are tested on my own logged history once the replay harness (P3) exists.

| # | Signal | Available in | Evidence so far | Decision |
|---|---|---|---|---|
| C1 | Characters typed so far (prefix) | All | The core of inline suggestion. On KYPO, adding word-by-word completion raises keystrokes saved from 13.1% to 29.9% (+16.8 pp, significant) | Must |
| C2 | Previous command(s) | All | On Schonlau, a first-order sequence model predicts the next program far better than frecency (57.6% vs 21.3% top-1, +36.4 pp, significant), though script-launched chains inflate this. On KYPO full lines the gain is small (11.2% vs 10.7%) | Must |
| C3 | Working directory | KYPO, own | On KYPO, filtering by directory *lowered* top-1 accuracy by 1.4 pp (significant). Trainees use a median of 3 directories in short sessions, so per-directory data is sparse. Expected to matter more for long-term use across projects, and as a re-weighting signal rather than a filter | Should; re-test on own history |
| C4 | Host (machine) | KYPO, own | No gain on KYPO (median 1 host per trainee); matters when one history spans laptop and servers | Should; re-test |
| C5 | Exit status of the last command | Own only | Not in public data. A failed command is often retried or corrected | Should; measure in P3 |
| C6 | Git state (in a repo, branch, uncommitted changes) | Own only | Not in public data. Strong prior for `git` commands | Should; measure in P3 |
| C7 | Time since the last command (session start) | KYPO, own | Not yet analysed | Could |
| C8 | Files in the working directory | Live only | For completing file arguments | Could |

## 5. Evaluation targets (fixed before any experiment, per PDD §11)

| Measure | Target |
|---|---|
| Next-command top-1 / top-3 accuracy | Hybrid at least matches the best traditional baseline |
| Keystrokes saved (replay) | ≥ 25% overall. Whole-line suggestion alone reaches only 13% on KYPO; word-by-word completion reaches 30%, so the target is realistic only with F5 |
| Latency | As N1 and N2 |
| Privacy | As N3 and N4 |
| Usability | SUS ≥ 68; fewer keystrokes and shorter task times with the assistant |

## 6. Questions for the supervisor

1. Is word-by-word completion with POSIX parsing (F5) the right reading of the POSIX suggestion?
2. The public data shows little benefit from directory context. Is it acceptable to rely on my own logged history to test C3–C6, given it is one user?
3. Should bash inline suggestions be a Must? Bash has no built-in inline suggestion support, so this may need a fallback (F11).
