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

**Decision.** The assistant targets bash 4.4+ on Linux, including remote servers over SSH. Zsh, fish and PowerShell are out of scope; macOS is supported only with a modern bash installed. This narrows the PDD, which planned bash and zsh.

**Why.** Supervisor feedback: POSIX is the base command line, bash is the standard shell built on it, and PowerShell is not POSIX-compatible. Bash is also the default on the Linux servers the project targets, and focusing on one shell leaves more time for prediction and evaluation.

## D6 — Build on bash's own line editor and history (11 Nov 2026)

**Decision.** Suggestions and history recall are delivered through bash's own mechanisms: readline key bindings (`bind -x`), programmable Tab completion (`complete`), the `PROMPT_COMMAND` hook for recording, and `~/.bash_history` as a starting history. Task 4 compares the concrete options, including whether inline grey suggestions are possible within readline.

**Why.** Supervisor feedback asked how bash already does completion and history recall. Building on them keeps the assistant familiar, lightweight and installable on any server with bash.

## D7 — Next-word prediction as language modelling (11 Nov 2026)

**Decision.** Treat predicting the next word of a command as a language-modelling problem: n-gram models over command words as the traditional technique (P4), and a neural language model as the AI component (P5).

**Why.** Supervisor feedback suggested using NLP mechanisms for "what comes next". This fits the analysis: word-by-word completion is where most keystrokes are saved (D3), and the existing sequence predictor is already a simple n-gram model over whole commands.
