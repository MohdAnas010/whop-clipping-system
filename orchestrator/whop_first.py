"""Whop Content Rewards preparation: approved source -> real clips -> upload package.

No artificial engagement, account warmup, model loop, or unsupported submission API.
One process at a time; keep DATA_DIR persistent for request limits and cached outputs.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
from urllib.parse import urlparse
from agents.llm import generate_json

DATA = Path(os.getenv('DATA_DIR', str(Path(__file__).resolve().parent / 'data')))
OUT = Path(os.getenv('RENDER_OUT', str(Path(__file__).resolve().parent / 'out')))


def validate(campaign):
    errors = []
    if campaign.get('approved_by') != 'user' or campaign.get('status') != 'approved':
        errors.append('Select and explicitly approve a campaign first')
    if campaign.get('type') != 'content_rewards':
        errors.append('Campaign must be Content Rewards, not an affiliate offer')
    url = urlparse(str(campaign.get('campaign_url', '')))
    if url.scheme != 'https' or url.hostname not in {'whop.com', 'web.whop.com', 'contentrewards.com'}:
        errors.append('Valid Whop/Content Rewards campaign URL required')
    if campaign.get('source_authorized') is not True:
        errors.append('Campaign must permit reuse of this source')
    if 'instagram' not in campaign.get('allowed_platforms', []):
        errors.append('Campaign must allow Instagram')
    if not isinstance(campaign.get('requirements'), dict):
        errors.append('Campaign brief/requirements required')
    if not Path(str(campaign.get('source_video') or '__missing__')).is_file():
        errors.append('Local campaign source video missing')
    clips = campaign.get('clips', [])
    if not isinstance(clips, list) or not 1 <= len(clips) <= 3:
        errors.append('Provide 1-3 approved clip ranges')
    else:
        for clip in clips:
            try:
                start, duration = float(clip['start']), float(clip['duration'])
                if not math.isfinite(start) or not math.isfinite(duration) or start < 0 or not 5 <= duration <= 90:
                    raise ValueError()
            except (ValueError, TypeError, KeyError):
                errors.append('Clip start must be >=0; duration must be 5-90 seconds')
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        errors.append('ffmpeg and ffprobe required')
    return errors


def run(campaign_path, preflight=False):
    DATA.mkdir(parents=True, exist_ok=True)
    report = {'status': 'blocked', 'published': 0, 'submitted': 0, 'blockers': []}
    try:
        campaign = json.loads(Path(campaign_path).read_text())
        if not isinstance(campaign, dict):
            raise ValueError()
    except (OSError, ValueError):
        report['blockers'] = ['Approved campaign configuration missing or invalid']
        campaign = {}
    if campaign:
        report['blockers'] = validate(campaign)
    if report['blockers']:
        pass
    elif preflight:
        report['status'] = 'ready_to_prepare'
    else:
        try:
            source = str(Path(campaign['source_video']).resolve())
            probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                    '-of', 'default=noprint_wrappers=1:nokey=1', source],
                                   capture_output=True, text=True, check=True, timeout=30)
            length = float(probe.stdout.strip())
            for clip in campaign['clips']:
                if float(clip['start']) + float(clip['duration']) > length:
                    raise ValueError('Clip extends beyond source video')
            OUT.mkdir(parents=True, exist_ok=True)
            packages = []
            for index, clip in enumerate(campaign['clips']):
                signature = hashlib.sha256(json.dumps([campaign, index, Path(source).stat().st_mtime_ns],
                                                     sort_keys=True).encode()).hexdigest()[:16]
                video = OUT / f'clip-{signature}.mp4'
                if not video.exists():
                    temporary = OUT / f'clip-{signature}.partial.mp4'
                    subprocess.run(['ffmpeg', '-nostdin', '-y', '-v', 'error', '-ss', str(clip['start']),
                                    '-i', source, '-t', str(clip['duration']), '-vf',
                                    'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2',
                                    '-c:v', 'libx264', '-preset', 'fast', '-c:a', 'aac',
                                    '-movflags', '+faststart', str(temporary)], check=True, timeout=600)
                    temporary.replace(video)
                caption = clip.get('caption', '')
                if not caption and os.getenv('GEMINI_API_KEY') and clip.get('transcript'):
                    try:
                        draft = generate_json('Write one factual Instagram caption as JSON {"caption":"..."}. '
                                              'Use only supplied facts, follow the campaign requirements, no invented claims.',
                                              json.dumps({'transcript': clip['transcript'],
                                                          'requirements': campaign['requirements']}))
                        caption = draft.get('caption', '')
                    except (RuntimeError, ValueError, requests_error):
                        caption = ''
                packages.append({'video_path': str(video), 'caption': caption,
                                 'campaign_url': campaign['campaign_url'], 'requirements': campaign['requirements'],
                                 'status': 'awaiting_review_and_instagram_publish'})
            (DATA / 'upload_packages.json').write_text(json.dumps(packages, indent=2))
            report.update(status='prepared', clips=len(packages),
                          next_action='Review clips/captions, publish on Instagram, submit actual post URLs in Whop')
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            report['blockers'] = [f'Preparation failed: {type(error).__name__}']
    (DATA / 'whop_first_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return report


# Network failures are handled without dumping request headers or API keys.
from requests.exceptions import RequestException as requests_error

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaign', default=str(DATA / 'approved_campaign.json'))
    parser.add_argument('--preflight', action='store_true')
    args = parser.parse_args()
    result = run(args.campaign, args.preflight)
    raise SystemExit(0 if result['status'] in {'prepared', 'ready_to_prepare'} else 2)
