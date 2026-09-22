"""Main Orchestrator - Sab agents ko chalata hai, loop me.

Flow: Scout -> DriveReader -> Scribe -> Stealth -> Editor -> Uploader -> Dispatcher -> Approver -> Meta
Har RUN_EVERY_HOURS me ek cycle. 100% free stack.
"""
import os
import time
import json
import traceback
from datetime import datetime

from agents import scout, scribe, editor, dispatcher, meta, competitor, warmer, stealth, innovator
from agents import drive_reader, uploader, approver, campaign_finder, whop_optimizer, self_healing, join_watcher, profile_builder

RUN_EVERY_HOURS = int(os.environ.get("RUN_EVERY_HOURS", "6"))

def one_cycle():
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n===== CYCLE START {ts} =====")
    summary = {"started": ts, "offers": 0, "scripts": 0, "rendered": 0, "dispatched": 0, "errors": []}

    try:
        # Warmer pehle - Tier 1 warmup (account ko Tier 1 audience ke liye ready karta hai)
        warmer.run()

        # WhopOptimizer: Profile ko professional banaye rakho, Instagram-Whop connection check karo
        try:
            opt_report = whop_optimizer.run()
            summary["whop_optimized"] = True
        except Exception as e:
            summary["errors"].append(f"whop_optimizer failed: {e}")

        # ProfileBuilder: Whop profile banao (user ko kuch nahi karna)
        try:
            profile_result = profile_builder.run()
            summary["profile_built"] = True
            summary["profile_name"] = profile_result["profile"]["display_name"]
        except Exception as e:
            summary["errors"].append(f"profile_builder failed: {e}")

        # JoinWatcher: Dekho tumne Whop par koi nayi campaign join ki ya nahi
        # Tumhe kuch nahi bolna, bas Join dabana hai - ye khud detect kar lega
        try:
            join_result = join_watcher.run()
            summary["join_watcher"] = join_result
            if join_result.get("new_join"):
                print(f"[orchestrator] Nayi join mili: {join_result['campaign'].get('offer_name')}")
        except Exception as e:
            summary["errors"].append(f"join_watcher failed: {e}")

        # Pehle approved campaign check karo (Google Doc se user ne approve kiya ho)
        top_campaign = None
        approved_path = os.path.join(os.path.dirname(__file__), "data", "approved_campaign.json")
        if os.path.exists(approved_path):
            try:
                with open(approved_path) as f:
                    top_campaign = json.load(f)
                print(f"[orchestrator] Approved campaign mila: {top_campaign.get('offer_name')} | {top_campaign.get('commission')}")
            except Exception as e:
                print(f"[orchestrator] Approved campaign read fail: {e}")
        
        # Agar approved nahi hai to Scout se dhoondho
        if not top_campaign:
            offers = scout.run()
            summary["offers"] = len(offers)
            if not offers:
                summary["errors"].append("koi offer nahi mila")
                return summary
            # Sabse zyada payout wala campaign lo (Scout already sort karke deta hai)
            top_campaign = offers[0]
            print(f"[orchestrator] Top campaign: {top_campaign.get('offer_name')} | {top_campaign.get('commission')}")
        else:
            offers = [top_campaign]
            summary["offers"] = 1

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

    # CampaignFinder: Best Whop campaigns dhoondho (din me 1 baar)
    # Google Doc "AUTO CLIP AGENT" me likhta hai, user approve karta hai
    try:
        import os as _os2
        _cf_marker = "/app/data/.campaign_finder_last"
        _run_cf = True
        if _os2.path.exists(_cf_marker):
            import time as _time2
            if _time2.time() - _os2.path.getmtime(_cf_marker) < 86400:
                _run_cf = False
        if _run_cf:
            best_campaigns = campaign_finder.run()
            summary["best_campaigns"] = len(best_campaigns)
            open(_cf_marker, "w").write("1")
    except Exception as e:
        summary["errors"].append(f"campaign_finder failed: {e}")

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

    # SelfHealing: Mistakes ko automatically theek karo
    # Agar 30 min tak user se instruction nahi aayi to khud action lo
    try:
        healing_report = self_healing.run(summary)
        summary["self_healing"] = healing_report
    except Exception as e:
        summary["errors"].append(f"self_healing failed: {e}")

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
