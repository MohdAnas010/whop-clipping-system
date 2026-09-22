"""Father Agent - Sab agents par nazar rakhta hai aur seekhta hai.

IMPORTANT - Honest scope:
- Ye agent har cycle me agents ka performance track karta hai
- Counters aur scores maintain karta hai
- Lekin ye agents ke code ko automatically repair NAHI karta
- "Fixes" ka matlab hai: issues ko identify karke report karna, code ko khud theek karna nahi
- Earning potential hypothetical hai (scripts * payout), actual earnings nahi

Ye agent:
1. Har agent ka success/fail track karta hai
2. Weak agents ko identify karta hai
3. Har cycle me ek report banata hai
4. Earning potential ka estimate deta hai (hypothetical, guarantee nahi)
"""
import os
import json
import time
from datetime import datetime

# Files
LAST_INSTRUCTION_FILE = "/app/data/.last_user_instruction"
KNOWLEDGE_FILE = "/app/data/father_knowledge.json"
AUTO_FIX_TIMEOUT = 1800  # 30 minutes

# Sab agents ki list
ALL_AGENTS = [
    "warmer", "whop_optimizer", "scout", "campaign_finder",
    "drive_reader", "scribe", "stealth", "editor",
    "uploader", "dispatcher", "approver", "competitor",
    "meta", "innovator", "self_healing"
]

def load_knowledge():
    """Pichla gyaan load karo - jitna time hua, utna smart."""
    default = {
        "cycles_completed": 0,
        "total_fixes": 0,
        "agent_scores": {a: {"success": 0, "fail": 0} for a in ALL_AGENTS},
        "lessons": [],
        "smart_level": 1,
    }
    # Local path try karo (GitHub Actions me /app/data, local me orchestrator/data)
    for path in [KNOWLEDGE_FILE, os.path.join(os.path.dirname(__file__), "..", "data", "father_knowledge.json")]:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                    # Merge with default
                    for k, v in default.items():
                        if k not in data:
                            data[k] = v
                    return data
            except:
                pass
    return default

def save_knowledge(knowledge):
    """Gyaan save karo - agli baar aur smart hoga."""
    for path in [KNOWLEDGE_FILE, os.path.join(os.path.dirname(__file__), "..", "data", "father_knowledge.json")]:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                json.dump(knowledge, f, indent=2)
        except:
            pass

def get_last_instruction_time():
    for path in [LAST_INSTRUCTION_FILE, os.path.join(os.path.dirname(__file__), "..", "data", ".last_user_instruction")]:
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return float(f.read().strip())
            except:
                pass
    return 0

def should_auto_fix():
    last = get_last_instruction_time()
    if last == 0:
        return True
    return (time.time() - last) > AUTO_FIX_TIMEOUT

def observe_agents(summary, knowledge):
    """Har agent ko observe karo, seekho."""
    observations = []
    
    # Har agent ka performance track karo
    agent_data = {
        "warmer": summary.get("warmer", True),
        "whop_optimizer": summary.get("whop_optimized", False),
        "scout": summary.get("offers", 0) > 0,
        "drive_reader": bool(summary.get("drive_requirements")),
        "scribe": summary.get("scripts", 0) > 0,
        "editor": summary.get("rendered", 0) > 0,
        "uploader": summary.get("upload_packages", 0) > 0,
        "dispatcher": summary.get("dispatched", 0) > 0,
        "approver": summary.get("submissions", 0) > 0,
    }
    
    for agent, success in agent_data.items():
        if agent in knowledge["agent_scores"]:
            if success:
                knowledge["agent_scores"][agent]["success"] += 1
            else:
                knowledge["agent_scores"][agent]["fail"] += 1
                # Galti se seekho
                lesson = f"{agent} fail hua cycle {knowledge['cycles_completed']+1} me"
                if lesson not in knowledge["lessons"][-20:]:  # Last 20 me nahi hai to add karo
                    knowledge["lessons"].append(lesson)
    
    return observations

def get_wisdom(knowledge):
    """Pita ka gyaan - EARNING par focus."""
    cycles = knowledge["cycles_completed"]
    total_earning_potential = knowledge.get("total_earning_potential", 0)
    if cycles < 5:
        return f"Naya hun. Mission: Sabko earning ki taraf le jana. Potential: ${total_earning_potential:.2f}"
    elif cycles < 20:
        return f"{cycles} cycles ka anubhav. Har decision earning ke liye. Potential: ${total_earning_potential:.2f}"
    elif cycles < 50:
        return f"{cycles} cycles! Earning patterns samajh aa gaye. Potential: ${total_earning_potential:.2f}"
    else:
        return f"{cycles} cycles ka gyaani. Sab agents earning machine hain. Potential: ${total_earning_potential:.2f}"

