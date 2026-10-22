"""One-command demo: run DonePile on the bundled messy-notes sample.

    python demo.py

Prints a screenshot-able done-list to the terminal and writes demo-output.md.
"""
from __future__ import annotations

from pathlib import Path

from donepile.engine import DEFAULT_MODEL_PATH, ensure_model, extract_tasks, load_llm
from donepile.render import render_markdown, render_text

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT / "samples" / "messy-notes.txt"


def main() -> int:
    notes = SAMPLE.read_text(encoding="utf-8")
    print("=" * 64)
    print("DONEPILE DEMO — the dreaded task: sorting a messy pile of notes")
    print("=" * 64)
    print("\n--- INPUT: messy notes --------------------------------------\n")
    print(notes)
    model_path = ensure_model(DEFAULT_MODEL_PATH)
    print(f"--- Loading local model: {model_path.name} (CPU, llama.cpp)\n")
    llm = load_llm(model_path)
    tasks, raw = extract_tasks(llm, notes)
    print("--- RAW MODEL OUTPUT (JSON) ---------------------------------\n")
    print(raw)
    print("\n--- OUTPUT: your done-list ----------------------------------\n")
    print(render_text(tasks))
    out = ROOT / "demo-output.md"
    out.write_text(render_markdown(tasks, source_name=SAMPLE.name), encoding="utf-8")
    print(f"\nMarkdown version written to {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
