"""Warmer Agent - Instagram account ko Tier 1 audience ke liye warm up karta hai.

Kaam (sirf Tier 1 - USA/UK/CA/AU):
1. Tier 1 creators ke posts dekhta hai (watch)
2. Unke posts like karta hai
3. Relevant comments karta hai (English only)

Kyon: Naya account agar sirf Tier 1 content se engage karega to Instagram
uska region/audience signal Tier 1 set kar dega. Isse hamari Reels/Shorts
Tier 1 users ko dikhengi.

Free route: Instagram Graph API ya instagrapi (open source).
Credentials env se: IG_USERNAME, IG_PASSWORD (ya session).
"""
import os
import json
import random
import time
from datetime import datetime

DATA_DIR = "/app/data"
WARMER_LOG = os.path.join(DATA_DIR, "warmer_log.json")

# Tier 1 engagement targets - user apne niche ke add karega
# Format: {"platform": "instagram", "handle": "@xyz", "tier": "1", "country": "USA"}
TARGETS_PATH = os.path.join(DATA_DIR, "warmer_targets.json")

# English-only comment templates (natural, spammy nahi)
COMMENT_TEMPLATES = [
    "This is actually really helpful, thanks for sharing!",
    "Great breakdown, just followed for more like this.",
    "This makes so much sense, saving this one.",
    "Solid advice, appreciate the transparency here.",
    "Been looking for something like this, great post!",
]

# Safe limits (Instagram ban se bachne ke liye)
DAILY_LIKE_LIMIT = 50
DAILY_COMMENT_LIMIT = 15
DAILY_WATCH_LIMIT = 80

def load_targets():
    if not os.path.exists(TARGETS_PATH):
        return []
    with open(TARGETS_PATH) as f:
        return json.load(f)

def log_action(action):
    os.makedirs(DATA_DIR, exist_ok=True)
    entry = {"at": datetime.utcnow().isoformat(), **action}
    log = []
    if os.path.exists(WARMER_LOG):
        try:
            with open(WARMER_LOG) as f:
                log = json.load(f)
        except Exception:
            log = []
    log.append(entry)
    # Sirf last 500 entries rakho
    with open(WARMER_LOG, "w") as f:
        json.dump(log[-500:], f, indent=2)

def warm_up(dry_run=True):
    """Tier 1 targets par engage karo. dry_run=True me sirf log, koi real action nahi."""
    targets = [t for t in load_targets() if t.get("tier") == "1"]
    print(f"[warmer] {len(targets)} Tier 1 targets mile")
    if not targets:
        print("[warmer] data/warmer_targets.json me Tier 1 accounts add karo")
        return {"status": "no_targets"}

    actions = []
    # Aaj ke limits
    likes_today = random.randint(20, DAILY_LIKE_LIMIT)
    comments_today = random.randint(5, DAILY_COMMENT_LIMIT)

    for target in targets:
        handle = target.get("handle")
        # Watch (hamesha safe)
        actions.append({"type": "watch", "target": handle, "tier": "1"})
        # Like
        if likes_today > 0:
            actions.append({"type": "like", "target": handle, "tier": "1"})
            likes_today -= 1
        # Comment (kam, natural)
        if comments_today > 0 and random.random() < 0.4:
            comment = random.choice(COMMENT_TEMPLATES)
            actions.append({"type": "comment", "target": handle, "text": comment, "tier": "1"})
            comments_today -= 1
        if likes_today <= 0 and comments_today <= 0:
            break

    if dry_run:
        print(f"[warmer] DRY RUN: {len(actions)} actions plan kiye (koi real action nahi)")
    else:
        # TODO: instagrapi se real actions - IG_USERNAME/IG_PASSWORD env se
        print("[warmer] Real actions ke liye Instagram credentials chahiye")
        for a in actions:
            time.sleep(random.uniform(30, 90))  # human-like delay

    for a in actions:
        log_action({**a, "dry_run": dry_run})
    return {"status": "ok", "actions": len(actions), "dry_run": dry_run}

def run():
    print("[warmer] Tier 1 warmup shuru...")
    # Pehle dry run, jab Instagram milega tab real
    has_creds = bool(os.environ.get("IG_USERNAME"))
    return warm_up(dry_run=not has_creds)
