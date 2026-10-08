# Whop first: resume with a small, verifiable workflow

The older dispatcher and approver contain placeholders. An API key alone does not enable Instagram publishing or Whop Content Rewards submission. This mode prepares actual clips from campaign-approved video rather than generating affiliate promotion cards.

1. Pick a Content Rewards campaign that accepts your Instagram account and region. Read its brief, payout conditions, minimum views and remaining budget.
2. Copy `campaign.example.json` to `orchestrator/data/approved_campaign.json`. Set the real campaign URL, authorized local source video, rules and 1-3 clip ranges. After reviewing the campaign, set `status` to `approved`, `approved_by` to `user`, and `source_authorized` to `true`.
3. Install `ffmpeg`/`ffprobe` and `pip install -r orchestrator/requirements.txt`.
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
