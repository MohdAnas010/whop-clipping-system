# Editor Agent - Remotion

Remotion-based video renderer for 9:16 Shorts/Reels (1080x1920, 30fps).

## Setup

```bash
cd ~/workspace/whop-clipping-system/agents/editor
npm install
```

## Dev Preview

```bash
npx remotion studio
```

## Render from Scribe output

Scribe agent output JSON format:
```json
{
  "hook": "Ye Whop offer miss mat karo",
  "scriptLines": ["Line 1", "Line 2", "Line 3"],
  "caption": "Top Whop Offer #affiliate",
  "accentColor": "#00ff88"
}
```

Render:
```bash
node scripts/render.mjs --input ../scribe/output.json --output ./out/clip.mp4
```

Ya direct Remotion CLI:
```bash
npx remotion render ClipComposition ./out/clip.mp4 --props='{"hook":"..."}'
```

## Pipeline

1. **Scribe** → `output.json` (hook, scriptLines, caption)
2. **Editor (Remotion)** → `clip.mp4` (1080x1920, 35 sec)
3. **Dispatcher** → Instagram Reels / YouTube Shorts par upload

## Customization

- `src/ClipComposition.tsx` me colors, fonts, animations change karo
- `src/Root.tsx` me duration, dimensions change karo
- B-roll ya product screenshots ke liye `<Img>` ya `<Video>` components add karo
