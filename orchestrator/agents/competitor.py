"""Competitor Analysis Agent - Free/Open Source.

Kaam:
1. Competitor accounts track karta hai (user data/competitors.json me list deta hai)
2. YouTube Data API (free quota) se unke recent videos, views, posting time nikaalta hai
3. Best posting timing analyze karta hai (USA audience ke liye)
4. Meta agent ko insights deta hai taaki timing aur content improve ho

Koi paid tool nahi. Instagram ke liye public data + manual notes.
"""
import os
import json
from datetime import datetime
from collections import Counter

DATA_DIR = "/app/data"
COMPETITORS_PATH = os.path.join(DATA_DIR, "competitors.json")
ANALYSIS_PATH = os.path.join(DATA_DIR, "competitor_analysis.json")
SCHEDULE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "posting_schedule.json")
SCHEDULE_PATH = os.path.normpath(SCHEDULE_PATH)

def load_schedule():
    try:
        with open(SCHEDULE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}

def today_recommendation(schedule):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = days[datetime.utcnow().weekday()]
    for entry in schedule.get("weekly_schedule", []):
        if entry.get("day") == today:
            return entry
    return {}

# USA audience ke liye best posting times (industry data, IST me convert karke rakho)
# Source: multiple 2024-2026 social media studies ka aggregate
BEST_TIMES_USA = {
    "instagram_reels": {
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
        "best_hours_et": [11, 12, 19, 20, 21],
        "note": "Lunch (11-12 ET) aur evening (7-9 ET) sabse acha. ET se IST = +9:30",
        "best_hours_ist": ["20:30", "21:30", "04:30", "05:30", "06:30"],
    },
    "youtube_shorts": {
        "best_days": ["Friday", "Saturday", "Sunday"],
        "best_hours_et": [12, 13, 14, 15, 18],
        "note": "Weekend afternoon ET best hai. ET se IST = +9:30",
        "best_hours_ist": ["21:30", "22:30", "23:30", "00:30", "03:30"],
    },
}

def load_competitors():
    if not os.path.exists(COMPETITORS_PATH):
        return []
    with open(COMPETITORS_PATH) as f:
        return json.load(f)

def analyze_youtube_channel(api_key, channel_id, max_results=20):
    """YouTube Data API (free, 10k units/day) se recent videos analyze karo."""
    import urllib.request
    import urllib.parse
    if not api_key:
        return {"error": "YOUTUBE_API_KEY nahi hai"}
    try:
        # Channel ke recent videos
        params = urllib.parse.urlencode({
            "key": api_key, "channelId": channel_id,
            "part": "snippet", "order": "date", "maxResults": max_results,
            "type": "video",
        })
        url = f"https://www.googleapis.com/youtube/v3/search?{params}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        videos = []
        hours = []
        for item in data.get("items", []):
            snip = item.get("snippet", {})
            published = snip.get("publishedAt", "")
            try:
                dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                hours.append(dt.hour)  # UTC hour
            except Exception:
                pass
            videos.append({
                "title": snip.get("title"),
                "publishedAt": published,
            })
        # Sabse common posting hours
        common_hours = Counter(hours).most_common(3)
        return {
            "channel_id": channel_id,
            "videos_analyzed": len(videos),
            "common_posting_hours_utc": [h for h, _ in common_hours],
            "recent_titles": [v["title"] for v in videos[:5]],
        }
    except Exception as e:
        return {"error": str(e)}

def run():
    print("[competitor] Competitors analyze kar rahe hain...")
    competitors = load_competitors()
    yt_key = os.environ.get("YOUTUBE_API_KEY", "")

    results = {"analyzed_at": datetime.utcnow().isoformat(), "channels": []}
    for comp in competitors:
        if comp.get("platform") == "youtube" and comp.get("channel_id"):
            info = analyze_youtube_channel(yt_key, comp["channel_id"])
            info["name"] = comp.get("name")
            results["channels"].append(info)
        else:
            # Instagram/TikTok: manual notes (public profile dekh kar user bharega)
            results["channels"].append({
                "name": comp.get("name"),
                "platform": comp.get("platform"),
                "notes": comp.get("notes", ""),
                "status": "manual - profile khud check karo",
            })

    results["best_times_usa"] = BEST_TIMES_USA

    # Full week schedule (Tier 1 views ke liye)
    schedule = load_schedule()
    results["weekly_schedule"] = schedule.get("weekly_schedule", [])
    results["tier1_targeting_tips"] = schedule.get("tier1_targeting_tips", [])
    today = today_recommendation(schedule)
    results["today"] = today
    if today:
        times = ", ".join(today.get("times_et", []))
        results["recommendation"] = (
            f"Aaj {today.get('day')} hai: {today.get('platform')} par "
            f"{times} ET par post karo. Angle: {today.get('content_angle')}. "
            f"Tags: {today.get('caption_tags')}"
        )
    else:
        results["recommendation"] = (
            "USA audience ke liye: Reels Tue-Thu shaam 7-9 ET (IST me subah 4:30-6:30) "
            "ya dopahar 11-12 ET (IST raat 8:30-9:30). "
            "Shorts weekend dopahar ET me post karo."
        )

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ANALYSIS_PATH, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[competitor] Analysis saved: {ANALYSIS_PATH}")
    return results
