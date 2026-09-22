#!/usr/bin/env node
/**
 * Render script for Editor agent.
 * Takes Scribe JSON output and renders via Remotion.
 *
 * Usage:
 *   node scripts/render.mjs --input ../scribe/output.json --output ./out/clip.mp4
 *
 * Input JSON format:
 * {
 *   "hook": "...",
 *   "scriptLines": ["...", "..."],
 *   "caption": "...",
 *   "accentColor": "#00ff88"
 * }
 */
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
import {readFileSync, mkdirSync} from 'fs';
import {resolve, dirname} from 'path';

const args = process.argv.slice(2);
const getArg = (name) => {
  const idx = args.indexOf(name);
  return idx !== -1 ? args[idx + 1] : null;
};

const inputPath = getArg('--input');
const outputPath = getArg('--output') || './out/clip.mp4';

if (!inputPath) {
  console.error('Usage: node scripts/render.mjs --input <scribe-json> --output <mp4>');
  process.exit(1);
}

const inputData = JSON.parse(readFileSync(resolve(inputPath), 'utf-8'));
mkdirSync(dirname(resolve(outputPath)), {recursive: true});

console.log('Bundling Remotion project...');
const bundleLocation = await bundle({
  entryPoint: resolve('./src/index.ts'),
  webpackOverride: (config) => config,
});

console.log('Selecting composition...');
const composition = await selectComposition({
  serveUrl: bundleLocation,
  id: 'ClipComposition',
  inputProps: {
    hook: inputData.hook,
    scriptLines: inputData.scriptLines || [],
    caption: inputData.caption || '',
    backgroundColor: '#0a0a0a',
    accentColor: inputData.accentColor || '#00ff88',
  },
});

console.log(`Rendering to ${outputPath}...`);
await renderMedia({
  composition,
  serveUrl: bundleLocation,
  codec: 'h264',
  outputLocation: resolve(outputPath),
  inputProps: {
    hook: inputData.hook,
    scriptLines: inputData.scriptLines || [],
    caption: inputData.caption || '',
    backgroundColor: '#0a0a0a',
    accentColor: inputData.accentColor || '#00ff88',
  },
});

console.log('Done:', outputPath);
