"""Approver Agent - Video upload ke baad Whop par approval ke liye submit karo.

Whop Content Rewards me:
1. Video ko allowed platform par post karo (Instagram/TikTok/YouTube)
2. Post ka link copy karo
3. Whop campaign page par jao
4. Submission me link submit karo
5. Brand approve karega, phir payout milega

Ye agent submission ko track karta hai aur Whop API se entry submit karta hai.
"""
import os
import json
import urllib.request
from datetime import datetime

WHOP_API_KEY = os.environ.get("WHOP_API_KEY", "")
BASE = "https://api.whop.com"

def _headers():
    return {
        "Authorization": f"Bearer {WHOP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def submit_to_whop(campaign, video_url, platform):
    """Whop campaign me video submission karo."""
    if not WHOP_API_KEY:
        print("[approver] WHOP_API_KEY nahi hai, manual submission needed")
        return {"status": "manual_required", "video_url": video_url}
    
    # Whop Content Rewards me entries API se submit hota hai
    # NOTE: Exact endpoint campaign type par depend karta hai
    campaign_id = campaign.get("product_id") or campaign.get("offer_name")
    
    submission = {
        "campaign_id": campaign_id,
        "campaign_name": campaign.get("offer_name"),
        "video_url": video_url,
        "platform": platform,
        "submitted_at": datetime.utcnow().isoformat(),
        "status": "pending_approval",
    }
    
    # TODO: Jab Whop ka exact Content Rewards submission API milega,
    # tab yahan POST request jayega. Abhi ke liye tracking ke liye save karo.
    print(f"[approver] Submission taiyar: {campaign.get('offer_name')} | {platform} | {video_url}")
    return submission

def run(upload_packages, campaign, dispatched_results=None):
    """Upload ke baad Whop par approval ke liye submit karo."""
    print("[approver] Whop par approval ke liye submit kar rahe hain...")
    
    submissions = []
    for i, pkg in enumerate(upload_packages):
        # Dispatched result se actual posted URL lo (agar hai)
        video_url = pkg.get("video_path", "")
        if dispatched_results and i < len(dispatched_results):
            video_url = dispatched_results[i].get("url", video_url)
        
        platform = pkg.get("platform", "instagram")
        sub = submit_to_whop(campaign, video_url, platform)
        submissions.append(sub)
    
    # Submissions ko track karo
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "whop_submissions.json")
    
    # Purani submissions ke saath merge karo
    existing = []
    if os.path.exists(out_path):
        try:
            with open(out_path) as f:
                existing = json.load(f)
        except:
            pass
    
    existing.extend(submissions)
    with open(out_path, "w") as f:
        json.dump(existing, f, indent=2)
    
    print(f"[approver] {len(submissions)} submissions track ki gayi")
    print("[approver] NOTE: Whop dashboard par jakar manually approve karwana hoga")
    print("[approver] Ya jab Content Rewards API milega tab auto-submit hoga")
    
    return submissions

if __name__ == "__main__":
    test_pkg = [{"video_path": "/tmp/test.mp4", "platform": "instagram", "campaign_name": "Test"}]
    test_camp = {"offer_name": "Test Campaign", "product_id": "123"}
    print(json.dumps(run(test_pkg, test_camp), indent=2))
