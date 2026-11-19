# Decision log

Short records of design and technology decisions, with the evidence behind them. Task 4 (P2) adds the scored technology comparison here, and section 11.2 of the PDD evaluates these decisions at the end of the project.

## D1 — Python for analysis and prototyping (2 Nov 2026)

**Decision.** Use Python 3.10+ for the analysis, replay harness and prototype engine, as proposed to the supervisor.

**Why.** Fast to write, good for data analysis, and the libraries for the AI component are Python-first.

**Open question for P2.** Python takes about 20–50 ms just to start, so it cannot be launched on every keystroke within the 50 ms target. The likely answer is a long-running local process that the shell talks to, but this is decided in Task 4 with measurements.

## D2 — Datasets for usage-pattern analysis (2 Nov 2026)

**Decision.** Use the Schonlau et al. (2001) masquerade data and the KYPO cybersecurity-training logs (Švábenský et al., 2021; Ošlejšek et al., 2023), plus my own history locally.

**Why.** Schonlau gives long-term habits from 50 users but only program names. KYPO gives full command lines with working directory, host and time, but from short task-driven sessions. Each covers the other's weakness. Greenberg's (1988) traces would be ideal (full lines, directory, errors, long-term) but need written permission from the author; requested separately.

## D3 — Predict word by word, not only whole lines (2 Nov 2026)

**Decision.** The engine will complete the current word (program, then options and arguments) as well as whole command lines.

**Why.** In the KYPO data, only 30% of full command lines repeat, against 69% of programs. Simulated keystroke savings rise from 13.1% with whole-line suggestions to 29.9% with word-by-word completion (+16.8 pp, significant across 227 users). Only the latter meets the PDD's 25% target. See [analysis/usage-patterns.md](analysis/usage-patterns.md). This is also where POSIX utility syntax (IEEE and The Open Group, 2024) comes in, as suggested by the supervisor.

## D4 — Context signals re-weight suggestions rather than filter them (2 Nov 2026)

**Decision.** In the hybrid ranker (P4/P5), context such as the working directory will add to a candidate's score rather than restrict the candidates to those seen in that context.

**Why.** On KYPO, a predictor that ranked commands by their frequency in the current directory was significantly *worse* than one ignoring the directory (−1.4 pp top-1). Splitting short histories by directory leaves too little data per directory. A blended score keeps the user's overall habits and lets context nudge the ranking. To be confirmed on my own long-term history, where directory may be more informative.

## D5 — Bash only (11 Nov 2026)

**Status.** Superseded by D12 (18 Nov 2026).

**Decision.** The assistant targets bash 4.4+ on Linux, including remote servers over SSH. Zsh, fish and PowerShell are out of scope; macOS is supported only with a modern bash installed. This narrows the PDD, which planned bash and zsh.

**Why.** Supervisor feedback: POSIX is the base command line, bash is the standard shell built on it, and PowerShell is not POSIX-compatible. Bash is also the default on the Linux servers the project targets, and focusing on one shell leaves more time for prediction and evaluation.

## D6 — Build on bash's own line editor and history (11 Nov 2026)

**Status.** Superseded by D12 (18 Nov 2026).

**Decision.** Suggestions and history recall are delivered through bash's own mechanisms: readline key bindings (`bind -x`), programmable Tab completion (`complete`), the `PROMPT_COMMAND` hook for recording, and `~/.bash_history` as a starting history. Task 4 compares the concrete options, including whether inline grey suggestions are possible within readline.

**Why.** Supervisor feedback asked how bash already does completion and history recall. Building on them keeps the assistant familiar, lightweight and installable on any server with bash.

## D7 — Next-word prediction as language modelling (11 Nov 2026)

**Decision.** Treat predicting the next word of a command as a language-modelling problem: n-gram models over command words as the traditional technique (P4), and a neural language model as the AI component (P5).

**Why.** Supervisor feedback suggested using NLP mechanisms for "what comes next". This fits the analysis: word-by-word completion is where most keystrokes are saved (D3), and the existing sequence predictor is already a simple n-gram model over whole commands.

## D8 — A minimum core, with later stages dropped from the end if late (18 Nov 2026)

**Decision.** The core is bash on a local Linux machine with recording, the traditional engine, key-binding and Tab suggestions, AI re-ranking, privacy controls, and the full evaluation (offline replay, heuristic evaluation, user study). Inline grey suggestions (Stage 2), SSH (Stage 3), macOS (Stage 4) and the secondary objectives follow in that order. See requirements §2.

**Why.** Supervisor feedback: requiring all eight objectives on 12–15 hours a week is risky, and the old contingency only dropped secondary objectives. With stages, a late feature never threatens the core or the evaluation.

## D9 — Over SSH, everything runs on the server (18 Nov 2026)

**Decision.** In the SSH case, the shell integration, recorder, store and traditional engine run on the server, where the shell runs. The AI component runs there only if the server has enough memory; otherwise it is off. Nothing beyond normal terminal traffic crosses the connection. A laptop-side model reached through an SSH tunnel is not planned; it would be opt-in with redaction only.

**Why.** Supervisor feedback: history must stay on the machine where the shell runs, a free-tier server cannot run even a small model, and running the model on the laptop would send context off the server. Keeping the traditional engine small (≤ 200 MB, N9) means the useful part works on any server.

## D10 — The AI component re-ranks, and generates only on request (18 Nov 2026)

**Decision.** The language model re-ranks the traditional engine's top candidates (replacing the suggestion only if ready within 300 ms), and generates a command only when the user presses a key for it. It never generates on every keystroke.

**Why.** Supervisor feedback: one second is too slow while typing. Re-ranking keeps typing fast, still lets the evaluation measure what the AI adds, and on-request generation covers commands the user has never typed.

## D11 — Volunteers share aggregate results only (18 Nov 2026; agreed with the supervisor 19 Nov)

**Decision.** Volunteers run the logger and replay harness on their own machines and send only aggregate results. No raw history is collected, released or submitted. The PDD's "anonymised datasets" deliverable becomes "the replay harness and aggregate results".

**Why.** Supervisor feedback: volunteered histories are personal data and may contain secrets even after redaction, and the PDD both promised a dataset and promised deletion. Collecting only aggregates removes the conflict and the risk. Agreed at the supervisor meeting on 19 Nov: volunteers are participants and sign a consent form, and also answer a short usability questionnaire. The costs (no inspection or re-analysis, reruns after a harness bug, results examiners cannot reproduce) are stated in requirements §8.

## D12 — Zsh on Linux is the core; bash becomes Stage 4 (18 Nov 2026)

**Decision.** The core targets zsh 5.8+ on Linux, using zsh's own mechanisms: the line editor (ZLE) for inline suggestions, the completion system for Tab, and the `preexec`/`precmd` hooks for recording. Stages follow in this order: macOS (Stage 2), a remote server over SSH with zsh installed (Stage 3), and bash (Stage 4). This replaces D5 and D6.

**Why.** The supervisor's written feedback (12 Nov) pointed out that inline suggestions are much harder in bash than in zsh, and proposed zsh on Linux as the minimum core with bash, macOS and SSH staged after it. Zsh's line editor supports inline suggestions directly, so the core can include them; bash needs an add-on (ble.sh) for the same thing. The context logger has a version for each shell, so data collection does not depend on this choice. The supervisor's earlier verbal comment was "bash only", so this order is to be confirmed with him.

