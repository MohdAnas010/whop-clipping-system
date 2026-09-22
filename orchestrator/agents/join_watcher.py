"""JoinWatcher Agent - Whop par nazar rakhta hai ki tumne campaign join kiya ya nahi.

Ye agent:
1. Har cycle me Whop API check karta hai
2. Dekhta hai ki tumne koi nayi campaign join ki ya nahi
3. Agar join ho gayi, to usko approved campaign bana deta hai
4. Phir workflow automatically us par kaam shuru kar deta hai

Tumhe kuch nahi bolna, bas Join dabana hai. Ye khud detect kar lega.
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

def get_joined_campaigns():
    """Whop se joined campaigns/memberships lao."""
    if not WHOP_API_KEY:
        print("[join_watcher] WHOP_API_KEY nahi hai")
        return []
    
    # Memberships check karo - joined campaigns yahan dikhengi
    url = f"{BASE}/api/v5/memberships?limit=20"
    req = urllib.request.Request(url, headers=_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[join_watcher] API error: {e}")
        return []
    
    items = data.get("data") or []
    campaigns = []
    for m in items:
        # Content Rewards campaigns ko identify karo
        product = m.get("product") or {}
        campaigns.append({
            "offer_name": product.get("title") or m.get("product_id"),
            "product_id": product.get("id") or m.get("product_id"),
            "joined_at": m.get("created_at"),
            "status": m.get("status"),
        })
    return campaigns

def get_approved_campaign():
    """Current approved campaign lao."""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "approved_campaign.json")
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except:
            pass
    return None

def save_approved_campaign(campaign):
    """Nayi joined campaign ko approved banao."""
    path = os.path.join(os.path.dirname(__file__), "..", "data", "approved_campaign.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(campaign, f, indent=2)
    print(f"[join_watcher] Nayi campaign approved: {campaign.get('offer_name')}")

def run():
    """Join status check karo."""
    print("[join_watcher] Whop par check kar rahe hain ki tumne join kiya ya nahi...")
    
    joined = get_joined_campaigns()
    print(f"[join_watcher] {len(joined)} joined campaigns mile")
    
    approved = get_approved_campaign()
    approved_name = approved.get("offer_name") if approved else None
    
    # Nayi join detect karo
    for camp in joined:
        name = camp.get("offer_name")
        if name and name != approved_name:
            # Nayi campaign mili!
            print(f"[join_watcher] NAYI JOIN DETECTED: {name}")
            # Approved banao
            new_approved = {
                "offer_name": name,
                "product_id": camp.get("product_id"),
                "joined_at": camp.get("joined_at"),
                "status": "approved",
                "approved_by": "join_watcher",
                "approved_at": datetime.utcnow().isoformat(),
                # CampaignFinder se details lao agar ho
                "commission": "Check Whop dashboard",
                "source": "whop_join_detected",
            }
            save_approved_campaign(new_approved)
            return {"new_join": True, "campaign": new_approved}
    
    print("[join_watcher] Koi nayi join nahi mili")
    return {"new_join": False, "joined_count": len(joined)}

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
