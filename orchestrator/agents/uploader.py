"""Uploader Agent - Video upload ki taiyari campaign requirements ke hisab se.

DriveReader se mili requirements ke hisab se:
- Sahi hashtags lagao
- Campaign ko tag/mention karo
- Platform-specific formatting karo

Ye agent upload package taiyar karta hai jo Dispatcher use karega.
"""
import os
import json
from datetime import datetime

def build_caption(script, requirements):
    """Requirements ke hisab se caption banao."""
    base_caption = script.get("caption", "")
    hashtags = requirements.get("hashtags", [])
    mentions = requirements.get("mentions", [])
    
    # Mentions pehle, phir caption, phir hashtags
    parts = []
    if mentions:
        parts.append(" ".join(mentions))
    if base_caption:
        # Purane hashtags hatao, naye lagayenge
        import re
        clean = re.sub(r"#\w+", "", base_caption).strip()
        parts.append(clean)
    if hashtags:
        parts.append(" ".join(hashtags))
    
    return " ".join(parts).strip()

def build_upload_package(rendered_video, script, requirements, campaign):
    """Upload ke liye poora package banao."""
    package = {
        "video_path": rendered_video.get("path", ""),
        "caption": build_caption(script, requirements),
        "hashtags": requirements.get("hashtags", []),
        "mentions": requirements.get("mentions", []),
        "tags": requirements.get("tags", []),
        "campaign_name": campaign.get("offer_name", ""),
        "campaign_id": campaign.get("product_id", ""),
        "platform": "instagram",  # Default, requirements se override ho sakta hai
        "scheduled_time": datetime.utcnow().isoformat(),
        "requirements_followed": list(requirements.keys()),
    }
    
    # Platform requirements se lo
    platforms = requirements.get("platforms", [])
    if platforms:
        # Instagram preferred hai hamare system me
        if "instagram" in platforms or "reels" in platforms:
            package["platform"] = "instagram"
        elif "tiktok" in platforms:
            package["platform"] = "tiktok"
        elif "youtube" in platforms or "shorts" in platforms:
            package["platform"] = "youtube"
    
    return package

def run(rendered_videos, scripts, drive_data, campaign):
    """Sab videos ke liye upload packages banao."""
    print("[uploader] Upload packages bana rahe hain...")
    
    requirements = drive_data.get("requirements", {}) if drive_data else {}
    packages = []
    
    for i, video in enumerate(rendered_videos):
        script = scripts[i] if i < len(scripts) else {}
        pkg = build_upload_package(video, script, requirements, campaign)
        packages.append(pkg)
        print(f"[uploader] Package {i+1}: {pkg['campaign_name']} | {len(pkg['hashtags'])} hashtags | {pkg['platform']}")
    
    # Packages ko file me save karo taaki Dispatcher use kar sake
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "upload_packages.json")
    with open(out_path, "w") as f:
        json.dump(packages, f, indent=2)
    
    print(f"[uploader] {len(packages)} packages taiyar")
    return packages

if __name__ == "__main__":
    test_video = {"path": "/tmp/test.mp4"}
    test_script = {"caption": "Amazing offer! #oldtag"}
    test_req = {"hashtags": ["#whop", "#money"], "mentions": ["@whop"], "platforms": ["instagram"]}
    test_camp = {"offer_name": "Test", "product_id": "123"}
    print(json.dumps(run([test_video], [test_script], {"requirements": test_req}, test_camp), indent=2))
