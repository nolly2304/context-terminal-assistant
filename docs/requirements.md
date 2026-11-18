# Requirements specification

**Project:** LBS-26-1112 Context-based Terminal Assistant · **Objective:** P1 · **Status:** draft v0.3, 18 Nov 2026, for agreement with Jan Springer

Priorities use MoSCoW: **Must** (needed for the project to succeed), **Should** (expected, but the project still succeeds without it), **Could** (only if time allows), **Won't** (out of scope). Each requirement traces to a PDD objective and to a delivery stage (§2). Evidence refers to the [usage-pattern analysis](analysis/usage-patterns.md).

## Changes since v0.2, following the written PDD feedback (12 Nov)

- **Zsh on Linux is the core, as you suggested** (§2). Zsh's line editor supports inline suggestions directly, which bash does not. macOS, SSH and bash are added after the core in a fixed order, and dropped from the end if time runs short.
- **Datasets named, with the signals each records** (§6). No public dataset records exit status or Git state, so risk R4 is raised and a context logger now records these on my own use.
- **Where each component runs over SSH** (§5, and the separate one-page sketch). Over SSH everything runs on the server and nothing extra crosses the connection; the AI component runs only where it fits.
- **The AI component's role is fixed**: it re-ranks the traditional engine's candidates, and generates a command only on request (F10). Speed targets exclude network time (N1, N2).
- **What data is released** (§8), the **unit of analysis** (§10), and **real-world baselines** (§9) are now stated.

## 1. Users and situations

| Situation | Example | What it needs |
|---|---|---|
| Developer on their own Linux machine | Long-term use of zsh in many project folders | Learns personal habits; directory and Git context |
| Engineer on a remote Linux server over SSH | Running `systemctl`, `journalctl`, `nmcli`, `docker` on a server | Works on the server's own shell; nothing leaves the server |
| Newcomer to a system | First hour on an unfamiliar server (closest to the KYPO data) | Useful with little history; completes options and arguments, not just whole lines |

## 2. Minimum core and stages

The **core** is what must be delivered and evaluated for the project to succeed. Stages after it are added in this order; if time runs short they are dropped from the end, so the core is never put at risk. The order puts the cheapest stage first (macOS uses the same shell) and the hardest last (inline suggestions in bash need an add-on).

| Stage | What it adds | Planned | If late |
|---|---|---|---|
| **Core** | Zsh on a local Linux machine: recording with context (F1); traditional engine with whole-line, word-by-word and next-word prediction (F5–F7); inline suggestions as you type, plus Tab completion (F2, F3, F4); AI re-ranking and on-request generation (F10, F11); privacy controls (F12); offline evaluation with the replay harness (P3, P7); heuristic evaluation and user study run on the core (P8) | Iterations 1–3, 30 Nov – 19 Feb | Cannot be dropped |
| **Stage 2** | macOS (N8). Zsh is the default shell there, so this is mainly testing | Iteration 4, by 26 Feb | Linux only |
| **Stage 3** | Use on a remote Linux server over SSH, with zsh installed on the server (F18, N6) | Iteration 4, by 26 Feb | Described as future work; user study runs on a local Linux VM |
| **Stage 4** | Bash (F19): the context logger already supports bash; suggestions through a key binding and Tab completion, and inline via ble.sh | Only if ahead, by 26 Mar | Bash users can still contribute data through the logger |
| **Secondary** | S1 destructive-command warnings (F15), S2 natural-language mode (F16), S3 local vs hosted model comparison, S4 packaging | Only after the core is evaluated, by 26 Mar | Dropped |

## 3. Functional requirements

