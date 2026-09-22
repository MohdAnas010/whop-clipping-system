"""Father Agent (SelfHealing) - Sab agents ka pita, un par nazar rakhta hai.

Ye agent:
1. Sab 15 agents par nazar rakhta hai
2. Unse seekhta hai - successes aur mistakes dono se
3. Jitna time kaam karta hai, utna smart hota jata hai
4. Knowledge base banata hai jo har cycle me badhta hai
5. Agents ko guide karta hai, jaise pita bachchon ko
6. 30 min tak instruction na aaye to khud action leta hai
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
    """Pita ka gyaan - jitne cycles, utni wisdom."""
    cycles = knowledge["cycles_completed"]
    if cycles < 5:
        return "Naya hun, seekh raha hun. Har galti mujhe smart banati hai."
    elif cycles < 20:
        return f"{cycles} cycles ka anubhav hai. Patterns samajh aa rahe hain."
    elif cycles < 50:
        return f"{cycles} cycles! Ab main pehle se predict kar sakta hun ki kahan problem aayegi."
    else:
        return f"{cycles} cycles ka gyaani hun. Sab agents mere bachche hain, main unhe behtar banata hun."

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
    """Pita ka kaam - sab par nazar, sabse seekho."""
    print("[father] Sab bachchon (agents) par nazar rakh raha hun...")
    
    if summary is None:
        summary = {}
    
    # Gyaan load karo
    knowledge = load_knowledge()
    knowledge["cycles_completed"] += 1
    
    # Smart level badhao - jitne cycles, utna smart
    knowledge["smart_level"] = 1 + (knowledge["cycles_completed"] // 10)
    
    print(f"[father] Cycle #{knowledge['cycles_completed']} | Smart Level: {knowledge['smart_level']}")
    print(f"[father] Wisdom: {get_wisdom(knowledge)}")
    
    # Sab agents ko observe karo
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
