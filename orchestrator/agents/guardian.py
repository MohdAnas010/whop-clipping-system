"""Guardian Agent - Poore workflow ko leaks aur problems se bachata hai.

Ye agent har cycle me security check karta hai:

1. SECRET SCAN: Saare code files me hardcoded secrets dhoondhta hai
   - API keys, tokens, passwords jo code me likhe hon
   - Git remote URLs me embedded credentials
   - Shell commands me exposed secrets

2. GIT HISTORY CHECK: Pichle commits me leak hue secrets dhoondhta hai

3. GITIGNORE CHECK: Sensitive files gitignore me hain ya nahi

4. PRE-COMMIT GUARD: Commit se pehle scan karta hai, leak mile to rokta hai

5. SECURITY REPORT: Har cycle me report banata hai

SECRET PATTERNS jo detect karta hai:
- ghp_, gho_, github_pat_ (GitHub tokens)
- sk-, sk-ant-, xoxb-, xoxp- (API keys)
- AKIA (AWS keys)
- password/passwd/pwd assignments
- Bearer tokens in URLs
- https://user:pass@ or https://token@ URLs
"""
import os
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Project root (orchestrator se do level up)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Secret patterns - ye sab code me kabhi nahi hone chahiye
SECRET_PATTERNS = [
    # (name, regex, severity)
    ("github_pat", r"github_pat_[A-Za-z0-9_]+", "CRITICAL"),
    ("github_token_ghp", r"ghp_[A-Za-z0-9]{20,}", "CRITICAL"),
    ("github_token_gho", r"gho_[A-Za-z0-9]{20,}", "CRITICAL"),
    ("openai_key", r"sk-[A-Za-z0-9]{20,}", "CRITICAL"),
    ("anthropic_key", r"sk-ant-[A-Za-z0-9\-_]{20,}", "CRITICAL"),
    ("aws_key", r"AKIA[0-9A-Z]{16}", "CRITICAL"),
    ("slack_token", r"xox[bap]-[A-Za-z0-9\-]+", "HIGH"),
    ("url_with_credentials", r"https?://[^/\s:]+:[^/\s@]+@[^\s]+", "CRITICAL"),
    ("url_with_token", r"https?://[A-Za-z0-9_\-]{20,}@[^\s]+", "CRITICAL"),
    ("generic_api_key_assign", r"(?i)(api[_-]?key|apikey)\s*=\s*['\"][A-Za-z0-9\-_]{16,}['\"]", "HIGH"),
    ("generic_secret_assign", r"(?i)(secret|passwd|password)\s*=\s*['\"][^'\"]{8,}['\"]", "HIGH"),
    ("bearer_hardcoded", r"Bearer\s+[A-Za-z0-9\-_\.]{20,}", "HIGH"),
]

# Ye files scan hongi
SCAN_EXTENSIONS = {".py", ".js", ".ts", ".yml", ".yaml", ".json", ".env", ".sh", ".md", ".txt"}

# Ye directories skip hongi
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".ollama"}

# Sensitive files jo gitignore me hone chahiye
SENSITIVE_FILES = [".env", "*.pem", "*.key", "credentials.json", "*secret*"]


def scan_file_for_secrets(filepath):
    """Ek file me secrets dhoondho."""
    findings = []
    try:
        with open(filepath, "r", errors="ignore") as f:
            content = f.read()
    except Exception:
        return findings

    for name, pattern, severity in SECRET_PATTERNS:
        matches = re.finditer(pattern, content)
        for m in matches:
            # Line number nikalo
            line_no = content[:m.start()].count("\n") + 1
            # Match ko mask karo (pehle 4 chars + ****)
            raw = m.group(0)
            masked = raw[:4] + "****" if len(raw) > 8 else "****"
            findings.append({
                "file": str(filepath.relative_to(PROJECT_ROOT)),
                "line": line_no,
                "pattern": name,
                "severity": severity,
                "masked_match": masked,
            })
    return findings


def scan_project():
    """Poore project me secrets scan karo."""
    print("[guardian] Project me secrets scan kar rahe hain...")
    all_findings = []

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Skip directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in files:
            ext = Path(fname).suffix.lower()
            if ext not in SCAN_EXTENSIONS:
                continue
            # .gitignore wali files skip karo agar wo khud sensitive hain
            fpath = Path(root) / fname
            findings = scan_file_for_secrets(fpath)
            all_findings.extend(findings)

    return all_findings


def check_git_remote_for_credentials():
    """Git remote URLs me credentials to nahi hain."""
    print("[guardian] Git remote URLs check kar rahe hain...")
    findings = []
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.split("\n"):
            # https://TOKEN@github.com ya https://user:pass@ check karo
            if re.search(r"https?://[^/\s@]+@[^\s]+", line):
                findings.append({
                    "issue": "Git remote URL me credentials hain!",
                    "detail": re.sub(r"(https?://)[^@]+@", r"\1****@", line.strip()),
                    "severity": "CRITICAL",
                    "fix": "git remote set-url origin https://github.com/USER/REPO.git (bina token ke)",
                })
    except Exception as e:
        print(f"[guardian] Git remote check fail: {e}")
    return findings


def check_gitignore():
    """Sensitive files gitignore me hain ya nahi."""
    print("[guardian] .gitignore check kar rahe hain...")
    findings = []
    gitignore_path = PROJECT_ROOT / ".gitignore"

    if not gitignore_path.exists():
        findings.append({
            "issue": ".gitignore file nahi hai!",
            "severity": "HIGH",
            "fix": ".gitignore banao aur sensitive patterns add karo",
        })
        return findings

    try:
        with open(gitignore_path) as f:
            content = f.read()
        for pattern in SENSITIVE_FILES:
            # Simple check: pattern ya uska base gitignore me hai ya nahi
            base = pattern.replace("*", "").replace(".", "")
            if base and base not in content and pattern not in content:
                findings.append({
                    "issue": f".gitignore me '{pattern}' nahi hai",
                    "severity": "MEDIUM",
                    "fix": f".gitignore me '{pattern}' add karo",
                })
    except Exception as e:
        print(f"[guardian] gitignore check fail: {e}")

    return findings


