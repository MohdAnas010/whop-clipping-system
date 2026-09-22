"""DriveReader Agent - Google Drive campaign brief padhta hai.

Whop Content Rewards campaigns me Google Drive link hota hai jisme:
- Campaign requirements (hashtags, tags, mentions)
- Rules (kya allowed hai, kya nahi)
- Source content links
- Payout details

Ye agent Drive se ye sab nikal kar structured format me deta hai,
taaki aage wale agents (Scribe, Editor, Uploader) uske hisab se kaam karein.
"""
import os
import json
import re
import urllib.request
import urllib.parse

def extract_drive_id(drive_url):
    """Google Drive URL se folder/file ID nikalo."""
    # Formats: /drive/folders/ID, /file/d/ID, ?id=ID
    patterns = [
        r"/folders/([a-zA-Z0-9_-]+)",
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"[?&]id=([a-zA-Z0-9_-]+)",
    ]
    for pat in patterns:
        m = re.search(pat, drive_url)
        if m:
            return m.group(1)
    return None

def fetch_drive_folder_public(drive_id):
    """Public Drive folder ki listing (bina auth ke, best effort)."""
    # Google Drive public folders ko direct API bina key ke nahi padh sakte.
    # Hum embedded view se metadata nikalne ki koshish karte hain.
    url = f"https://drive.google.com/embeddedfolderview?id={drive_id}#list"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # File names nikalo
        files = re.findall(r'"name":"([^"]+)"', html)
        return {"files": files[:20], "raw_access": True}
    except Exception as e:
        print(f"[drive_reader] Folder read fail: {e}")
        return {"files": [], "raw_access": False}

def parse_requirements(text):
    """Brief text se requirements nikalo."""
    req = {
        "hashtags": [],
        "mentions": [],
        "tags": [],
        "rules": [],
        "payout": "",
        "platforms": [],
    }
    # Hashtags
    req["hashtags"] = re.findall(r"#\w+", text)
    # Mentions
    req["mentions"] = re.findall(r"@\w+", text)
    # Platforms
    for plat in ["tiktok", "instagram", "youtube", "reels", "shorts", "twitter", "x"]:
        if plat in text.lower():
            req["platforms"].append(plat)
    # Payout
    payout_match = re.search(r"\$[\d.]+\s*(?:per|\/)?\s*1[kK]?", text)
    if payout_match:
        req["payout"] = payout_match.group(0)
    return req

def run(campaign):
    """Campaign ka Drive brief padho aur requirements do."""
    print("[drive_reader] Campaign brief padh rahe hain...")
    
    drive_url = campaign.get("drive_url") or campaign.get("brief_url") or ""
    if not drive_url:
        print("[drive_reader] Koi Drive URL nahi mila, default requirements")
        return {
            "campaign_id": campaign.get("offer_name", "unknown"),
            "requirements": {
                "hashtags": ["#whop", "#clipping"],
                "mentions": [],
                "tags": [],
                "rules": ["original content only"],
                "payout": campaign.get("commission", ""),
                "platforms": ["instagram"],
            },
            "source": "default",
        }
    
    drive_id = extract_drive_id(drive_url)
    result = {
        "campaign_id": campaign.get("offer_name", "unknown"),
        "drive_url": drive_url,
        "drive_id": drive_id,
        "requirements": {},
        "source": "drive",
    }
    
    if drive_id:
        folder_data = fetch_drive_folder_public(drive_id)
        result["folder_files"] = folder_data.get("files", [])
    
    # Campaign ke apne text se bhi requirements nikalo
    brief_text = f"{campaign.get('headline', '')} {campaign.get('offer_name', '')} {drive_url}"
    result["requirements"] = parse_requirements(brief_text)
    
    # Ensure defaults
    if not result["requirements"]["hashtags"]:
        result["requirements"]["hashtags"] = ["#whop", "#clipping"]
    if not result["requirements"]["platforms"]:
        result["requirements"]["platforms"] = ["instagram"]
    
    print(f"[drive_reader] Requirements mile: {result['requirements']}")
    return result

if __name__ == "__main__":
    test = {"offer_name": "Test Campaign", "commission": "$2/1k", "drive_url": "https://drive.google.com/drive/folders/abc123"}
    print(json.dumps(run(test), indent=2))