def calculate_earning_focus(summary, knowledge):
    """Earning par focus karo - sabse important metric."""
    payout = 0
    try:
        _path = os.path.join(os.path.dirname(__file__), "..", "data", "approved_campaign.json")
        if os.path.exists(_path):
            with open(_path) as _f:
                _camp = json.load(_f)
                _payout_str = _camp.get("commission", "") or _camp.get("payout", "")
                import re as _re
                _m = _re.search(r'\$([\d.]+)', str(_payout_str))
                if _m:
                    payout = float(_m.group(1))
    except:
        pass
    
    scripts = summary.get("scripts", 0)
    # Har script se potential earning (conservative: 1000 views avg)
    earning_potential = scripts * payout if payout else 0
    
    knowledge["total_earning_potential"] = knowledge.get("total_earning_potential", 0) + earning_potential
    
    return {
        "campaign_payout_per_1k": payout,
        "scripts_made": scripts,
        "cycle_earning_potential": earning_potential,
        "total_earning_potential": knowledge["total_earning_potential"],
    }

def fix_with_wisdom(summary, knowledge):
    """Issues identify karo aur report karo.
    
    NOTE: Ye function issues ko IDENTIFY karta hai, code ko automatically REPAIR nahi karta.
    "Fix" ka matlab yahan "identified issue + suggested action" hai.
    """
    issues = []
    smart = knowledge["smart_level"]
    
    if "koi offer nahi mila" in str(summary.get("errors", [])):
        issues.append({"issue": "No offers", "suggested_action": "Approved campaign use karo", "auto_repaired": False})
    
    if not summary.get("drive_requirements"):
        issues.append({"issue": "Drive empty", "suggested_action": "Defaults use karo", "auto_repaired": False})
    
    if summary.get("scripts", 0) == 0:
        issues.append({"issue": "No scripts", "suggested_action": "Fallback template", "auto_repaired": False})
    
    if smart >= 3:
        weak = [a for a, s in knowledge["agent_scores"].items() if s["fail"] > s["success"]]
        if weak:
            issues.append({
                "issue": f"Weak agents: {', '.join(weak[:3])}",
                "suggested_action": "In par zyada nazar rakhni hogi",
                "auto_repaired": False,
            })
    
    return issues

def run(summary=None):
    """Pita ka kaam - sabko EARNING ki taraf le jana."""
    print("[father] Mission: Sab agents ko EARNING ki taraf le jana...")
    
    if summary is None:
        summary = {}
    
    # Gyaan load karo
    knowledge = load_knowledge()
    knowledge["cycles_completed"] += 1
    
    # Smart level badhao - jitne cycles, utna earning-smart
    knowledge["smart_level"] = 1 + (knowledge["cycles_completed"] // 10)
    
    # EARNING FOCUS - sabse important
    earning = calculate_earning_focus(summary, knowledge)
    print(f"[father] Cycle #{knowledge['cycles_completed']} | Smart Level: {knowledge['smart_level']}")
    print(f"[father] Earning Potential: ${earning['cycle_earning_potential']:.2f} (Total: ${earning['total_earning_potential']:.2f})")
    print(f"[father] Wisdom: {get_wisdom(knowledge)}")
    
    # Sab agents ko observe karo - earning ke lens se
    observe_agents(summary, knowledge)
    
    # 30 min check
    auto = should_auto_fix()
    print(f"[father] Auto-fix: {'ON' if auto else 'OFF'}")
    
    issues = []
    if auto:
        issues = fix_with_wisdom(summary, knowledge)
        knowledge["total_fixes"] += len(issues)
        for i in issues:
            print(f"[father] Issue identified: {i['issue']} -> suggested: {i['suggested_action']}")
    
    # Gyaan save karo - agli baar aur smart
    save_knowledge(knowledge)
    
    # Report
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    
    report = {
        "checked_at": datetime.utcnow().isoformat(),
        "cycle": knowledge["cycles_completed"],
        "smart_level": knowledge["smart_level"],
        "wisdom": get_wisdom(knowledge),
        "auto_fix_enabled": auto,
        "issues_identified": issues,
        "total_issues_ever": knowledge["total_fixes"],
        "lessons_learned": len(knowledge["lessons"]),
        "honest_note": "Issues identify kiye gaye, code auto-repair nahi hua. Earning potential hypothetical hai.",
    }
    
    with open(os.path.join(out_dir, "father_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"[father] {len(issues)} issues identified | Total lessons: {len(knowledge['lessons'])}")
    return report

def record_user_instruction():
    for path in [LAST_INSTRUCTION_FILE, os.path.join(os.path.dirname(__file__), "..", "data", ".last_user_instruction")]:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(str(time.time()))
        except:
            pass

if __name__ == "__main__":
    print(json.dumps(run({"errors": [], "scripts": 2}), indent=2, ensure_ascii=False))
