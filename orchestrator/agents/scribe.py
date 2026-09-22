"""Scribe Agent - Viral script writer using Ollama (free, open source).

Model: qwen2.5:7b (default) ya llama3.1:8b - Hugging Face via Ollama.
Prompts: agents/scribe/prompts.md se load hote hain.
"""
import os
import json
import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

SYSTEM_PROMPT = """You are a viral short-form video script writer. You write 30-45 second Reels/Shorts scripts for Whop affiliate offers targeting Tier 1 audiences (USA, UK, Canada, Australia). Tone: direct, energetic, ENGLISH ONLY. Output ONLY valid JSON, no extra text.

Output format:
{"hook": "...", "scriptLines": ["...", "...", "..."], "caption": "...", "accentColor": "#00ff88"}

Rules:
- hook max 10 words, English only
- each scriptLine max 12 words
- caption with 3-5 hashtags, English only
- CTA: "Link in bio/description"
"""

def generate_script(offer):
    prompt = f"""Offer: {offer.get('offer_name')}
Commission: {offer.get('commission')}
Niche: {offer.get('niche')}
Headline: {offer.get('headline')}

Pick the best viral angle for a Tier 1 (USA) audience and create the JSON script (case-study, mistake-fix, or blueprint angle). ENGLISH ONLY."""
    try:
        r = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "system": SYSTEM_PROMPT,
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.8},
            },
            timeout=120,
        )
        r.raise_for_status()
        raw = r.json().get("response", "{}")
        # Ollama kabhi-kabhi markdown fences deta hai, saaf karo
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw
            raw = raw.rsplit("```", 1)[0]
        data = json.loads(raw)
        # Validate
        assert "hook" in data and "scriptLines" in data, "incomplete script"
        data.setdefault("caption", f"{offer.get('offer_name')} #whop #affiliate #makemoneyonline")
        data.setdefault("accentColor", "#00ff88")
        return data
    except Exception as e:
        print(f"[scribe] LLM error: {e}, fallback template use kar rahe hain")
        return {
            "hook": f"Make money with {offer.get('offer_name')}",
            "scriptLines": [
                f"This is {offer.get('offer_name')}",
                f"Earn up to {offer.get('commission')} commission",
                "Link in bio, check it out now",
            ],
            "caption": f"{offer.get('offer_name')} #whop #affiliate #makemoneyonline #sidehustle",
            "accentColor": "#00ff88",
        }

def run(offers):
    print(f"[scribe] {len(offers)} offers ke liye scripts bana rahe hain...")
    scripts = []
    for offer in offers:
        script = generate_script(offer)
        scripts.append({"offer": offer, "script": script})
    return scripts
