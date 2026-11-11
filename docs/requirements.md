# Requirements specification

**Project:** LBS-26-1112 Context-based Terminal Assistant · **Objective:** P1 · **Status:** draft v0.2, 11 Nov 2026, for agreement with Jan Springer by 13 Nov 2026

Priorities use MoSCoW: **Must** (needed for the project to succeed), **Should** (expected, but the project still succeeds without it), **Could** (only if time allows), **Won't** (out of scope). Each requirement traces to a PDD objective. Evidence refers to the [usage-pattern analysis](analysis/usage-patterns.md).

## Changes since v0.1, following supervisor feedback

- **Bash only.** The assistant targets bash, the standard shell on Linux and the closest to the POSIX base shell. Zsh, fish and PowerShell are out of scope.
- **Built on bash's own mechanisms.** Suggestions and history recall go through bash's line editor (readline): Tab completion, key bindings and the history file, rather than a separate tool.
- **Next-word prediction.** Predicting what comes next uses language-modelling techniques from NLP: n-gram models over the words of a command, with the AI component as the more advanced model.
- **Example tasks added** (§5), including network management with `nmcli` and renaming many files by a pattern.

## 1. Users and situations

| Situation | Example | What it needs |
|---|---|---|
| Developer on their own Linux machine | Long-term use of bash in many project folders | Learns personal habits; directory and Git context |
| Engineer on a remote Linux server over SSH | Running `systemctl`, `journalctl`, `nmcli`, `docker` on a server | Works with a standard bash; nothing leaves the server |
| Newcomer to a system | First hour on an unfamiliar server (closest to the KYPO data) | Useful with little history; completes options and arguments, not just whole lines |

## 2. Functional requirements

| ID | Requirement | Priority | Objective |
|---|---|---|---|
| F1 | Record each command with its context (§4) into a local store as it is run, using bash's prompt hook (`PROMPT_COMMAND`) | Must | P6 |
| F2 | Offer suggestions while the user types, through bash's line editor: a key binding that fills in the best suggestion, and Tab completion (bash programmable completion, `complete`) that lists the top candidates | Must | P6 |
| F3 | Show the suggestion inline, greyed out after the cursor, if this can be done within bash's line editor (decided in Task 4) | Should | P6 |
| F4 | Accept a suggestion only with an explicit key; never run anything automatically | Must | P6 |
| F5 | Suggest whole command lines that match what has been typed | Must | P4 |
| F6 | Complete the current word (program, option or argument), using POSIX utility syntax to tell options from operands, e.g. `nmcli dev` → `nmcli device` | Must | P4 |
| F7 | Predict the next word from the words typed so far with an n-gram language model over command words, e.g. after `nmcli device wifi` suggest `connect` or `list` | Must | P4 |
| F8 | Context-aware history recall: a better version of Ctrl+R and the up arrow that ranks past commands by relevance to the current context, using `~/.bash_history` and the local store | Should | P4 |
| F9 | Suggest a likely next command at an empty prompt | Should | P4 |
| F10 | An AI component (a language model) proposes or re-ranks suggestions, combined with the traditional predictors in one ranked list (hybrid ranking) | Must | P5 |
| F11 | AI component runs locally by default; a hosted model is used only after the user opts in, and only after secrets are redacted | Must | P5 |
| F12 | Let the user exclude directories or commands from recording, and delete all stored data with one command | Must | P6 |
| F13 | Each predictor and context signal can be switched on or off by configuration, for evaluation | Must | P3, P7 |
| F14 | Import existing `~/.bash_history` so suggestions are useful from day one | Should | P4 |
| F15 | Warn before accepting a destructive or high-risk command (e.g. `rm -rf /`, `dd`, `mkfs`) | Could | S1 |
| F16 | Natural-language mode: describe a task ("rename all .jpeg files to .jpg"), get a command | Could | S2 |
| F17 | Zsh, fish, PowerShell or Windows support | Won't | — |

## 3. Non-functional requirements

