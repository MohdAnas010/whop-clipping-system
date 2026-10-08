# Remotion editor

Uses https://github.com/remotion-dev/remotion to render source clips with real audio and optional timed subtitles.

Install Node 22, then `npm install`. The Whop-first Python workflow calls `scripts/render.mjs` automatically. Input JSON: `sourceVideo` (authorized absolute local path), `start`, `duration` (5–90 seconds), optional `hook`, `fit` (`contain` or `cover`) and `subtitles` (`start`, `end`, `text`, seconds relative to the clip).

`node scripts/render.mjs --input /path/to/input.json --output /path/to/clip.mp4`

Output: 1080×1920, 30 fps, H.264/AAC. Chromium is required; Remotion downloads its browser if absent. Set `REMOTION_BROWSER_EXECUTABLE` for an existing compatible browser. CPU rendering with concurrency 1; no LLM requests. Legacy text-only inputs still use `ClipComposition`.
