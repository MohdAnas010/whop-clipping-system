"""JoinWatcher Agent - Whop par nazar rakhta hai ki campaign join hui ya nahi.

IMPORTANT - Honest limitations:
- Ye agent Whop API se memberships check karta hai
- Agar WHOP_API_KEY invalid/expired hai, to ye kuch detect nahi kar sakta
- API se 403/401 aaye to report me saaf likha jayega
- Bina valid API key ke join detection kaam nahi karegi

Ye agent:
1. Har cycle me Whop API check karta hai (agar key valid hai)
2. Dekhta hai ki koi nayi campaign join hui ya nahi
3. Agar join hui, to usko approved campaign bana deta hai
"""
import os
import json
import urllib.request
import urllib.error
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
    """Whop se joined campaigns/memberships lao. Returns (campaigns, status_info)."""
    if not WHOP_API_KEY:
        print("[join_watcher] WHOP_API_KEY nahi hai - detection possible nahi")
        return [], {"api_available": False, "reason": "no_api_key"}
    
    url = f"{BASE}/api/v5/memberships?limit=20"
    req = urllib.request.Request(url, headers=_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Auth fail ho to saaf batao, chhupao mat
        print(f"[join_watcher] API HTTP error {e.code}: key invalid ya expired ho sakti hai")
        return [], {"api_available": False, "reason": f"http_{e.code}", "detail": "API key check karo"}
    except Exception as e:
        print(f"[join_watcher] API error: {e}")
        return [], {"api_available": False, "reason": "network_error", "detail": str(e)}
    
    items = data.get("data") or []
    campaigns = []
    for m in items:
        product = m.get("product") or {}
        campaigns.append({
            "offer_name": product.get("title") or m.get("product_id"),
            "product_id": product.get("id") or m.get("product_id"),
            "joined_at": m.get("created_at"),
            "status": m.get("status"),
        })
    return campaigns, {"api_available": True}

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
    print("[join_watcher] Whop par check kar rahe hain ki campaign join hui ya nahi...")
    
    joined, status_info = get_joined_campaigns()
    
    if not status_info.get("api_available"):
        print(f"[join_watcher] API available nahi: {status_info.get('reason')}")
        print("[join_watcher] Join detection is cycle me possible nahi tha")
        return {
            "new_join": False,
            "joined_count": 0,
            "detection_working": False,
            "reason": status_info.get("reason"),
            "honest_note": "API key invalid hai, isliye join detect nahi ho saki. Key rotate karo.",
        }
    
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
    return {"new_join": False, "joined_count": len(joined), "detection_working": True}

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