| ID | Requirement | Priority | How it is checked |
|---|---|---|---|
| N1 | Traditional suggestions: median ≤ 50 ms, 95th percentile ≤ 100 ms from key press to suggestion | Must | Timing in the replay harness and in bash |
| N2 | AI suggestions never block typing; they arrive within 1 s or are dropped | Must | Timing; manual test |
| N3 | No network traffic in the default configuration | Must | Network monitoring during a scripted session |
| N4 | Secrets are redacted before anything is stored or sent (passwords in flags, tokens, keys, credentials in URLs) | Must | Test suite of seeded secrets: all must be redacted |
| N5 | Local store readable only by the user (file mode 0600) | Must | Automated test |
| N6 | Works with bash 4.4 or later on Linux, including on a remote server over SSH | Must | CI on Linux; manual SSH test |
| N7 | Records and suggests standard POSIX command syntax; relies only on bash features available in bash 4.4+ | Must | Tests against bash 4.4 and 5.x |
| N8 | Works on macOS when a modern bash (4.4+) is installed | Could | Manual test |
| N9 | Resident memory of the background process ≤ 200 MB without a local model | Should | Measured |
| N10 | All core modules covered by unit tests; CI runs on every push | Must | CI |

## 4. Candidate context signals

The PDD asks for at least six. Evidence so far comes from the public datasets; signals they do not record are tested on my own bash history once the replay harness (P3) exists.

| # | Signal | Available in | Evidence so far | Decision |
|---|---|---|---|---|
| C1 | What has been typed so far (characters and words) | All | The core of suggestion. On KYPO, adding word-by-word completion raises keystrokes saved from 13.1% to 29.9% (+16.8 pp, significant) | Must |
| C2 | Previous command(s) | All | On Schonlau, a first-order sequence model predicts the next program far better than frecency (57.6% vs 21.3% top-1, +36.4 pp, significant), though script-launched chains inflate this. On KYPO full lines the gain is small (11.2% vs 10.7%) | Must |
| C3 | Working directory | KYPO, own | On KYPO, filtering by directory *lowered* top-1 accuracy by 1.4 pp (significant). Trainees use a median of 3 directories in short sessions, so per-directory data is sparse. Expected to matter more for long-term use, as a re-weighting signal rather than a filter | Should; re-test on own history |
| C4 | Host (machine) | KYPO, own | No gain on KYPO (median 1 host per trainee); matters when one history spans a laptop and servers | Should; re-test |
| C5 | Exit status of the last command | Own only | Not in public data. A failed command is often retried or corrected | Should; measure in P3 |
| C6 | Git state (in a repository, branch, uncommitted changes) | Own only | Not in public data. Strong prior for `git` commands | Should; measure in P3 |
| C7 | Time since the last command (session start) | KYPO, own | Not yet analysed | Could |
| C8 | Files in the working directory | Live only | For completing file arguments, e.g. in rename commands | Could |

## 5. Example tasks

These tasks are used in the replay evaluation and the user study (P7, P8). They are chosen because the commands are long, hard to remember, or easy to get wrong.

| Task | Typical commands |
|---|---|
| Network management | `nmcli device status`, `nmcli device wifi list`, `nmcli device wifi connect <SSID> password <pw>`, `nmcli connection show` |
| Renaming many files by a pattern | `rename 's/\.jpeg$/.jpg/' *.jpeg`, or `for f in *.jpeg; do mv -- "$f" "${f%.jpeg}.jpg"; done` |
| Version control | `git status`, `git add`, `git commit -m "…"`, `git push origin <branch>` |
| Services and logs on a server | `systemctl status <service>`, `journalctl -u <service> --since today`, `tail -f /var/log/syslog` |

Renaming is a useful test because Linux has two different `rename` tools with different syntax (the Perl version and the util-linux version), so the right suggestion depends on the system.

## 6. Evaluation targets (fixed before any experiment, per PDD §11)

| Measure | Target |
|---|---|
| Next-command top-1 / top-3 accuracy | Hybrid at least matches the best traditional baseline |
| Keystrokes saved (replay) | ≥ 25% overall. Whole-line suggestion alone reaches only 13% on KYPO; word-by-word completion reaches 30%, so the target is realistic only with F6 and F7 |
| Latency | As N1 and N2 |
| Privacy | As N3 and N4 |
| Usability | SUS ≥ 68; fewer keystrokes and shorter task times with the assistant |

## 7. Questions for the supervisor

1. The public datasets do not record exit status or Git state. Is it acceptable to test those signals (C5, C6) on my own bash history, given it is one user?
2. Is renaming files by a pattern meant as an example task (as in §5), or as a feature the assistant should support directly (F16)?
3. Are you happy to agree these requirements?