def check_git_history_for_secrets():
    """Git history me leak hue secrets check karo (last 20 commits)."""
    print("[guardian] Git history check kar rahe hain (last 20 commits)...")
    findings = []
    try:
        # Har commit ka diff lo aur secrets dhoondho
        result = subprocess.run(
            ["git", "log", "--oneline", "-20", "--format=%H"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=15,
        )
        commits = result.stdout.strip().split("\n")
        for commit in commits[:20]:
            if not commit:
                continue
            diff = subprocess.run(
                ["git", "show", commit, "--format="],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=15,
            )
            for name, pattern, severity in SECRET_PATTERNS[:8]:  # Sirf critical patterns
                if re.search(pattern, diff.stdout):
                    findings.append({
                        "issue": f"Commit {commit[:8]} me possible secret leak!",
                        "pattern": name,
                        "severity": "CRITICAL",
                        "fix": "Us commit se secret hatao, key rotate karo, history clean karo",
                    })
                    break  # Ek commit me ek hi report
    except Exception as e:
        print(f"[guardian] Git history check fail: {e}")
    return findings


def auto_fix_gitignore():
    """.gitignore me missing patterns add karo."""
    gitignore_path = PROJECT_ROOT / ".gitignore"
    needed = [".env", "*.pem", "*.key", "credentials.json", "*secret*", ".last_user_instruction"]
    added = []
    try:
        existing = ""
        if gitignore_path.exists():
            with open(gitignore_path) as f:
                existing = f.read()
        with open(gitignore_path, "a") as f:
            for pattern in needed:
                if pattern not in existing:
                    f.write(f"\n{pattern}")
                    added.append(pattern)
        if added:
            print(f"[guardian] .gitignore me add kiya: {', '.join(added)}")
    except Exception as e:
        print(f"[guardian] .gitignore fix fail: {e}")
    return added


def run():
    """Guardian ka kaam - poore workflow ko secure rakho."""
    print("[guardian] 🛡️  Workflow security check shuru...")
    print("[guardian] NOTE: Ye agent secrets ko kabhi print/log nahi karta, sirf masked form me.")

    # 1. Code me secrets scan karo
    secret_findings = scan_project()

    # 2. Git remote check karo
    remote_findings = check_git_remote_for_credentials()

    # 3. Gitignore check karo
    gitignore_findings = check_gitignore()

    # 4. Git history check karo
    history_findings = check_git_history_for_secrets()

    # Auto-fix: gitignore theek karo
    gitignore_fixed = auto_fix_gitignore()

    # Critical issues gino
    critical = [f for f in secret_findings + remote_findings + history_findings
                if f.get("severity") == "CRITICAL"]

    # Report banao
    out_dir = PROJECT_ROOT / "orchestrator" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "checked_at": datetime.now().isoformat(),
        "secrets_in_code": secret_findings,
        "git_remote_issues": remote_findings,
        "gitignore_issues": gitignore_findings,
        "git_history_issues": history_findings,
        "gitignore_auto_fixed": gitignore_fixed,
        "total_findings": len(secret_findings) + len(remote_findings) + len(gitignore_findings) + len(history_findings),
        "critical_count": len(critical),
        "status": "DANGER" if critical else ("WARNING" if secret_findings or remote_findings or gitignore_findings else "SECURE"),
        "honest_note": "Ye agent secrets ko detect karta hai, lekin leak ho chuke secrets ko wapas nahi le sakta. Leak hui keys ko turant rotate karo.",
    }

    with open(out_dir / "guardian_report.json", "w") as f:
        json.dump(report, f, indent=2)

    # Console output
    print(f"[guardian] Status: {report['status']}")
    print(f"[guardian] Total findings: {report['total_findings']} | Critical: {report['critical_count']}")
    for finding in secret_findings:
        print(f"[guardian] ⚠️  {finding['severity']}: {finding['file']}:{finding['line']} ({finding['pattern']})")
    for finding in remote_findings:
        print(f"[guardian] ⚠️  {finding['severity']}: {finding['issue']}")
    for finding in history_findings:
        print(f"[guardian] ⚠️  {finding['severity']}: {finding['issue']}")

    if report["status"] == "SECURE":
        print("[guardian] ✅ Koi leak nahi mila. Workflow secure hai.")

    return report


def pre_commit_check():
    """Commit se pehle chalao. Agar CRITICAL leak hai to False return karo (commit roko)."""
    print("[guardian] Pre-commit security check...")
    secret_findings = scan_project()
    remote_findings = check_git_remote_for_credentials()
    critical = [f for f in secret_findings + remote_findings if f.get("severity") == "CRITICAL"]
    if critical:
        print(f"[guardian] 🛑 COMMIT ROKO! {len(critical)} critical leak mile:")
        for c in critical:
            print(f"  - {c.get('file', '')}:{c.get('line', '')} ({c.get('pattern', c.get('issue', ''))})")
        return False
    print("[guardian] ✅ Pre-commit check pass. Commit kar sakte ho.")
    return True


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--pre-commit":
        ok = pre_commit_check()
        sys.exit(0 if ok else 1)
    print(json.dumps(run(), indent=2, ensure_ascii=False))
