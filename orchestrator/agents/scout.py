"""Scout Agent - Whop affiliate campaign discovery (free, open source).

Uses Whop API via WHOP_API_KEY env. Falls back to Discover marketplace
scrape notes when API has no affiliate endpoint.
"""
import os
import json
import urllib.request

WHOP_API_KEY = os.environ.get("WHOP_API_KEY", "")
BASE = "https://api.whop.com"

def _headers():
    return {
        "Authorization": f"Bearer {WHOP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

def fetch_products(limit=10):
    """Fetch products; filter those with affiliate enabled."""
    if not WHOP_API_KEY:
        print("[scout] WHOP_API_KEY nahi hai, skip kar rahe hain")
        return []
    # NOTE: Whop ka public affiliate-discover endpoint documented nahi hai.
    # Ye company ke apne products + affiliate settings check karta hai.
    # Discover marketplace ke liye browser-based scout alag se chalega.
    url = f"{BASE}/api/v5/products?limit={limit}"
    req = urllib.request.Request(url, headers=_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[scout] API error: {e}")
        return []
    items = data.get("data") or data.get("products") or []
    offers = []
    for p in items:
        aff_pct = p.get("global_affiliate_percentage") or p.get("member_affiliate_percentage") or 0
        aff_status = p.get("global_affiliate_status") or p.get("member_affiliate_status")
        if aff_status == "enabled" and aff_pct:
            offers.append({
                "offer_name": p.get("title"),
                "product_id": p.get("id"),
                "commission": f"{aff_pct}%",
                "commission_value": float(aff_pct),
                "niche": (p.get("product_tax_code") or {}).get("name", "general"),
                "price": str(p.get("price") or ""),
                "route": p.get("route"),
                "headline": p.get("headline") or p.get("description") or "",
            })
    offers.sort(key=lambda o: o["commission_value"], reverse=True)
    return offers[:5]

def run():
    print("[scout] Top offers dhoondh rahe hain...")
    offers = fetch_products()
    print(f"[scout] {len(offers)} offers mile")
    return offers

if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
