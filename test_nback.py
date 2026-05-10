"""
Headless tests for N-back logic (no PsychoPy / display required).
Run: python3 test_nback.py
"""

import random, csv, os, io, sys
from collections import Counter

# ── Replicate constants & functions under test ─────────────────────────────────
LETTERS     = list("BCDFGHJKLMNPQRST")
TARGET_PROP = 0.30

def generate_sequence(n, n_trials):
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

# ── Test helpers ───────────────────────────────────────────────────────────────
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
results = []

def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 1. generate_sequence: length ===")
for n in [1, 2]:
    for t in [10, 12, 25]:
        seq, targets = generate_sequence(n, t)
        check(f"n={n}, trials={t}: len(seq)=={t}",    len(seq) == t)
        check(f"n={n}, trials={t}: len(targets)=={t}", len(targets) == t)

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 2. generate_sequence: first N items are never targets ===")
for n in [1, 2]:
    RUNS = 1000
    violations = 0
    for _ in range(RUNS):
        _, targets = generate_sequence(n, 25)
        if any(targets[:n]):
            violations += 1
    check(f"n={n}: first {n} items never target over {RUNS} runs",
          violations == 0, f"{violations} violations")

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 3. generate_sequence: targets match n-back item ===")
for n in [1, 2]:
    RUNS = 500
    violations = 0
    for _ in range(RUNS):
        seq, targets = generate_sequence(n, 25)
        for i, is_target in enumerate(targets):
            if is_target and seq[i] != seq[i - n]:
                violations += 1
    check(f"n={n}: every target == seq[i-n] over {RUNS} runs",
          violations == 0, f"{violations} mismatches")

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 4. generate_sequence: non-targets differ from n-back item ===")
for n in [1, 2]:
    RUNS = 500
    violations = 0
    for _ in range(RUNS):
        seq, targets = generate_sequence(n, 25)
        for i in range(n, len(seq)):
            if not targets[i] and seq[i] == seq[i - n]:
                violations += 1
    check(f"n={n}: no non-target == seq[i-n] over {RUNS} runs",
          violations == 0, f"{violations} violations")

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 5. generate_sequence: target proportion in plausible range ===")
for n in [1, 2]:
    RUNS = 2000
    all_props = []
    for _ in range(RUNS):
        _, targets = generate_sequence(n, 25)
        eligible = targets[n:]           # first n are structurally lure-free
        prop = sum(eligible) / len(eligible) if eligible else 0
        all_props.append(prop)
    mean_prop = sum(all_props) / len(all_props)
    # With TARGET_PROP=0.30, mean should be very close to 0.30
    check(f"n={n}: mean target prop in [0.25, 0.35] over {RUNS} runs",
          0.25 <= mean_prop <= 0.35, f"mean={mean_prop:.3f}")

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 6. generate_sequence: only valid letters ===")
for n in [1, 2]:
    RUNS = 200
    invalid = 0
    for _ in range(RUNS):
        seq, _ = generate_sequence(n, 25)
        invalid += sum(1 for l in seq if l not in LETTERS)
    check(f"n={n}: all stimuli in LETTERS over {RUNS} runs",
          invalid == 0, f"{invalid} invalid")

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 7. generate_sequence: handles n == n_trials edge case ===")
try:
    seq, targets = generate_sequence(n=5, n_trials=5)
    check("n==n_trials: returns without crash, no targets",
          len(seq) == 5 and not any(targets))
except Exception as e:
    check("n==n_trials: returns without crash", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 8. generate_sequence: handles n=1 trials=2 (minimal valid) ===")
try:
    seq, targets = generate_sequence(n=1, n_trials=2)
    check("n=1, trials=2: length correct", len(seq) == 2)
    check("n=1, trials=2: first item never target", not targets[0])
except Exception as e:
    check("n=1, trials=2: no crash", False, str(e))

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 9. CSV output integrity ===")
FIELDS = ["participant_id", "age", "block", "n_level", "trial",
          "stimulus", "is_target", "response", "correct", "rt_ms"]

buf = io.StringIO()
writer = csv.DictWriter(buf, fieldnames=FIELDS)
writer.writeheader()

seq, targets = generate_sequence(2, 25)
for i, (stim, is_target) in enumerate(zip(seq, targets)):
    writer.writerow({
        "participant_id": "TEST01",
        "age":            "22",
        "block":          "2-back",
        "n_level":        2,
        "trial":          i + 1,
        "stimulus":       stim,
        "is_target":      int(is_target),
        "response":       0,
        "correct":        int(not is_target),  # no response = correct only on non-targets
        "rt_ms":          ""
    })

buf.seek(0)
rows = list(csv.DictReader(buf))
check("CSV: 25 data rows written",          len(rows) == 25)
check("CSV: all FIELDS present",            set(rows[0].keys()) == set(FIELDS))
check("CSV: trial numbers 1..25",           [int(r["trial"]) for r in rows] == list(range(1, 26)))
check("CSV: is_target values are 0 or 1",   all(r["is_target"] in ("0","1") for r in rows))
check("CSV: rt_ms blank on no-response",    all(r["rt_ms"] == "" for r in rows))
check("CSV: stimuli match generated seq",   [r["stimulus"] for r in rows] == seq)

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 10. Correctness logic: correct = (response == is_target) ===")
cases = [
    # (response, is_target, expected_correct)
    (True,  True,  True),   # hit
    (False, False, True),   # correct rejection
    (True,  False, False),  # false alarm
    (False, True,  False),  # miss
]
for resp, tgt, expected in cases:
    correct = (resp == tgt)
    label = {(True,True):"hit", (False,False):"CR", (True,False):"FA", (False,True):"miss"}[(resp,tgt)]
    check(f"correct logic — {label}", correct == expected)

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 11. LETTERS: no vowels, no duplicates ===")
vowels = set("AEIOU")
check("LETTERS: no vowels",     not vowels.intersection(LETTERS))
check("LETTERS: no duplicates", len(LETTERS) == len(set(LETTERS)))
check("LETTERS: all uppercase", all(l.isupper() for l in LETTERS))

# ══════════════════════════════════════════════════════════════════════════════
print("\n=== 12. Stress test: 10,000 sequence generations ===")
crashes = 0
for _ in range(10_000):
    try:
        generate_sequence(random.choice([1,2]), random.randint(5, 40))
    except Exception:
        crashes += 1
check("10,000 random generate_sequence calls: zero crashes",
      crashes == 0, f"{crashes} crashes")

# ══════════════════════════════════════════════════════════════════════════════
total  = len(results)
passed = sum(results)
failed = total - passed
print(f"\n{'═'*50}")
print(f"  {passed}/{total} passed  |  {failed} failed")
print(f"{'═'*50}\n")
sys.exit(0 if failed == 0 else 1)
