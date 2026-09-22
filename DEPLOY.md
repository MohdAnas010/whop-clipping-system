# Whop Clipping System - Docker Deployment (Free Stack)

USA VPS par chalane ke liye, 100% free/open source.

## Stack
- **Ollama** + `qwen2.5:7b` (Hugging Face via Ollama, free LLM - Gemini ki jagah)
- **Remotion** (Editor agent, free)
- **Python orchestrator** (Scout/Scribe/Editor/Dispatcher/Meta agents)
- **Meta agent** - har run ke baad system ko khud improve karta hai

## Agents
1. **Scout** - Whop API se top affiliate offers dhoondhta hai
2. **Scribe** - Ollama se viral Hindi/Hinglish scripts likhta hai
3. **Editor** - Remotion se 9:16 video render karta hai
4. **Dispatcher** - Instagram Reels + YouTube Shorts par bhejta hai
5. **Meta** - Har cycle ke baad analyze karke prompts aur rules improve karta hai

## USA VPS par deploy karo

```bash
# 1. VPS lo (USA region) - Hetzner, Contabo, ya Oracle Free Tier
# 2. Docker install karo
curl -fsSL https://get.docker.com | sh

# 3. Code copy karo
git clone <tumhara-repo> whop-clipping-system
cd whop-clipping-system

# 4. Whop API key set karo
export WHOP_API_KEY="tumhari_key"

# 5. Chalao
docker compose up -d --build

# Logs dekho
docker compose logs -f app
```

## Test (ek cycle)
```bash
docker compose run --rm -e RUN_ONCE=1 app
```

## Competitor Analysis (free, open source)

```bash
# 1. data/competitors.json me apne competitors add karo
# 2. YouTube Data API key (free, 10k units/day) env me rakho:
export YOUTUBE_API_KEY="tumhari_key"
# 3. Har cycle me competitor agent automatically:
#    - Unke posting times analyze karega
#    - Best timing recommend karega (USA audience)
#    - data/competitor_analysis.json me report banayega
```

Best timing (USA audience):
- **Reels:** Tue-Thu, shaam 7-9 ET (IST subah 4:30-6:30)
- **Shorts:** Weekend dopahar ET

## Notes
- Pehli baar Ollama model download hoga (~4.7GB), time lagega
- `HUMAN_APPROVAL=true` rakho to videos `/app/data/approved` me approval ke liye rukenge
- Dispatcher me Instagram/YouTube API credentials abhi stub hain - Meta/Google ke free API se connect karo
- Meta agent ki reports: `data/improvements.md`
