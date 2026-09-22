# Whop Clipping Autonomous Agent System

100% free and open source multi-agent system for Whop affiliate short-form video automation. Runs 24/7 on any VPS with Docker.

## Agents

| Agent | Role |
|-------|------|
| **Scout** | Finds top Whop affiliate offers via API |
| **Scribe** | Writes viral scripts with Ollama (Qwen/Llama, free) |
| **Stealth** | Humanizes content to avoid AI detection |
| **Editor** | Renders 9:16 videos with Remotion (free) |
| **Dispatcher** | Publishes to Instagram Reels (YouTube later) |
| **Warmer** | Warms up account with Tier 1 engagement |
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
Warmer → Scout → Scribe → Stealth → Editor → Dispatcher
                                              ↓
              Competitor → Meta → Innovator (daily)
```

Every cycle (6h): warmup → find offers → write scripts → humanize → render → post → analyze → improve.

## License

MIT - free for personal and commercial use. See [LICENSE](LICENSE).
