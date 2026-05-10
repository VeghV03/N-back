# N-back Working Memory Task

A minimal, clean implementation of the N-back task in PsychoPy, measuring working memory updating via 1-back and 2-back conditions.

---

## What it measures

The N-back task (Kirchner, 1958) is a continuous performance task targeting the **central executive** component of working memory — specifically the *updating* function. Participants monitor a sequence of stimuli and respond when the current item matches the one presented N positions earlier.

Higher N demands greater maintenance and manipulation of information in working memory, producing reliable load-dependent accuracy and RT costs.

---

## Requirements

- Python 3.8+
- PsychoPy

```bash
pip install psychopy
```

---

## Running the task

```bash
python nback_task.py
```

A dialog will prompt for **Participant ID** and **Age** before the task begins.

---

## Task structure

| Phase | N | Trials | Feedback | Saved to CSV |
|---|---|---|---|---|
| Practice | 1-back | 12 | Yes | No |
| Block 1 | 1-back | 25 | No | Yes |
| Block 2 | 2-back | 25 | No | Yes |

**Timing per trial:** 500 ms stimulus → 1500 ms blank (total 2000 ms). Response window spans both phases; only the first SPACE press is recorded. Press **Escape** at any time to quit.

---

## Output

Data are saved to `data/nback_<ID>_<timestamp>.csv` automatically.

| Column | Description |
|---|---|
| `participant_id` | Entered at dialog |
| `age` | Entered at dialog |
| `block` | `1-back` or `2-back` |
| `n_level` | 1 or 2 |
| `trial` | Trial number within block |
| `stimulus` | Letter shown |
| `is_target` | 1 if n-back match, 0 otherwise |
| `response` | 1 if SPACE pressed, 0 otherwise |
| `correct` | 1 if response == is_target |
| `rt_ms` | Reaction time in milliseconds (blank if no response) |

---

## Design notes

- **Consonants only** (`BCDFGHJKLMNPQRST`) — vowels excluded to prevent phonological rhyming between letters, which would artificially inflate phonological loop involvement.
- **Non-targets are guaranteed to differ** from their n-back item — eliminates accidental near-targets from the non-target pool.
- **~30% target proportion** — below 50% to reduce response bias toward pressing; the first N trials per block are structurally lure-free (no n-back item exists yet) and are excluded from the target draw.
- **`event.clearEvents()`** called before every response window and every instruction screen — prevents buffered keypresses from earlier phases bleeding through.
- **`feedback` TextStim pre-created** outside the trial loop — avoids re-allocating an OpenGL texture on every practice trial.
- **`try/finally` block** — guarantees `win.close()` and `core.quit()` execute even if the participant presses Escape mid-block.

---

## Suggested analyses

- **Accuracy** (`correct`) by `n_level` — paired t-test or repeated-measures ANOVA
- **RT** (`rt_ms`, hits only) by `n_level`
- **d-prime** — `hits = is_target=1 & response=1`; `false alarms = is_target=0 & response=1`; apply standard SDT formula

---

## Reference

Kirchner, W. K. (1958). Age differences in short-term retention of rapidly changing information. *Journal of Experimental Psychology*, *55*(4), 352–358.
