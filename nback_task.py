#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
N-back Working Memory Task
Conditions: 1-back (practice + experimental), 2-back (experimental)
Response key: SPACE
Output: data/nback_<ID>_<timestamp>.csv
"""

from psychopy import visual, core, event, gui
import random, csv, os
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────────
LETTERS          = list("BCDFGHJKLMNPQRST")  # consonants only — prevents vowel rhyming artefacts
STIM_DURATION    = 0.5    # seconds stimulus visible
ISI              = 1.5    # seconds blank screen after stimulus
N_LEVELS         = [1, 2] # experimental conditions, presented in order
TRIALS_PER_BLOCK = 25     # includes first N lure-free trials
PRACTICE_TRIALS  = 12
TARGET_PROP      = 0.30   # proportion of eligible (non-lure-free) trials that are targets

# ── Participant dialog ─────────────────────────────────────────────────────────
dlg = gui.Dlg(title="N-back Task")
dlg.addField("Participant ID:")
dlg.addField("Age:")
info = dlg.show()
if not dlg.OK:
    core.quit()
participant_id, age = info[0], info[1]

# ── Output ─────────────────────────────────────────────────────────────────────
os.makedirs("data", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename  = f"data/nback_{participant_id}_{timestamp}.csv"
FIELDS    = ["participant_id", "age", "block", "n_level", "trial",
             "stimulus", "is_target", "response", "correct", "rt_ms"]

# ── Window & stimuli ───────────────────────────────────────────────────────────
win       = visual.Window([1200, 800], color="black", units="height", fullscr=False)
stim_text = visual.TextStim(win, text="",  height=0.15, color="white", bold=True)
msg       = visual.TextStim(win, text="",  height=0.04, color="white", wrapWidth=1.0)
feedback  = visual.TextStim(win, text="",  height=0.06)  # pre-created; text/color set per trial

# ── Sequence generation ────────────────────────────────────────────────────────
def generate_sequence(n, n_trials):
    """
    Returns (sequence, is_target) of length n_trials.
    First n items are never targets (no n-back item to match yet).
    Non-targets are guaranteed to differ from their n-back item.
    """
    seq     = [random.choice(LETTERS) for _ in range(n)]
    targets = [False] * n
    for i in range(n, n_trials):
        if random.random() < TARGET_PROP:
            seq.append(seq[i - n])
            targets.append(True)
        else:
            opts = [l for l in LETTERS if l != seq[i - n]]
            seq.append(random.choice(opts))
            targets.append(False)
    return seq, targets

# ── Trial ──────────────────────────────────────────────────────────────────────
def run_trial(stim):
    """
    Stimulus for STIM_DURATION → blank for ISI.
    Response window spans both phases; only first SPACE counted.
    Raises SystemExit on Escape.
    Returns (responded: bool, rt_ms: float | None).
    """
    t_clock = core.Clock()
    responded = False
    rt_ms     = None
    event.clearEvents()

    # Stimulus phase
    stim_text.text = stim
    stim_text.draw()
    win.flip()
    while t_clock.getTime() < STIM_DURATION:
        for k, t in event.getKeys(keyList=["space", "escape"], timeStamped=t_clock):
            if k == "escape":
                raise SystemExit
            if k == "space" and not responded:
                responded = True
                rt_ms = round(t * 1000, 1)

    # ISI phase — blank screen
    win.flip()
    while t_clock.getTime() < STIM_DURATION + ISI:
        for k, t in event.getKeys(keyList=["space", "escape"], timeStamped=t_clock):
            if k == "escape":
                raise SystemExit
            if k == "space" and not responded:
                responded = True
                rt_ms = round(t * 1000, 1)

    return responded, rt_ms

# ── Block ──────────────────────────────────────────────────────────────────────
def run_block(n, n_trials, writer, block_label, practice=False):
    seq, targets = generate_sequence(n, n_trials)
    for i, (stim, is_target) in enumerate(zip(seq, targets)):
        responded, rt_ms = run_trial(stim)
        correct = (responded == is_target)

        if practice:
            feedback.text  = "Correct!" if correct else "Incorrect"
            feedback.color = "lime"     if correct else "red"
            feedback.draw()
            win.flip()
            core.wait(0.5)
            win.flip()
            core.wait(0.2)

        if writer is not None:
            writer.writerow({
                "participant_id": participant_id,
                "age":            age,
                "block":          block_label,
                "n_level":        n,
                "trial":          i + 1,
                "stimulus":       stim,
                "is_target":      int(is_target),
                "response":       int(responded),
                "correct":        int(correct),
                "rt_ms":          rt_ms if rt_ms is not None else ""
            })

# ── Instructions ───────────────────────────────────────────────────────────────
def show_instructions(text):
    event.clearEvents()   # discard any buffered keypresses before waiting
    msg.text = text
    msg.draw()
    win.flip()
    event.waitKeys(keyList=["space"])

# ── Main ───────────────────────────────────────────────────────────────────────
try:
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

        show_instructions(
            "N-BACK TASK\n\n"
            "A letter appears on screen, one at a time.\n"
            "Press SPACE if it matches the letter from 1 step ago.\n\n"
            "Example:   F  →  R  →  F  ← press SPACE here\n\n"
            "Feedback is shown during practice.\n"
            "Press Escape at any time to quit.\n\n"
            "Press SPACE to begin practice."
        )
        run_block(n=1, n_trials=PRACTICE_TRIALS, writer=None,
                  block_label="practice", practice=True)

        for n in N_LEVELS:
            show_instructions(
                f"{n}-BACK\n\n"
                f"Press SPACE when the letter matches the one from {n} step(s) ago.\n\n"
                "No feedback this time.\n\n"
                "Press SPACE to begin."
            )
            run_block(n=n, n_trials=TRIALS_PER_BLOCK, writer=writer,
                      block_label=f"{n}-back")

        show_instructions("Task complete. Thank you!\n\nPress SPACE to exit.")

except SystemExit:
    pass
finally:
    win.close()
    core.quit()
