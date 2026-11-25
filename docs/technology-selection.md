# Technique and technology selection (Task 4, objective P2)

**Status:** 25 Nov 2026. Each section lists the options, the evidence, and the decision. Scores are 1 (poor) to 3 (good). Decisions are also recorded in [decisions.md](decisions.md) (D13–D17).

## Summary

| Question | Decision |
|---|---|
| How suggestions appear in zsh | A custom strategy for zsh-autosuggestions, plus a zsh completion function for Tab and one widget for on-request AI |
| How the engine stays fast | One resident Python engine per user, which zsh queries over a Unix socket with its built-in `zsocket` |
| How commands are split into words | POSIX option parsing plus subcommands learned from history; zsh's completion definitions used live where available |
| Traditional prediction | Whole lines ranked by frecency, the previous command and context weights; words predicted by an n-gram model over parsed words |
| AI component | Qwen2.5-Coder-0.5B (provisional), run locally with llama.cpp; hosted model only as an opt-in for on-request generation |

## 1. How suggestions appear in zsh

| Option | Inline as you type (F2) | Effort | Fair comparison with the zsh-autosuggestions baseline | Control |
|---|---|---|---|---|
| A. Own line-editor (ZLE) widgets drawing grey text | 3 | 1 | 2 | 3 |
| B. Custom strategy for zsh-autosuggestions | 3 | 3 | 3 | 2 |
| C. Tab completion only | 1 | 3 | 1 | 2 |

zsh-autosuggestions (MIT licence) lets a plugin add a strategy: a function `_zsh_autosuggest_strategy_<name>` that receives what has been typed and sets `suggestion`. The plugin already draws the grey text (`POSTDISPLAY` with `region_highlight`), fetches suggestions in a background subshell so typing never waits, and accepts a whole suggestion or one word at a time (`forward-word`).

**Decision: B.** A strategy named `cta` asks the engine for the suggestion. In the user study, the "with assistant" and baseline conditions then look and behave identically, so only suggestion quality differs. Tab (F3) uses a zsh completion function that lists the engine's top candidates, and on-request AI generation (F10) uses its own widget. If the plugin blocks a feature, the fallback is option A.

## 2. How the engine stays fast

Measured in the cloud workspace (2 CPUs, Python 3.13, zsh 5.9), using the KYPO history (13,704 commands, 5,179 distinct lines). Script: `bench/engine_latency.zsh`.

| Option | Median | 95th percentile |
|---|---|---|
| A. Start Python for every keystroke, before doing any work | 37–46 ms | 52–66 ms |
| B. Resident engine, queried directly from zsh with `zsocket` | 0.06 ms | 0.09 ms |
| C. Resident engine, queried from a background subshell (as zsh-autosuggestions does) | 0.4 ms | 0.6 ms |

Option A uses the whole 50 ms budget (N1) on start-up alone. A compiled engine (for example in Rust) was also considered, but is not needed: with a resident process, about 49 ms of the budget is left for prediction.

**Decision: a resident Python engine**, one per user, started on first use. It listens on a Unix socket in the user's runtime directory, readable only by that user, and zsh talks to it with `zsocket`, which needs no new process. The measurement will be repeated on the development laptop in Iteration 1, and a compiled engine is reconsidered only if P4 misses N1.

## 3. How commands are split into words

| Option | Handles `nmcli dev wifi list` | Runs in the offline replay | Works for any tool | Effort |
|---|---|---|---|---|
| P1. Words by position (Task 3 baseline) | 1 | 3 | 3 | 3 |
| P2. POSIX options and operands | 1 | 3 | 3 | 3 |
| P3. P2 plus subcommands learned from history | 2 | 3 | 3 | 2 |
| P4. P2 plus zsh's completion definitions, queried live | 3 | 1 | 2 | 1 |