| ID | Requirement | Priority | Stage | Objective |
|---|---|---|---|---|
| F1 | Record each command with its context (§7) into a local store as it is run, using zsh's `preexec` and `precmd` hooks | Must | Core | P6 |
| F2 | Show the best suggestion inline, greyed out after the cursor, as the user types, through zsh's line editor (ZLE) | Must | Core | P6 |
| F3 | List the top candidates through Tab completion (zsh's completion system) and a key binding | Should | Core | P6 |
| F4 | Accept a suggestion only with an explicit key; never run anything automatically | Must | Core | P6 |
| F5 | Suggest whole command lines that match what has been typed | Must | Core | P4 |
| F6 | Complete the current word (program, option or argument), using POSIX utility syntax to tell options from operands, e.g. `nmcli dev` → `nmcli device` | Must | Core | P4 |
| F7 | Predict the next word from the words typed so far with an n-gram language model over command words, e.g. after `nmcli device wifi` suggest `connect` or `list` | Must | Core | P4 |
| F8 | Context-aware history recall: a better Ctrl+R that ranks past commands by relevance to the current context, using the shell history file and the local store | Should | Core | P4 |
| F9 | Suggest a likely next command at an empty prompt | Should | Core | P4 |
| F10 | AI component (a small language model) **re-ranks** the traditional engine's top candidates, and **generates** a command only when the user asks with a key binding. It never generates on every keystroke | Must | Core | P5 |
| F11 | AI component runs locally by default; a hosted model is used only after the user opts in, and only after secrets are redacted | Must | Core | P5 |
| F12 | Let the user exclude directories or commands from recording, pause recording, and delete all stored data with one command | Must | Core | P6 |
| F13 | Each predictor and context signal can be switched on or off by configuration, for evaluation | Must | Core | P3, P7 |
| F14 | Import existing `~/.zsh_history` (and `~/.bash_history`) so suggestions are useful from day one | Should | Core | P4 |
| F15 | Warn before accepting a destructive or high-risk command (e.g. `rm -rf /`, `dd`, `mkfs`) | Could | Secondary | S1 |
| F16 | Natural-language mode: describe a task ("rename all .jpeg files to .jpg"), get a command | Could | Secondary | S2 |
| F17 | fish, PowerShell or Windows support | Won't | — | — |
| F18 | Install and run entirely on a remote Linux server, as described in §5 | Should | 3 | P6 |
| F19 | Bash support: suggestions through a readline key binding and Tab completion (`complete`), and inline via ble.sh | Could | 4 | P6 |

## 4. Non-functional requirements

| ID | Requirement | Priority | Stage | How it is checked |
|---|---|---|---|---|
| N1 | Traditional suggestions: median ≤ 50 ms, 95th percentile ≤ 100 ms, measured on the machine where the shell runs, from key press to suggestion ready. Over SSH this excludes network time, which affects every keystroke equally with or without the assistant | Must | Core | Timing in the replay harness and in the shell |
| N2 | AI re-ranking never delays the traditional suggestion: it replaces it only if ready within 300 ms. On-request generation responds within 2 s on the development laptop | Must | Core | Timing |
| N3 | No network traffic in the default configuration | Must | Core | Network monitoring during a scripted session |
| N4 | Secrets are redacted before anything is stored or sent (passwords in flags, tokens, keys, credentials in URLs) | Must | Core | Test suite of seeded secrets: all must be redacted |
| N5 | Local store readable only by the user (file mode 0600) | Must | Core | Automated test |
| N6 | Works with zsh 5.8 or later on Linux; on a remote server, needs only zsh, Python 3 and no extra network access | Must (local) / Should (SSH) | Core / 3 | CI on Linux; manual SSH test |
| N7 | Records and suggests standard POSIX command syntax, whichever shell is used | Must | Core | Tests |
| N8 | Works on macOS with its default zsh | Should | 2 | Manual test |
| N9 | Background process ≤ 200 MB resident memory without a local model, so it fits a small server | Should | Core | Measured |
| N10 | All core modules covered by unit tests; CI runs on every push | Must | Core | CI |

## 5. Where each component runs

| Component | Local use | Over SSH |
|---|---|---|
| Shell integration (zsh line editor widgets, Tab completion) | Laptop | Server (zsh installed there) |
| Recorder and local store | Laptop | Server |
| Traditional engine | Laptop | Server |
| AI component | Laptop | Server, only if it has enough memory; otherwise switched off. Never on the laptop for a remote shell by default |

Over SSH, only the normal terminal traffic crosses the connection: keystrokes one way and screen output the other, exactly as without the assistant. History and context never leave the server. Sending context back to the laptop's model through an SSH tunnel is possible, but would only be an opt-in with redaction, and is not planned. Details are in the one-page SSH sketch.

## 6. Datasets and the signals they record

| Dataset | Users | Commands | Full command line | Directory | Host | Time | Exit status | Git state | Use |
|---|---|---|---|---|---|---|---|---|---|
| Schonlau et al. (2001) | 50 | 750,000 | No (program name only) | No | No | No | No | No | Long-term repetition and sequences |
| Švábenský et al. (2021), KYPO | 175 | 10,956 bash | Yes | Yes | Yes | Yes | No | No | Prediction and word-by-word completion |
| Ošlejšek et al. (2023), KYPO | 52 | 2,748 bash | Yes | Yes | Yes | Yes | No | No | As above |
| My own shell history, Oct 2026 onwards | 1 | grows | Yes | No | No | If timestamps on | No | No | Personal long-term use |
| My own use with the context logger, from Nov 2026 | 1 | grows | Yes | Yes | Yes | Yes | **Yes** | **Yes** | The only source for exit status and Git state |
| Volunteers with the context logger (§8) | target 5–10 | grows | Yes | Yes | Yes | Yes | Yes | Yes | Generalise the context results |

**Consequence for risk R4.** The context comparison in P7 can test directory, host and time on 227 public users, but exit status and Git state only on my own logged use plus volunteers. R4 (too little or unrepresentative data) is raised from likelihood 3 to 4 (score 16). Mitigation: the context logger (`scripts/cta-log.zsh`, with a bash version) runs on my machines from now, giving about five months of data before P7, and volunteers are recruited in December. Contingency: report exit status and Git state as a single-user case study, and say so.

## 7. Candidate context signals

| # | Signal | Recorded by | Evidence so far | Decision |
|---|---|---|---|---|
| C1 | What has been typed so far (characters and words) | All | The core of suggestion. On KYPO, word-by-word completion raises keystrokes saved from 13.1% to 29.9% (+16.8 pp, significant) | Must |
| C2 | Previous command(s) | All | On Schonlau, a first-order sequence model predicts the next program far better than frecency (57.6% vs 21.3% top-1, +36.4 pp, significant), though script-launched chains inflate this. On KYPO full lines the gain is small (11.2% vs 10.7%) | Must |
| C3 | Working directory | KYPO, logger | On KYPO, filtering by directory *lowered* top-1 accuracy by 1.4 pp (significant): a median of 3 directories in short sessions leaves too little data per directory. To be used as a re-weighting signal, and re-tested on long-term use | Should |
| C4 | Host (machine) | KYPO, logger | No gain on KYPO (median 1 host per trainee); matters when one history spans a laptop and servers | Should |
| C5 | Exit status of the last command | Logger only | Not in any public dataset. A failed command is often retried or corrected | Should |
| C6 | Git state (in a repository, branch, uncommitted changes) | Logger only | Not in any public dataset. Strong prior for `git` commands | Should |
| C7 | Time since the last command (session start) | KYPO, logger | Not yet analysed | Could |
| C8 | Files in the working directory | Live only | For completing file arguments, e.g. in rename commands | Could |

## 8. Data handling and release

- **Released (public repository):** code, the replay harness, download scripts for the public datasets, and aggregate results only. The public datasets themselves are not redistributed; anyone can download them from their original sources.
- **Never released or submitted:** my own logs and any volunteer's history. They stay on the owner's machine or on university-approved storage, are not in the repository, and are deleted by September 2027. The PDD's "anonymised datasets" deliverable is replaced by "the replay harness and aggregate results".
- **Volunteers (proposed, to confirm with the supervisor against the ethics checklist):** volunteers run the logger and the replay harness on their own machine, and send me only the aggregate results (accuracy and keystrokes saved per signal), never their commands. No raw history leaves their machine, so no personal data or secrets are collected. The consent form will say exactly this.

## 9. Baselines

| Baseline | What it does | How it is compared |
|---|---|---|
| zsh-autosuggestions and fish | Suggest the most recent past command that starts with what has been typed. zsh-autosuggestions is the direct real-world comparator for a zsh core | Simulated in the replay harness. On KYPO it saves 12.8% of keystrokes, against 29.9% for frecency with word-by-word completion (+17.1 pp, significant, 227 users) |
| ble.sh auto-complete (bash) | The same history-based strategy, in bash | Same simulation; the likely base for Stage 4 |
| Plain zsh | Tab completion and Ctrl+R history search only | The "without assistant" condition in the user study |
| McFly, Atuin | Ranked history search with some context | Compared with F8 on features; McFly's ranking can be simulated if time allows |

## 10. Evaluation design notes

- **Unit of analysis is the user.** Each measure is computed per user, then compared between methods with paired tests across users, so one user's many sessions are not treated as independent. For my own logged use (one user), the unit is the day, results are reported as a case study, and no general claim is made from it.
- **User study results are descriptive.** With 8–12 participants, task times, keystrokes and SUS are reported with medians, ranges and effect sizes, not significance tests.

## 11. Example tasks

Used in the replay evaluation and the user study. Chosen because the commands are long, hard to remember, or easy to get wrong.

| Task | Typical commands |
|---|---|
| Network management | `nmcli device status`, `nmcli device wifi list`, `nmcli device wifi connect <SSID> password <pw>`, `nmcli connection show` |
| Renaming many files by a pattern | `rename 's/\.jpeg$/.jpg/' *.jpeg`, or `for f in *.jpeg; do mv -- "$f" "${f%.jpeg}.jpg"; done` |
| Version control | `git status`, `git add`, `git commit -m "…"`, `git push origin <branch>` |
| Services and logs on a server | `systemctl status <service>`, `journalctl -u <service> --since today`, `tail -f /var/log/syslog` |

Renaming is a useful test because Linux has two different `rename` tools with different syntax (the Perl version and the util-linux version), so the right suggestion depends on the system.

## 12. Evaluation targets (fixed before any experiment, per PDD §11)

| Measure | Target |
|---|---|
| Next-command top-1 / top-3 accuracy | Hybrid at least matches the best traditional baseline |
| Keystrokes saved (replay) | ≥ 25% overall, and more than the zsh/fish-style baseline |
| Latency | As N1 and N2 |
| Privacy | As N3 and N4 |
| Usability | SUS ≥ 68; fewer keystrokes and shorter task times with the assistant (descriptive) |

## 13. Questions for the supervisor

1. I have followed your written feedback: zsh on Linux is the core, and bash is Stage 4. In our earlier meeting you mentioned bash only, so can you confirm this order?
2. Does the "no further approval" ethics outcome cover volunteers if they share only aggregate results, never their commands (§8)?
3. Is renaming files by a pattern meant as an example task (§11), or as a feature to support directly (F16)?
4. Are you happy to agree these requirements?
