"""DonePile command-line interface.

Usage:
    python -m donepile.cli notes.txt [-o done.md] [--model path/to/model.gguf]
    cat notes.txt | python -m donepile.cli -
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .engine import DEFAULT_MODEL_PATH, ensure_model, extract_tasks, load_llm
from .render import render_markdown, render_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="donepile",
        description="Turn messy notes into a clean, prioritised task list — locally, with an open-weight model.",
    )
    parser.add_argument("input", help="Path to a .txt file with messy notes, or '-' for stdin")
    parser.add_argument("-o", "--output", help="Write the Markdown done-list to this file")
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH), help="Path to the GGUF model file")
    parser.add_argument("--show-raw", action="store_true", help="Also print the model's raw JSON output")
    args = parser.parse_args(argv)

    notes = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8")
    if not notes.strip():
        print("No notes given — nothing to do (the laziest outcome of all).", file=sys.stderr)
        return 1

    model_path = ensure_model(Path(args.model))
    print(f"Loading local model: {model_path.name} (CPU, llama.cpp) ...", file=sys.stderr)
    llm = load_llm(model_path)
    print("Reading your pile and extracting tasks ...", file=sys.stderr)
    tasks, raw = extract_tasks(llm, notes)

    if args.show_raw:
        print("\n--- Raw model output ---\n" + raw + "\n------------------------\n")

    print(render_text(tasks))
    if args.output:
        source = "stdin" if args.input == "-" else Path(args.input).name
        Path(args.output).write_text(render_markdown(tasks, source_name=source), encoding="utf-8")
        print(f"\nMarkdown done-list written to {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
