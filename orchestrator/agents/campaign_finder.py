"""CampaignFinder Agent - Whop Content Rewards campaigns ke liye research karta hai.

IMPORTANT - Honest limitations:
- Ye agent ke paas hardcoded PLACEHOLDER data hai, verified campaign details NAHI
- Payout rates ($6/1K, $2/1K, etc.) UNVERIFIED hain - inko fact ki tarah mat lo
- Campaign status, budgets, requirements sab UNVERIFIED hain
- Asli campaign details sirf logged-in Whop/Content Rewards dashboard se milenge
- Exact campaign URLs ke liye Whop login zaroori hai

Ye agent:
1. Content Rewards discover page ka link deta hai
2. Join karne ke instructions deta hai
3. Campaign research ke liye ek template banata hai
4. Sab kuch "unverified" label ke saath mark karta hai
"""
import os
import json
from datetime import datetime

# Google Doc ID (AUTO CLIP AGENT - Campaigns)
DOC_ID = "1FSRXhGKNwfgXOvFyolqHH9MB8vbNMJHjL9iXqaozkGI"
FOLDER_ID = "14m6b_L9t_BtAr1NrlcySvzEkuPuw8bVT"

# Content Rewards discover page - yahan se asli campaigns milenge
DISCOVER_URL = "https://contentrewards.com/discover/"

def get_campaign_research_template():
    """Campaign research ke liye template.
    
    NOTE: Neeche diye gaye campaign names sirf research ke liye hain.
    Inke payout, budget, status UNVERIFIED hain.
    """
    return {
        "discover_url": DISCOVER_URL,
        "how_to_find": [
            "1. contentrewards.com/discover/ kholo (Whop login zaroori)",
            "2. Search me campaign ka naam likho",
            "3. Campaign page par payout, budget, requirements check karo",
            "4. Join button dabao",
        ],
        "campaigns_to_research": [
            {"name": "MUTUUM", "niche": "Crypto/DeFi", "status": "UNVERIFIED - dashboard se check karo"},
            {"name": "Roobet", "niche": "Gaming", "status": "UNVERIFIED - dashboard se check karo"},
            {"name": "Cluely", "niche": "AI/Productivity", "status": "UNVERIFIED - dashboard se check karo"},
        ],
        "honest_note": (
            "In campaigns ke payout rates, budgets, aur requirements VERIFY NAHI hue hain. "
            "Koi bhi number fact ki tarah mat lo. "
            "Asli details sirf logged-in Content Rewards dashboard se milengi."
        ),
    }

def format_for_doc(template):
    """Research template ko Google Doc format me banao."""
    lines = []
    lines.append("AUTO CLIP AGENT - Campaign Research")
    lines.append(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("⚠️  IMPORTANT: Neeche di gayi saari campaign details UNVERIFIED hain.")
    lines.append("Asli payout, budget, requirements ke liye Whop dashboard check karo.")
    lines.append("")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"Content Rewards Discover: {template['discover_url']}")
    lines.append("")
    lines.append("Kaise dhoondo:")
    for step in template["how_to_find"]:
        lines.append(f"  {step}")
    lines.append("")
    lines.append("Research karne wali campaigns:")
    for c in template["campaigns_to_research"]:
        lines.append(f"  - {c['name']} ({c['niche']}): {c['status']}")
    lines.append("")
    lines.append(template["honest_note"])
    lines.append("")
    return "\n".join(lines)

def save_local(template, doc_text):
    """Local backup save karo."""
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    
    with open(os.path.join(out_dir, "campaign_research.json"), "w") as f:
        json.dump(template, f, indent=2)
    
    with open(os.path.join(out_dir, "auto_clip_agent_doc.txt"), "w") as f:
        f.write(doc_text)
    
    print(f"[campaign_finder] Local files saved")

def run():
    """Campaign research template banao."""
    print("[campaign_finder] Campaign research template bana rahe hain...")
    print("[campaign_finder] NOTE: Saari campaign details UNVERIFIED hain.")
    
    template = get_campaign_research_template()
    print(f"[campaign_finder] {len(template['campaigns_to_research'])} campaigns research ke liye")
    print(f"[campaign_finder] Discover URL: {template['discover_url']}")
    
    doc_text = format_for_doc(template)
    save_local(template, doc_text)
    
    print(f"[campaign_finder] Google Doc ID: {DOC_ID}")
    print("[campaign_finder] Doc link: https://docs.google.com/document/d/1FSRXhGKNwfgXOvFyolqHH9MB8vbNMJHjL9iXqaozkGI/edit")
    
    return template

if __name__ == "__main__":
    result = run()
    print(f"\nResearch template taiyar hai")
