"""Main Orchestrator - Sab agents ko chalata hai, loop me.

Flow: Scout -> DriveReader -> Scribe -> Stealth -> Editor -> Uploader -> Dispatcher -> Approver -> Meta
Har RUN_EVERY_HOURS me ek cycle. 100% free stack.
"""
import os
import time
import traceback
from datetime import datetime

from agents import scout, scribe, editor, dispatcher, meta, competitor, warmer, stealth, innovator
from agents import drive_reader, uploader, approver

RUN_EVERY_HOURS = int(os.environ.get("RUN_EVERY_HOURS", "6"))

def one_cycle():
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n===== CYCLE START {ts} =====")
    summary = {"started": ts, "offers": 0, "scripts": 0, "rendered": 0, "dispatched": 0, "errors": []}

    try:
        # Warmer pehle - Tier 1 warmup (account ko Tier 1 audience ke liye ready karta hai)
        warmer.run()

        offers = scout.run()
        summary["offers"] = len(offers)
        if not offers:
            summary["errors"].append("koi offer nahi mila")
            return summary

        # Sabse zyada payout wala campaign lo (Scout already sort karke deta hai)
        top_campaign = offers[0]
        print(f"[orchestrator] Top campaign: {top_campaign.get('offer_name')} | {top_campaign.get('commission')}")

        # DriveReader: Campaign ka Google Drive brief padho
        drive_data = drive_reader.run(top_campaign)
        summary["drive_requirements"] = drive_data.get("requirements", {})

        scripts = scribe.run(offers)
        summary["scripts"] = len(scripts)

        # Stealth: AI detection se bachne ke liye human-like banao
        scripts = stealth.run(scripts)

        rendered = editor.run(scripts)
        summary["rendered"] = len(rendered)

        # Uploader: Campaign requirements ke hisab se upload packages banao
        upload_packages = uploader.run(rendered, scripts, drive_data, top_campaign)
        summary["upload_packages"] = len(upload_packages)

        dispatched = dispatcher.run(rendered)
        summary["dispatched"] = len(dispatched)

        # Approver: Whop par approval ke liye submit karo
        submissions = approver.run(upload_packages, top_campaign, dispatched)
        summary["submissions"] = len(submissions)

    except Exception as e:
        summary["errors"].append(str(e))
        traceback.print_exc()

    # Competitor analysis - timing aur trends ke liye (free tools)
    try:
        comp_insights = competitor.run()
        summary["competitor_recommendation"] = comp_insights.get("recommendation", "")
    except Exception as e:
        summary["errors"].append(f"competitor failed: {e}")

    # Innovator: GitHub/HF se naye ideas (din me 1 baar, rate limit se bachne ke liye)
    try:
        import os as _os
        _marker = "/app/data/.innovator_last"
        _run_innovator = True
        if _os.path.exists(_marker):
            import time as _time
            if _time.time() - _os.path.getmtime(_marker) < 86400:
                _run_innovator = False
        if _run_innovator:
            innovator.run()
            open(_marker, "w").write("1")
    except Exception as e:
        summary["errors"].append(f"innovator failed: {e}")

    # Meta agent hamesha chalta hai - system ko behtar banata hai
    try:
        insights = meta.run(summary)
        summary["meta_insights"] = insights
    except Exception as e:
        summary["errors"].append(f"meta failed: {e}")

    print(f"===== CYCLE END: {summary} =====")
    return summary

def main():
    print("Whop Clipping Autonomous System shuru ho raha hai (free stack)")
    print(f"Har {RUN_EVERY_HOURS} ghante me ek cycle")
    while True:
        one_cycle()
        print(f"{RUN_EVERY_HOURS} ghante wait kar rahe hain...")
        time.sleep(RUN_EVERY_HOURS * 3600)

if __name__ == "__main__":
    # Ek baar chalane ke liye: RUN_ONCE=1
    if os.environ.get("RUN_ONCE") == "1":
        one_cycle()
    else:
        main()
