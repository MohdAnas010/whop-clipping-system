"""Meta Agent - Pure system ko aur extraordinary banata hai.

Kaam:
1. Har run ke results analyze karta hai (kya bana, kya fail hua)
2. Scribe ke prompts ko improve karta hai (hook quality, naye angles)
3. Scout ke filters ko tune karta hai (behtar offers)
4. Weekly self-review report banata hai: data/improvements.md

Ye agent Ollama (free) use karta hai, koi paid API nahi.
"""
import os
import json
import requests
from datetime import datetime

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
DATA_DIR = "/app/data"
REPORT_PATH = os.path.join(DATA_DIR, "improvements.md")

META_PROMPT = """Tum Meta agent ho - ek autonomous clipping system ke self-improvement coach.

Tumhe har run ka summary milega. Tumhara kaam:
1. Kya acha hua, kya fail hua - 3 bullet me analyze karo
2. Scribe ke liye 1 naya viral hook angle suggest karo (Hindi/Hinglish)
3. Scout ke liye 1 behtar offer filter rule suggest karo
4. Agle run ke liye 1 concrete improvement action batao

Output sirf JSON: {"analysis": [...], "new_hook_angle": "...", "scout_rule": "...", "next_action": "..."}
"""

def analyze_run(summary):
    prompt = f"Run summary:\n{json.dumps(summary, ensure_ascii=False, indent=2)}"
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "system": META_PROMPT,
                  "format": "json", "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        raw = r.json().get("response", "{}").strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw
            raw = raw.rsplit("```", 1)[0]
        return json.loads(raw)
    except Exception as e:
        print(f"[meta] Analysis failed: {e}")
        return {"analysis": ["run complete"], "new_hook_angle": "",
                "scout_rule": "", "next_action": "prompts review karo"}

def append_report(summary, insights):
    os.makedirs(DATA_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    with open(REPORT_PATH, "a") as f:
        f.write(f"\n## Run {ts}\n")
        f.write(f"Summary: {json.dumps(summary, ensure_ascii=False)}\n")
        f.write(f"Insights: {json.dumps(insights, ensure_ascii=False, indent=2)}\n")
    print(f"[meta] Report updated: {REPORT_PATH}")

def improve_scribe_prompt(new_angle):
    """Naya hook angle Scribe ke prompts me add karta hai."""
    if not new_angle:
        return
    path = os.path.join(os.path.dirname(__file__), "..", "..",
                        "agents", "scribe", "prompts.md")
    path = os.path.normpath(path)
    try:
        with open(path, "a") as f:
            f.write(f"\n### Auto-added angle ({datetime.utcnow().date()})\n{new_angle}\n")
        print(f"[meta] Scribe prompt me naya angle add hua")
    except Exception as e:
        print(f"[meta] Prompt update failed: {e}")

def run(summary):
    print("[meta] System ko analyze kar rahe hain...")
    insights = analyze_run(summary)
    append_report(summary, insights)
    improve_scribe_prompt(insights.get("new_hook_angle", ""))
    return insights
