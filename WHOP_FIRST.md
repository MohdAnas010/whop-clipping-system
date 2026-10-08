# Whop first: resume with a small, verifiable workflow

The older dispatcher and approver contain placeholders. An API key alone does not enable Instagram publishing or Whop Content Rewards submission. This mode prepares actual clips from campaign-approved video rather than generating affiliate promotion cards.

1. Pick a Content Rewards campaign that accepts your Instagram account and region. Read its brief, payout conditions, minimum views and remaining budget.
2. Copy `campaign.example.json` to `orchestrator/data/approved_campaign.json`. Set the real campaign URL, authorized local source video, rules and 1-3 clip ranges. After reviewing the campaign, set `status` to `approved`, `approved_by` to `user`, and `source_authorized` to `true`.
3. Install Node 22, `ffmpeg`/`ffprobe` and `pip install -r orchestrator/requirements.txt`. Run `npm install` in `agents/editor`. Rendering now uses Remotion with the actual source video and audio.
4. Run `python orchestrator/whop_first.py --preflight`, then `python orchestrator/whop_first.py`.
5. Review the MP4s and captions, publish on Instagram, and submit the actual Instagram post URLs in the campaign dashboard. Publishing/submission are not automated in this mode yet. A preparation report does not prove a post or payment exists.

## Token conservation

Trimming, rendering, validation and package creation use no LLM. Supply captions for zero API usage. If a caption is missing but a transcript and `GEMINI_API_KEY` are supplied, Gemini drafts it with an input cap, output cap, persistent cache and at most two new requests/day by default. No automatic retries or paid-provider fallback. Credentials belong in environment variables or GitHub Secrets, never source code or chat.

- `GEMINI_MODEL`: configurable, default `gemini-2.5-flash` (confirm availability in your account).
- `LLM_MAX_OUTPUT_TOKENS`: default 768, maximum 2048.
- `LLM_MAX_CALLS_PER_DAY`: default 2, set 0 to prohibit uncached calls.
- `DATA_DIR`: persistent private state/cache directory.
- `RENDER_OUT`: MP4 output directory.

Run only one process against each DATA_DIR. Daily limits are request limits, not billing guarantees. Gemini usage depends on your project's available quota and billing. ChatGPT subscription tokens cannot be moved into this service. Rendering, API access and hosting may have costs.

The GitHub workflow only runs when repository variable `WHOP_FIRST_ENABLED=true`. Provide approved campaign JSON in repository secret `APPROVED_CAMPAIGN_JSON` and optional `GEMINI_API_KEY`. Source video must be provisioned on the runner at its configured path; the workflow does not silently download arbitrary media. It only prepares clips; Instagram authorization and a verified submission method remain necessary for unattended publishing.

## Remotion editing

The default Whop-first renderer is Remotion (https://github.com/remotion-dev/remotion). `SourceClip` preserves the selected video/audio range, renders 1080×1920 at 30 fps, and supports a first-three-seconds `hook`, `fit: contain` (full frame) or `cover` (crop), and optional timed `subtitles`. Subtitle times are relative to the clip, not the full video. Supply real spoken text; no automatic transcript calls are made. Rendering uses one worker and cached completed MP4s to reduce resource use. Source assets stay local in a temporary public directory that is removed afterwards. No LLM tokens are used for editing.

Selected candidate checked 2026-10-08: [AAACLAN CLIPPING](https://contentrewards.com/c/campaigns/7308fb8c-6f87-4c31-b3b1-2cbf08919a54) by A4CLAN Campaign. Direct live page: accepting clips, Instagram $7/1K, min payout $1, max payout $650, $0 spent, $1,000 remaining (100%). Brief: clipping for AAAClan and SideBrother; no botting. Reference source: https://youtube.com/@ybrap?si=__KLYIH6VGbrifF8. Best rate among the qualifying candidates checked, not a verified global maximum. No campaign has been joined yet. Ben Affleck candidate excluded because remaining budget was below 50%.

## Persistent Instagram worker

`instagram_worker.py` implements official Instagram Login API container creation, processing checks, publish and permalink retrieval. Install/connect Metricool for secure account discovery and scheduling in ChatGPT; that connection does not automatically supply API credentials to this separate self-hosted worker. To self-host, supply `IG_ACCESS_TOKEN`, `IG_USER_ID`, and your Meta app's supported `META_API_VERSION` privately in environment variables. Copy `instagram.config.example.json` to `data/instagram_config.json`, set the authorized account's exact username and ID, and enable it after OAuth connection. Queued posts come from `data/instagram_queue.json` (see example). When `PUBLIC_MEDIA_BASE_URL` points to a HTTPS host serving `RENDER_OUT`, preparation automatically queues clips with supplied captions. Files are not automatically copied to an external host; provision that media host separately. The MP4 needs a public HTTPS URL readable by Meta; local render paths and ordinary Drive sharing links are not MP4 URLs.

Run `docker compose -f docker-compose.instagram.yml up -d --build` on an always-on server. Worker checks every minute; SQLite state persists in `data`, process restarts with Docker. Account matching prevents publishing to the wrong account. Cadence: 1/day for the first 3 days after the first actual post, 2/day through day 7, then 3/day, at least 4 hours apart. US/UK/Australia local-time posting windows are initial hypotheses; no guaranteed audience region. OAuth token expiry/revocation pauses publishing and requires reconnection; no unattended token-refresh implementation is claimed.

Each publish checks live budget; below 50% remaining or unreadable budget pauses the queue. Campaign page parsing may need updating if the website markup changes. Durable container IDs resume processing; publish intent is committed before sending, and uncertain results pause for reconciliation to prevent duplicate posts. No artificial watches, likes, follows, or comments. No LLM calls in the worker. Whop submission remains separate until a real supported submission method is verified. The chat cannot host a 24/7 process; actual deployment and credentials are still required.

Validation: Python unit tests and TypeScript compilation pass. A real Remotion render was attempted here but blocked by browser-download network access and the environment's network-interface restriction; an end-to-end render on a supported runner is still required.
