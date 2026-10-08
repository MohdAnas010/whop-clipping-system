#!/usr/bin/env node
// Authorized local video -> 9:16 Remotion edit. No LLM calls.
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
import {readFileSync, mkdirSync, copyFileSync, mkdtempSync, rmSync, existsSync} from 'node:fs';
import {resolve, dirname, extname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {tmpdir} from 'node:os';

const args = process.argv.slice(2);
const arg = (name) => args.includes(name) ? args[args.indexOf(name) + 1] : null;
if (!arg('--input') || !arg('--output')) throw new Error('Use --input <json> --output <mp4>');
const project = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(readFileSync(resolve(arg('--input')), 'utf8'));
const output = resolve(arg('--output'));
const temp = mkdtempSync(resolve(tmpdir(), 'whop-remotion-'));
try {
  let id = 'ClipComposition';
  let inputProps = {...data, backgroundColor: '#0a0a0a', accentColor: data.accentColor || '#00ff88',
    scriptLines: data.scriptLines || [], caption: data.caption || ''};
  if (data.sourceVideo) {
    if (!existsSync(data.sourceVideo)) throw new Error('Source video missing');
    if (!Number.isFinite(data.start) || data.start < 0 || !Number.isFinite(data.duration) ||
      data.duration < 5 || data.duration > 90) throw new Error('Invalid source clip range');
    if (data.fit && !['contain', 'cover'].includes(data.fit)) throw new Error('Invalid fit');
    const subtitles = data.subtitles || [];
    if (!Array.isArray(subtitles) || subtitles.some((cue) => !Number.isFinite(cue.start) ||
      !Number.isFinite(cue.end) || cue.start < 0 || cue.end <= cue.start || cue.end > data.duration ||
      typeof cue.text !== 'string')) throw new Error('Invalid clip-relative subtitle timing');
    const source = 'source' + extname(data.sourceVideo);
    copyFileSync(resolve(data.sourceVideo), resolve(temp, source));
    id = 'SourceClip';
    inputProps = {source, start: data.start, duration: data.duration, hook: data.hook || '',
      fit: data.fit || 'contain', subtitles};
  }
  mkdirSync(dirname(output), {recursive: true});
  const serveUrl = await bundle({entryPoint: resolve(project, 'src/index.ts'), publicDir: temp});
  const browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE || undefined;
  const composition = await selectComposition({serveUrl, id, inputProps, browserExecutable});
  await renderMedia({composition, serveUrl, inputProps, codec: 'h264', audioCodec: 'aac',
    outputLocation: output, concurrency: 1, browserExecutable});
  console.log('Rendered:', output);
} finally {
  rmSync(temp, {recursive: true, force: true});
}
