"""Local inference engine for DonePile.

Core: Qwen2.5-1.5B-Instruct (open-weight, Apache-2.0) in GGUF Q4_K_M format,
run entirely on CPU with llama.cpp via llama-cpp-python (MIT).

There is no fallback rule-based "fake AI" path: if the model is not present,
DonePile tells you how to download it and exits. The small deterministic
helpers in render.py only sort / de-duplicate / format what the model
extracted — they never invent tasks.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MODEL_REPO = "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
MODEL_FILE = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODEL_LICENSE = "Apache-2.0 (Qwen2.5 model weights)"
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / MODEL_FILE

SYSTEM_PROMPT = (
    "You extract tasks from messy notes. "
    "Reply with ONLY a JSON array. Each item is an object with keys: "
    '"task" (short imperative sentence), "owner" (person name or "Me"), '
    '"due" (day/date mentioned, or "No date"), '
    '"priority" (one of "High", "Medium", "Low"). '
    "Rules: if a line names a person (e.g. 'anna:', 'ask Ben for...', 'Priya will...'), "
    "that person is the owner — never default to \"Me\" when a name is given. "
    "Copy due days/dates exactly as written (e.g. \"friday\", \"Oct 30\", \"the 28th\"). "
    "A task with a hard deadline, an expiry, or something breaking is High priority. "
    "Ignore headings, warnings like 'DO NOT LOSE', and pure commentary — only real actions. "
    "Include every actionable item. Do not add items that are not in the notes. "
    "No explanation, no markdown fences, only the JSON array.\n\n"
    "Example notes:\n"
    "- anna to send the contract by tuesday\n"
    "call mum about sunday lunch\n"
    "fix bike tyre before saturday — urgent!! race day\n"
    "Example output:\n"
    '[{"task": "Send the contract", "owner": "Anna", "due": "tuesday", "priority": "Medium"}, '
    '{"task": "Call mum about Sunday lunch", "owner": "Me", "due": "sunday", "priority": "Low"}, '
    '{"task": "Fix bike tyre", "owner": "Me", "due": "saturday", "priority": "High"}]'
)


def ensure_model(model_path: Path) -> Path:
    """Download the open-weight GGUF model once (from Hugging Face), then reuse it offline."""
    if model_path.exists():
        return model_path
    print(f"Model not found at {model_path}", file=sys.stderr)
    print(f"Downloading {MODEL_FILE} from {MODEL_REPO} (one-time, ~1.07 GB) ...", file=sys.stderr)
    # Plain HTTP download (the Xet transfer path stalls behind some proxies).
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "huggingface-hub is not installed. Run: pip install -r requirements.txt"
        ) from exc
    model_path.parent.mkdir(parents=True, exist_ok=True)
    downloaded = hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILE, local_dir=str(model_path.parent))
    return Path(downloaded)


def load_llm(model_path: Path, n_ctx: int = 4096):
    from llama_cpp import Llama

    return Llama(
        model_path=str(model_path),
        n_ctx=n_ctx,
        n_threads=os.cpu_count() or 2,
        verbose=False,
    )


def _chunks(notes: str, lines_per_chunk: int = 4) -> list[str]:
    """Split the pile into small chunks.

    Small open-weight models extract far more accurately from a few lines at
    a time than from one long dump — owners and dates stay attached to the
    line they came from. Messy notes are naturally one idea per line, so
    line-chunking loses almost no context.
    """
    lines = [ln.strip() for ln in notes.splitlines() if ln.strip()]
    return ["\n".join(lines[i : i + lines_per_chunk]) for i in range(0, len(lines), lines_per_chunk)]


def extract_tasks(llm, notes: str) -> tuple[list[dict], str]:
    """Ask the local model to turn raw notes into structured tasks (JSON), chunk by chunk."""
    all_tasks: list[dict] = []
    raw_parts: list[str] = []
    for chunk in _chunks(notes):
        result = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Messy notes:\n\n{chunk}\n\nJSON array of tasks:"},
            ],
            temperature=0.1,
            max_tokens=700,
        )
        raw = result["choices"][0]["message"]["content"].strip()
        raw_parts.append(raw)
        all_tasks.extend(parse_tasks(raw))
    if not all_tasks:
        raise ValueError("Model returned no usable tasks for any chunk.")
    return all_tasks, "\n\n".join(raw_parts)


def parse_tasks(raw: str) -> list[dict]:
    """Parse the model's JSON output. Tolerates stray fences / prose around the array."""
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    start, end = cleaned.find("["), cleaned.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"Model did not return a JSON array. Raw output was:\n{raw}")
    data = json.loads(cleaned[start : end + 1])
    tasks: list[dict] = []
    for item in data:
        if not isinstance(item, dict) or not str(item.get("task", "")).strip():
            continue
        priority = str(item.get("priority", "Medium")).title()
        if priority not in {"High", "Medium", "Low"}:
            priority = "Medium"
        tasks.append(
            {
                "task": str(item["task"]).strip(),
                "owner": str(item.get("owner") or "Me").strip() or "Me",
                "due": str(item.get("due") or "No date").strip() or "No date",
                "priority": priority,
            }
        )
    if not tasks:
        raise ValueError(f"Model returned no usable tasks. Raw output was:\n{raw}")
    return tasks
