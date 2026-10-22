# DonePile — Extra Verification Checks

_Run 2026-10-22 on the same machine as the smoke test, after
`evidence/SMOKE-TEST.md` passed. These prove DonePile is not fitted to the
bundled sample: both inputs below were written fresh for these checks._

## 1. CLI on unseen input

Input (`/tmp/fresh-notes.txt`):

```text
tom to review the PR by tomorrow morning, its blocking release
book flights for the conference, prices go up friday
water the plants while im away next week
```

Command: `python -m donepile.cli fresh-notes.txt -o fresh-done.md` → exit 0

Actual output:

```text
DONEPILE — 3 tasks extracted locally
==============================================
[ ] (High  ) Book flights  —  Me · friday
[ ] (High  ) Review the PR  —  Tom · tomorrow morning
[ ] (Low   ) Water the plants  —  Me · next week
==============================================
Estimated manual effort saved: ~9.5 minutes
```

Owner (Tom), due ("tomorrow morning", "friday") and urgency (blocking
release → High) all extracted correctly from text the project has never seen.

## 2. Local web UI (`python app.py`, http://127.0.0.1:8765)

- `GET /` returned the page (`<title>DonePile — Notes to Done List</title>`).
- `POST /` with `notes=lena will ship the report by monday, its urgent`
  returned "Your done-list (1 tasks)" with the task card **"Ship the report"**.
- A first version of the UI had a real bug (CSS braces vs `str.format`,
  `KeyError: 'font-family'`); it was found by this check, fixed by switching
  to token replacement, and re-verified as above.

## 3. Deterministic helper tests

`python tests/test_parse_and_render.py` → 5/5 PASS
(parse fields, fence tolerance, dedupe + priority sort, Markdown rendering,
effort-saved estimate).
