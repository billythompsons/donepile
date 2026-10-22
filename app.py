"""DonePile local web UI — zero extra dependencies (Python standard library only).

Run:  python app.py            then open http://127.0.0.1:8765
The model runs on YOUR machine, on CPU. Notes never leave the device.
"""
from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from donepile.engine import DEFAULT_MODEL_PATH, ensure_model, extract_tasks, load_llm
from donepile.render import dedupe_and_sort, estimate_minutes_saved

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>DonePile — Notes to Done List</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:860px;margin:40px auto;padding:0 20px;background:#0f1115;color:#e8e8e8}
 h1{font-size:2rem} textarea{width:100%;height:220px;background:#1a1d24;color:#e8e8e8;border:1px solid #333;border-radius:8px;padding:12px}
 button{background:#ffb020;border:0;padding:12px 22px;border-radius:8px;font-weight:700;cursor:pointer}
 .task{background:#1a1d24;border:1px solid #2c303a;border-radius:8px;padding:10px 14px;margin:8px 0}
 .High{border-left:6px solid #ff5252}.Medium{border-left:6px solid #ffb020}.Low{border-left:6px solid #4caf50}
 small{color:#9aa0aa}
</style></head><body>
<h1>✅ DonePile</h1>
<p>Paste the messy pile. Get a clean, prioritised done-list.<br>
<small>Powered locally by Qwen2.5-1.5B-Instruct (open-weight, Apache-2.0) via llama.cpp — no cloud, no API key, your notes never leave this machine.</small></p>
<form method="POST" action="/">
<textarea name="notes" placeholder="Paste messy meeting notes / brain-dump here...">__NOTES__</textarea>
<p><button type="submit">Do the dreaded task for me →</button></p>
</form>
__RESULT__
</body></html>"""


def render_page(notes: str = "", result: str = "") -> str:
    # Token replacement, not str.format — the CSS in PAGE is full of braces.
    return PAGE.replace("__NOTES__", notes).replace("__RESULT__", result)

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = load_llm(ensure_model(DEFAULT_MODEL_PATH))
    return _llm


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802 (stdlib naming)
        self._send(render_page())

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        notes = (form.get("notes") or [""])[0]
        result = ""
        if notes.strip():
            tasks, _raw = extract_tasks(get_llm(), notes)
            tasks = dedupe_and_sort(tasks)
            cards = "\n".join(
                f'<div class="task {html.escape(t["priority"])}">'
                f'☐ <b>{html.escape(t["task"])}</b><br>'
                f'<small>Owner: {html.escape(t["owner"])} · Due: {html.escape(t["due"])} · '
                f'{html.escape(t["priority"])} priority</small></div>'
                for t in tasks
            )
            result = (
                f"<h2>Your done-list ({len(tasks)} tasks)</h2>{cards}"
                f"<p><small>Estimated manual effort saved: ~{estimate_minutes_saved(len(tasks))} minutes</small></p>"
            )
        self._send(render_page(notes=html.escape(notes), result=result))

    def log_message(self, *args):  # keep the terminal quiet
        pass


if __name__ == "__main__":
    print("DonePile web UI: http://127.0.0.1:8765  (Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
