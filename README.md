# Whop Clipping Autonomous Agent System

100% free and open source multi-agent system for Whop affiliate short-form video automation. Runs 24/7 on any VPS with Docker.

## Agents

| Agent | Role |
|-------|------|
| **Scout** | Finds top Whop affiliate offers via API (highest payout first) |
| **CampaignFinder** | Searches full internet for best Whop campaigns, writes to Google Doc |
| **DriveReader** | Reads Google Drive campaign brief, extracts requirements |
| **Scribe** | Writes viral scripts with Ollama (Qwen/Llama, free) |
| **Stealth** | Humanizes content to avoid AI detection |
| **Editor** | Renders 9:16 videos with Remotion (free) |
| **Uploader** | Prepares upload packages per campaign Drive requirements |
| **Dispatcher** | Publishes to Instagram Reels (YouTube later) |
| **Approver** | Submits to Whop for campaign approval after upload |
| **Warmer** | Warms up account with Tier 1 engagement |
| **WhopOptimizer** | Keeps Whop profile professional, checks Instagram-Whop connection |
| **JoinWatcher** | Watches Whop for new joins, auto-starts work when you join (no need to tell) |
| **ProfileBuilder** | Builds professional Whop profile (bio, name, theme) - user ko kuch nahi karna |
| **SelfHealing (Father)** | EK HI KAAM: Sab agents ko EARNING ki taraf le jana. Har decision earning ke liye |
| **Competitor** | Analyzes competitors + best posting times |
| **Meta** | Self-improves the system every cycle |
| **Innovator** | Scouts GitHub/Hugging Face for upgrades |

## Quick Start

### Option A: GitHub Actions 24/7 (Free, No Credit Card) ⭐ Recommended

1. Push this repo to GitHub (public repo = unlimited minutes)
2. Go to repo Settings → Secrets → Actions → New secret:
   - Name: `WHOP_API_KEY`, Value: your Whop API key
3. Done! The workflow runs automatically every 6 hours.
   - Manual trigger: Actions tab → "Whop Clipping 24/7" → Run workflow
   - Outputs: Actions tab → click a run → Artifacts

### Option B: Docker on VPS

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/whop-clipping-system.git
cd whop-clipping-system

# 2. Set your Whop API key
export WHOP_API_KEY="your_key_here"

# 3. Run (pulls Ollama model on first start)
docker compose up -d --build

# 4. Logs
docker compose logs -f app
```

## Test Single Cycle

```bash
docker compose run --rm -e RUN_ONCE=1 app
```

## Configuration

| Env Var | Description |
|---------|-------------|
| `WHOP_API_KEY` | Whop API key (required for Scout) |
| `OLLAMA_MODEL` | LLM model (default: `qwen2.5:7b`) |
| `RUN_EVERY_HOURS` | Cycle interval (default: `6`) |
| `HUMAN_APPROVAL` | `true` to hold videos for review |
| `ENABLE_YOUTUBE` | `true` to enable YouTube Shorts |
| `YOUTUBE_API_KEY` | For competitor analysis |
| `GDRIVE_FOLDER_ID` | For Innovator approval videos |

## How It Works

```
Warmer → WhopOptimizer → JoinWatcher → Scout → DriveReader → Scribe → Stealth → Editor → Uploader → Dispatcher → Approver
                                                                              ↓
              CampaignFinder (daily) → Competitor → Meta → Innovator (daily) → SelfHealing (Father)
```

Every cycle (6h): warmup → optimize profile → check for new joins → find campaign → read Drive brief → write scripts → humanize → render → prepare upload → post → submit for approval → analyze → improve → father learns.

JoinWatcher: Tum bas Whop par Join dabao, kuch bolne ki zaroorat nahi. Ye khud detect karke kaam shuru kar dega.

## License

MIT - free for personal and commercial use. See [LICENSE](LICENSE).
