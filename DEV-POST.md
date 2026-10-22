---
title: "DonePile: I Let an Open-Weight Model Do the Task I Dread Most — Sorting My Messy Notes"
published: false
tags: devchallenge, hf26challenge
# Submission for the Hacktoberfest Week 3 "Slow and Steady" Open Source AI Challenge.
# Participant: Raymonds Mason (@billythompsons on DEV)
# Deadline: October 25, 2026, 11:59 PM PDT
# Repo: https://github.com/billythompsons/donepile · Demo output: https://github.com/billythompsons/donepile/blob/main/evidence/SMOKE-TEST.md
---

*This is a submission for the Hacktoberfest "Slow and Steady" Challenge — Week 3: Open Source AI, on DEV.*

## What I Built

**DonePile — Notes to Done List.**

Everyone has the pile. Mine looks like this: half-finished meeting notes,
a brain-dump typed at midnight, "sarah said she can fix it by friday??",
"renew the domain before it expires on the 28th!!", "CALL THE DENTIST".
The dreaded task isn't doing the tasks — it's the 20+ minutes of re-reading,
rewriting, assigning and prioritising it takes to turn that pile into a list
you can actually act on. So I automated exactly that dreaded step.

DonePile takes a messy pile of notes and returns a clean, prioritised
done-list: every actionable item extracted, with an **owner**, a **due
day/date as written in the notes**, and a **priority** (High / Medium / Low),
grouped and checkbox-ready in Markdown or in a tiny local web UI.

And it does it **entirely on my own machine, on CPU, with an open-weight
model**. No cloud, no API key, no account, no per-token meter — because
meeting notes and brain dumps are precisely the text I don't want to paste
into someone else's cloud.

## Demo

- 📦 Code: https://github.com/billythompsons/donepile
- ▶️ Live demo / demo output: https://github.com/billythompsons/donepile/blob/main/evidence/SMOKE-TEST.md

Fastest demo (one command, on the bundled messy sample):

```bash
python demo.py
```

Real input (excerpt, from `samples/messy-notes.txt`):

```text
ok so website landing page hero text is still wrong, sarah said she can fix it by friday??
mike: api keys are expiring, he needs to rotate them before monday or the demo breaks
renew the domain before it expires on the 28th!! costs like $12 just do it
```

Real output: the smoke test in the repo (`evidence/SMOKE-TEST.md`) saves the
exact raw model output and the rendered done-list from an actual run —
**13 tasks extracted locally** (about 40 seconds on a small 2-core VM; a typical
laptop is faster), including:

- **Rotate API keys** — Owner: Mike · Due: monday · High
- **Send invoice to client** — Owner: Priya · Due: wednesday · High
- **Renew domain** — Owner: Me · Due: 28th · High
- **Team lunch order** — Owner: Alex · Due: thursday morning · Low

There's also a local web UI if you prefer paste-and-click:

```bash
python app.py   # then open http://127.0.0.1:8765
```

Full recorded demo output: see `demo-output.md` and `evidence/SMOKE-TEST.md` in the repo — both are files, captured from a real run, not mock-ups.

## Code

https://github.com/billythompsons/donepile

```bash
git clone https://github.com/billythompsons/donepile
cd donepile
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # builds llama-cpp-python (needs a C compiler + cmake)
python demo.py                    # first run downloads the model once (~1.07 GB)
python -m donepile.cli your-notes.txt -o done.md
```

Project layout:

```text
donepile/engine.py   # local inference: model download, llama.cpp load, extraction prompt, JSON parsing
donepile/render.py   # deterministic formatting only: dedupe, priority sort, Markdown/text, effort-saved estimate
donepile/cli.py      # command-line interface
app.py               # local web UI (Python standard library only)
demo.py              # one-command demo on the bundled sample
samples/messy-notes.txt
tests/               # helper tests (no model needed)
evidence/SMOKE-TEST.md  # real input -> raw model output -> rendered list
```

## How I Built It

**Open-weight model at the core:** Qwen2.5-1.5B-Instruct (Apache-2.0), in
GGUF Q4_K_M format (~1.07 GB). Small enough to run happily on an ordinary
laptop CPU, capable enough to read a messy pile and understand "he needs to
rotate them before monday" means *Mike owns the API keys, due Monday*.

**Open-source AI harness:** llama.cpp, via `llama-cpp-python` (MIT). It loads
the GGUF weights, runs chat-completion inference on CPU threads, and after
the one-time model download the whole thing works **fully offline**.

**The technique is mostly a strict prompt + honest plumbing:**

1. A system prompt that demands *only* a JSON array of
   `{task, owner, due, priority}` objects — every actionable item, nothing
   invented, no prose — plus one small worked example.
2. **Chunking:** the pile is fed to the model 4 lines at a time. I first
   tried one big call (and a 0.5B model); owners and dates drifted to the
   wrong lines. Small models keep them attached far more reliably on short
   inputs — that one change took the output from mush to a list I'd
   actually use.
3. Low temperature (0.1), because this is extraction, not poetry.
4. A tolerant parser that validates each item and normalises priorities.

**An honesty note I want in the open:** the extraction — the actual reading
and understanding — is the model's work. The only deterministic code after it
drops *exact* duplicates, sorts High → Medium → Low, and formats the output.
There is no rule-based fallback dressed up as AI; if the model isn't there,
DonePile says so and tells you how to download it.

**Limitations, plainly:** a 1.5B model is still a small brain. In my smoke
test it extracted 13 solid tasks but skipped the groceries line and folded
"the Q4 slides" into "Get chart from Ben", and it can pick a priority I'd
set differently. I treat
the output as an excellent first draft that takes me from *dread* to *list*
in about a minute of CPU time — then I skim and adjust. Dates are extracted as written
("friday", "the 28th"); it doesn't set calendar reminders. Yet.

## Why Does Open Innovation Matter?

DonePile exists only because two open things met: a capable
instruction-tuned model published under **Apache-2.0**, and a community
harness (**llama.cpp**, MIT) that makes open weights run anywhere — including
a modest CPU with no GPU and no cloud bill.

That changes who gets to build what. "AI that quietly does the boring parts
of life" shouldn't require an API key, a subscription, or handing a company
your private notes. Open weights mean the tool can be inspected, run
offline, forked, and improved by anyone — and a weekend Hacktoberfest
project by one person can stand on the same model a large company uses.
That's the whole spirit of open source, now applied to AI itself: the
capability is shared, so the laziness can be too.

## Lazy Payoff

My estimate is deliberately transparent (it's a formula in
`donepile/render.py`, not marketing): manually sorting a pile costs roughly
**1.5 minutes per item + 5 minutes of initial sorting**. A typical 14-item
pile is **~24.5 minutes saved — every single time the pile forms**, plus the
bigger, unmeasurable payoff: the pile stops being a thing I dread and
avoid, so the tasks on it actually get done.

Less time re-reading my own mess. More time doing — or, in the spirit of
Slow and Steady, *not* doing. 🦥

## Prize Categories

Submitting for the Hacktoberfest Week 3 "Slow and Steady" Open Source AI
Challenge overall / featured consideration — a brand-new project built with
an open-weight model and open-source AI tooling at its core, automating a
dreaded task and rewarding a little well-earned laziness.
