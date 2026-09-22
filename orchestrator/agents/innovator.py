"""Innovator Agent - GitHub aur Hugging Face par naye ideas dhoondhta hai.

Kaam:
1. GitHub/Hugging Face par search karta hai: naye open-source tools, models,
   workflows jo is clipping system ko aur behtar bana sakte hain
2. Agar kuch acha mile to ek short explanation VIDEO banata hai (Remotion se)
3. Video Google Drive par upload karta hai (approval ke liye)
4. User approve kare to hi aage implement hota hai

24/7 chalta hai, lekin Drive upload ke baad ruk kar approval ka wait karta hai.
"""
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

DATA_DIR = "/app/data"
INNOVATOR_LOG = os.path.join(DATA_DIR, "innovator_log.json")
APPROVAL_DIR = os.path.join(DATA_DIR, "innovator_pending")

# Kya search karna hai
SEARCH_TOPICS = [
    "ai video generation open source",
    "instagram automation open source",
    "viral hook generator llm",
    "short form video ai editor",
    "whop api affiliate tool",
]

def search_github(topic, limit=5):
    """GitHub API (free, no auth for basic search) se repos dhoondo."""
    try:
        q = urllib.parse.quote(f"{topic} stars:>100")
        url = f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page={limit}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json",
                                                   "User-Agent": "whop-clipping-agent"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return [{"name": r["full_name"], "stars": r["stargazers_count"],
                 "desc": r.get("description", "")[:200], "url": r["html_url"]}
                for r in data.get("items", [])]
    except Exception as e:
        print(f"[innovator] GitHub search failed: {e}")
        return []

def search_huggingface(topic, limit=5):
    """Hugging Face API (free) se models dhoondo."""
    try:
        q = urllib.parse.quote(topic)
        url = f"https://huggingface.co/api/models?search={q}&sort=likes&direction=-1&limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "whop-clipping-agent"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return [{"name": m.get("id"), "likes": m.get("likes", 0),
                 "desc": (m.get("cardData", {}) or {}).get("description", "")[:200] if isinstance(m.get("cardData"), dict) else ""}
                for m in data if isinstance(m, dict)]
    except Exception as e:
        print(f"[innovator] HF search failed: {e}")
        return []

def make_explainer_video(idea):
    """Idea ke baare me short explainer video banao (Remotion se)."""
    # Scribe jaisa JSON banao
    script = {
        "hook": f"New upgrade found: {idea.get('name', 'tool')}",
        "scriptLines": [
            f"Found {idea.get('name')} - {idea.get('stars', idea.get('likes', ''))} stars",
            (idea.get("desc") or "This could improve our workflow")[:80],
            "Check Google Drive, approve if you like it",
        ],
        "caption": f"System upgrade idea: {idea.get('name')} #automation #ai",
        "accentColor": "#4ecdc4",
    }
    # Editor agent se render karo
    try:
        from agents import editor
        path = editor.render(script, {"product_id": f"innovator_{datetime.utcnow().strftime('%Y%m%d_%H%M')}"})
        return path, script
    except Exception as e:
        print(f"[innovator] Video render failed: {e}")
        return None, script

def upload_to_drive(video_path):
    """Google Drive par upload karo (approval ke liye).

    Free route: rclone ya Google Drive API.
    GDRIVE_FOLDER_ID env me rakho. Agar configured nahi hai to
    local approval folder me rakho.
    """
    os.makedirs(APPROVAL_DIR, exist_ok=True)
    folder_id = os.environ.get("GDRIVE_FOLDER_ID", "")
    if not folder_id:
        # Local approval folder
        import shutil
        dest = os.path.join(APPROVAL_DIR, os.path.basename(video_path))
        shutil.copy2(video_path, dest)
        print(f"[innovator] Drive not configured, approval ke liye rakha: {dest}")
        return {"status": "pending_local", "path": dest}
    # TODO: Google Drive API upload (service account ya OAuth)
    print("[innovator] Drive upload ke liye GDRIVE credentials chahiye")
    return {"status": "pending_creds", "video": video_path}

def log_idea(idea, video_result):
    os.makedirs(DATA_DIR, exist_ok=True)
    entry = {"at": datetime.utcnow().isoformat(), "idea": idea, "video": video_result}
    log = []
    if os.path.exists(INNOVATOR_LOG):
        try:
            with open(INNOVATOR_LOG) as f:
                log = json.load(f)
        except Exception:
            log = []
    log.append(entry)
    with open(INNOVATOR_LOG, "w") as f:
        json.dump(log[-100:], f, indent=2)

def run():
    print("[innovator] GitHub/Hugging Face par naye ideas dhoondh rahe hain...")
    findings = []
    for topic in SEARCH_TOPICS[:2]:  # Har cycle me 2 topics (rate limit se bachne ke liye)
        for repo in search_github(topic, limit=3):
            findings.append({"source": "github", "topic": topic, **repo})
        for model in search_huggingface(topic, limit=2):
            findings.append({"source": "huggingface", "topic": topic, **model})

    if not findings:
        print("[innovator] Koi naya idea nahi mila")
        return {"status": "no_findings"}

    # Sabse promising idea chuno (sabse zyada stars/likes)
    best = max(findings, key=lambda x: x.get("stars", 0) + x.get("likes", 0))
    print(f"[innovator] Best idea: {best.get('name')}")

    video_path, script = make_explainer_video(best)
    if video_path:
        result = upload_to_drive(video_path)
    else:
        result = {"status": "video_failed"}
    log_idea(best, result)
    print(f"[innovator] Approval ke liye bheja: {result.get('status')}")
    return {"status": "pending_approval", "idea": best.get("name"), "result": result}
