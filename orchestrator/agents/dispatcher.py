"""Dispatcher Agent - Instagram Reels + YouTube Shorts par publish karta hai.

HUMAN_APPROVAL=true ho to sirf /app/out me file rakh kar approval ka wait karta hai.
Auto mode me platform APIs use karta hai (credentials env se).
"""
import os
import json
import shutil

OUT_DIR = os.environ.get("RENDER_OUT", "/app/out")
APPROVED_DIR = "/app/data/approved"
HUMAN_APPROVAL = os.environ.get("HUMAN_APPROVAL", "false").lower() == "true"
# Pehle sirf Instagram. YouTube baad me enable hoga.
ENABLE_YOUTUBE = os.environ.get("ENABLE_YOUTUBE", "false").lower() == "true"

def publish_instagram(video_path, caption):
    # TODO: Instagram Graph API ya instagrapi se connect karo
    # Free route: Meta app banao, IG Business account link karo
    print(f"[dispatcher] Instagram publish (stub): {video_path}")
    return {"platform": "instagram", "status": "pending_creds", "video": video_path}

def publish_youtube(video_path, title, description):
    # TODO: YouTube Data API v3 se upload karo
    # Free route: Google Cloud console me API enable karo, OAuth token env me rakho
    print(f"[dispatcher] YouTube publish (stub): {video_path}")
    return {"platform": "youtube", "status": "pending_creds", "video": video_path}

def run(rendered):
    print(f"[dispatcher] {len(rendered)} videos dispatch kar rahe hain...")
    results = []
    for item in rendered:
        video = item["video"]
        script = item["script"]
        caption = script.get("caption", "")
        if HUMAN_APPROVAL:
            os.makedirs(APPROVED_DIR, exist_ok=True)
            dest = os.path.join(APPROVED_DIR, os.path.basename(video))
            shutil.copy2(video, dest)
            print(f"[dispatcher] Approval ke liye rakha: {dest}")
            results.append({"video": video, "status": "awaiting_approval", "path": dest})
            continue
        ig = publish_instagram(video, caption)
        result = {"offer": item["offer"], "video": video, "instagram": ig}
        if ENABLE_YOUTUBE:
            yt = publish_youtube(video, script.get("hook", ""), caption)
            result["youtube"] = yt
        else:
            result["youtube"] = {"platform": "youtube", "status": "disabled_instagram_first"}
        results.append(result)
    return results
