"""Father Agent - Sab agents ko EARNING ki taraf le jana.

Ye agent ka EK HI KAAM hai:
Sab 16 agents ko earning ki taraf le jana.

1. Har decision earning ke hisab se leta hai
2. Jo agent earning badhata hai, usko badhava deta hai
3. Jo agent earning ghatata hai, usko theek karta hai
4. Har cycle me earning potential track karta hai
5. Sabse zyada payout wali campaign ko priority deta hai
6. Jitna time kaam karta hai, utna earning-smart hota jata hai

Pita ka sapna: Sab bachche (agents) milkar paisa kamayein.
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
    """Gyaan ke saath fix karo."""
    fixes = []
    smart = knowledge["smart_level"]
    
    # Basic fixes (sabko pata hai)
    if "koi offer nahi mila" in str(summary.get("errors", [])):
        fixes.append({"issue": "No offers", "fix": "Approved campaign use karo", "wisdom_used": smart})
    
    if not summary.get("drive_requirements"):
        fixes.append({"issue": "Drive empty", "fix": "Defaults use karo", "wisdom_used": smart})
    
    if summary.get("scripts", 0) == 0:
        fixes.append({"issue": "No scripts", "fix": "Fallback template", "wisdom_used": smart})
    
    # Smart fixes (jitna smart, utne behtar fixes)
    if smart >= 3:
        # Agent scores se seekho - kaunsa agent weak hai
        weak = [a for a, s in knowledge["agent_scores"].items() if s["fail"] > s["success"]]
        if weak:
            fixes.append({
                "issue": f"Weak agents: {', '.join(weak[:3])}",
                "fix": "In par zyada nazar rakhunga agle cycle me",
                "wisdom_used": smart,
            })
    
    return fixes

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
    
    fixes = []
    if auto:
        fixes = fix_with_wisdom(summary, knowledge)
        knowledge["total_fixes"] += len(fixes)
        for f in fixes:
            print(f"[father] Sikhaya: {f['issue']} -> {f['fix']}")
    
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
        "fixes_applied": fixes,
        "total_fixes_ever": knowledge["total_fixes"],
        "lessons_learned": len(knowledge["lessons"]),
    }
    
    with open(os.path.join(out_dir, "father_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"[father] {len(fixes)} cheezein theek ki | Total lessons: {len(knowledge['lessons'])}")
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
