# Analysis method

How each measure in [usage-patterns.md](usage-patterns.md) is calculated. The code is in `src/cta/analysis/`.

## Measures

- **Recurrence rate.** For one user, (commands − distinct commands) ÷ commands: the share of commands that repeat an earlier one exactly (Greenberg, 1993). Calculated for full lines and for program names (the first word, skipping `sudo` and `VAR=value` assignments).
- **Last-k coverage.** How often the next command is among the k most recently used *distinct* commands. This is what a plain "recent commands" list would achieve.
- **Top-k accuracy.** Each predictor ranks every command it has seen so far; a hit is when the true next command is in its top k. Predictions are made *online*: the predictor sees the context of the current command (directory, host, time) but its command line is blanked, and it only learns the command after predicting it. This avoids any leakage from the future.
- **Keystrokes saved.** A character-by-character simulation of inline suggestions. Before each keystroke, the best-ranked known command starting with what has been typed is shown; if it is the command the user wanted, the user accepts it for one keystroke. With *word-by-word completion*, the current word can also be completed from the words seen in the same position after the same program. Enter is ignored because it is pressed either way. Savings = 1 − keystrokes typed ÷ characters needed.
- **Statistics.** Every measure is computed per user, then averaged, so heavy users do not dominate. Intervals are 95% normal-approximation confidence intervals. Comparisons are *paired* (the same users under both methods); a difference is reported as significant when its interval excludes zero.

## Worked example for keystrokes saved

History: `git status`, `git status`, `git push origin main`, `git push origin dev` (59 characters). Frecency predictor, accept costs 1.

| Command | Whole-line only | + word-by-word |
|---|---|---|
| `git status` (10) | nothing known yet: 10 | 10 |
| `git status` (10) | suggested immediately: 1 | 1 |
| `git push origin main` (20) | `git status` is suggested until `git p`, then nothing matches: 20 | accept `git` (1), space (1), type `push origin main` because `status` is the only known 2nd word (16): 18 |
| `git push origin dev` (19) | `git status` ranks above `git push origin main`, and that line is wrong anyway: 19 | accept `git` (1), space (1), `p` (1), accept `push` (1), space (1), accept `origin` (1), space (1), type `dev` (3): 10 |
| **Total typed** | **50 → 9/59 = 15.3% saved** | **39 → 20/59 = 33.9% saved** |

The unit test `test_keystroke_savings_hand_checked` asserts exactly these numbers.

## Limitations

- **Schonlau** comes from process accounting: it includes programs launched by scripts, not just typed ones, and has no arguments. Its recurrence and accuracy figures are therefore higher than for typed commands.
- **KYPO** sessions are short (median about 60 commands), task-driven and done by learners on an unfamiliar network. A long-term user would repeat more, so these are pessimistic estimates for repetition and keystroke savings.
- **Word-by-word completion** here uses word position only. Real POSIX parsing (separating options from operands) should do better; that is part of P4.
- Neither public dataset records **exit status** or **Git state**, so those signals cannot be measured until my own logged history and the replay harness (P3) exist.
