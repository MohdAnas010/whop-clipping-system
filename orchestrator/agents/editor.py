"""Editor Agent - Remotion se video render karta hai.

Scribe ka JSON input le kar agents/editor/scripts/render.mjs chalata hai.
Output: /app/out/<offer_id>.mp4
"""
import os
import json
import subprocess
import tempfile

EDITOR_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "agents", "editor")
OUT_DIR = os.environ.get("RENDER_OUT", "/app/out")

def render(script_data, offer, filename=None):
    os.makedirs(OUT_DIR, exist_ok=True)
    name = filename or f"{offer.get('product_id', 'clip')}.mp4"
    out_path = os.path.join(OUT_DIR, name)

    # Scribe JSON ko temp file me likho
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(script_data, f, ensure_ascii=False)
        script_path = f.name

    cmd = ["node", "scripts/render.mjs", "--script", script_path, "--out", out_path]
    print(f"[editor] Render kar rahe hain: {out_path}")
    try:
        result = subprocess.run(
            cmd, cwd=EDITOR_DIR, capture_output=True, text=True, timeout=600
        )
        if result.returncode != 0:
            print(f"[editor] Render failed: {result.stderr[:500]}")
            return None
        print(f"[editor] Ho gaya: {out_path}")
        return out_path
    except subprocess.TimeoutExpired:
        print("[editor] Render timeout")
        return None
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass

def run(scripts):
    print(f"[editor] {len(scripts)} clips render kar rahe hain...")
    rendered = []
    for item in scripts:
        path = render(item["script"], item["offer"])
        if path:
            rendered.append({"offer": item["offer"], "script": item["script"], "video": path})
    return rendered
