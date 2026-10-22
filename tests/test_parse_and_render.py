"""Tests for DonePile's deterministic helpers (parsing + rendering).

These test the formatting layer only — task extraction itself is done by the
local model and is covered by the smoke test in evidence/SMOKE-TEST.md.
Run:  python -m pytest tests/ -q   (or: python tests/test_parse_and_render.py)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from donepile.engine import parse_tasks
from donepile.render import dedupe_and_sort, estimate_minutes_saved, render_markdown

SAMPLE_RAW = """[
  {"task": "Rotate the API keys", "owner": "Mike", "due": "Monday", "priority": "High"},
  {"task": "Call the dentist", "owner": "Me", "due": "No date", "priority": "Low"},
  {"task": "Rotate the API keys", "owner": "Mike", "due": "Monday", "priority": "High"}
]"""


def test_parse_extracts_fields():
    tasks = parse_tasks(SAMPLE_RAW)
    assert len(tasks) == 3
    assert tasks[0]["owner"] == "Mike"
    assert tasks[0]["priority"] == "High"


def test_parse_tolerates_fences():
    tasks = parse_tasks("```json\n" + SAMPLE_RAW + "\n```")
    assert len(tasks) == 3


def test_dedupe_and_sort_high_first():
    tasks = dedupe_and_sort(parse_tasks(SAMPLE_RAW))
    assert len(tasks) == 2  # exact duplicate removed
    assert tasks[0]["priority"] == "High"


def test_render_markdown_groups_and_counts():
    md = render_markdown(parse_tasks(SAMPLE_RAW), source_name="test.txt")
    assert "Rotate the API keys" in md
    assert "🔴 High priority" in md


def test_estimate_is_positive():
    assert estimate_minutes_saved(10) == 20.0  # 10 x 1.5 min + 5 min sorting


if __name__ == "__main__":
    for name, fn in sorted({k: v for k, v in globals().items() if k.startswith("test_")}.items()):
        fn()
        print(f"PASS {name}")
    print("All tests passed.")