POSIX utility syntax separates options from operands (`ls -la /tmp` is options `-la` and operand `/tmp`, and `--` ends the options), but treats `nmcli dev wifi list` as three plain operands. P3 learns, for each program, which leading words recur as subcommands (`nmcli device wifi list`), so it works on any tool and in the replay harness. P4 also knows abbreviations such as `dev` and valid options, but only for tools whose completion definitions are installed, and only in a live zsh.

**Decision: P3 in the engine**, so that the replay evaluation and live use behave the same. **P4 is used live** for Tab, which zsh already provides, and to expand abbreviations when a completion definition exists.

## 4. Traditional prediction

Evidence from Task 3 on KYPO (227 users):

| Technique | Top-1 next command | Keystrokes saved, whole lines |
|---|---|---|
| Recency (zsh-autosuggestions `history`) | 6.2% | 12.8% |
| Recency after the previous command (`match_prev_cmd`) | 7.7% | 12.9% |
| Frecency (frequency with decay) | 10.7% | 13.1% |
| Previous command (Markov-1) | 11.2% | 13.0% |
| Filtering by working directory | −1.4 pp against frecency | — |
| + Word-by-word completion, any of the above | — | 29.9–30.1% |

**Decision:** whole lines are ranked by a weighted score of frecency, the previous command, and context signals (directory, host, exit status, Git state). Context adds weight but never filters (D4), and the weights are tuned on a training split. Words are predicted by an n-gram model with back-off over parsed words, conditioned on the program and its subcommands, for both the current word (F6) and the next word (F7). That gives three traditional techniques to compare in P7: frecency, n-gram sequence models, and context weighting.

## 5. AI component

| Option | Size | Licence | Knows shell commands | Fits the 300 ms re-ranking budget | Privacy |
|---|---|---|---|---|---|
| L1. Qwen2.5-Coder-0.5B-Instruct | 0.40 GB (Q4_K_M) | Apache-2.0 | 3 (trained on code) | 2 (to measure) | 3 |
| L2. SmolLM2-360M-Instruct | ~362M parameters | Apache-2.0 | 2 | 3 | 3 |
| L3. ~1B models (e.g. Gemma 3 1B, TinyLlama 1.1B) | 0.6–0.8 GB | Mixed | 2 | 1 | 3 |
| H. Hosted model API | — | Commercial | 3 | 1 (network delay) | 1 (opt-in only) |

Published CPU-only tests on an older laptop show ~1B models generating about 19–28 tokens/s and reading prompts at about 80–96 tokens/s, while a 0.6B model generated about 35 tokens/s. Re-ranking must therefore stay small: score only the top 3–5 candidates and reuse the shared context.

**Decision (provisional): L1 through llama.cpp** (via `llama-cpp-python`) inside the resident engine, for re-ranking and on-request generation. L2 is the fallback if L1 misses 300 ms. A hosted model is only an opt-in for on-request generation, never for re-ranking, because of network delay, cost and privacy. Models could not be downloaded in the cloud workspace, so the choice is confirmed by a short test on the development laptop in December: load time, memory, time to re-rank 5 candidates, and time to generate 20 tokens.

## Risks introduced

- **Depending on zsh-autosuggestions.** It is widely used and MIT-licensed, and its last update was June 2025. Mitigation: the strategy is a thin layer, and option A remains the fallback.
- **AI speed on the development laptop.** Mitigation: the December test, the smaller fallback model, and re-ranking that never delays the traditional suggestion (N2).

## Sources

- zsh-autosuggestions source code and README: https://github.com/zsh-users/zsh-autosuggestions
- Qwen2.5-Coder-0.5B-Instruct GGUF files and licence: https://huggingface.co/tensorblock/Qwen2.5-Coder-0.5B-Instruct-GGUF
- SmolLM2-360M-Instruct summary: https://dev.co/ai/llms/smollm2-360m-instruct
- CPU-only benchmarks of small models: https://itsfoss.com/testing-local-llms-without-gpu
- POSIX utility syntax: IEEE and The Open Group (2024), see [references.md](references.md)
