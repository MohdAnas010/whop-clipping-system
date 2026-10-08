"""Persistent Instagram publisher. Official API only; no synthetic engagement.

Run one worker per DATA_DIR. Persist intent before publishing: ambiguous responses
pause for reconciliation rather than issuing a second publish request.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sqlite3
import time
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import requests

class APIError(RuntimeError):
    pass

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'): self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.hidden = max(0, self.hidden - 1)
    def handle_data(self, data):
        if not self.hidden: self.parts.append(data.strip())

def parse_budget(html):
    parser = TextParser()
    parser.feed(html)
    text = ' '.join(parser.parts).replace('\u2066', '').replace('\u2069', '')
    match = re.search(r'Budget\s*\$([\d,.]+)\s*\$([\d,.]+)\s*remaining', text)
    if not match:
        raise APIError('Cannot verify live campaign budget; publishing paused')
    spent, remaining = [float(v.replace(',', '')) for v in match.groups()]
    total = spent + remaining
    if total <= 0: raise APIError('Campaign budget invalid')
    return remaining / total

class Instagram:
    def __init__(self):
        self.token = os.environ.get('IG_ACCESS_TOKEN', '')
        self.user = os.environ.get('IG_USER_ID', '')
        version = os.environ.get('META_API_VERSION', '')
        if not self.token or not self.user or not re.fullmatch(r'v\d+\.\d+', version):
            raise APIError('Instagram OAuth token, account ID and Meta API version required')
        self.base = 'https://graph.instagram.com/' + version
    def call(self, method, path, **values):
        try:
            response = requests.request(method, self.base + '/' + path,
                headers={'Authorization': 'Bearer ' + self.token},
                **({'params': values} if method == 'GET' else {'data': values}), timeout=45)
            body = response.json()
        except (requests.RequestException, ValueError):
            raise APIError('Instagram response unavailable') from None
        if response.status_code >= 400 or 'error' in body:
            code = body.get('error', {}).get('code', response.status_code)
            raise APIError('Instagram API error code ' + str(code))
        return body
    def profile(self):
        return self.call('GET', self.user, fields='id,username')
    def create(self, video_url, caption):
        return self.call('POST', self.user + '/media', media_type='REELS',
            video_url=video_url, caption=caption, share_to_feed='true')['id']
    def status(self, container):
        return self.call('GET', container, fields='status_code')['status_code']
    def publish(self, container):
        return self.call('POST', self.user + '/media_publish', creation_id=container)['id']
    def permalink(self, media):
        return self.call('GET', media, fields='permalink')['permalink']

def allowed_limit(first_publish, now):
    # Gradual publishing cadence, not an Instagram safety guarantee.
    days = 0 if first_publish is None else (now - first_publish) / 86400
    return 1 if days < 3 else 2 if days < 7 else 3

def in_slot(now, slots):
    dt = datetime.fromtimestamp(now, timezone.utc)
    for slot in slots:
        local = dt.astimezone(ZoneInfo(slot['timezone']))
        if local.hour == int(slot['hour']) and local.minute < 30:
            return True
    return False

class Worker:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / 'instagram.sqlite')
        self.db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, payload TEXT NOT NULL, '
            'state TEXT NOT NULL, container TEXT, media TEXT, permalink TEXT, published_at REAL)')
        self.db.commit()
    def report(self, **values):
        dest = self.root / 'instagram_status.json'
        temp = dest.with_suffix('.tmp')
        temp.write_text(json.dumps({'checked_at': datetime.now(timezone.utc).isoformat(), **values}, indent=2))
        temp.replace(dest)
        return values
    def ingest(self):
        queue = self.root / 'instagram_queue.json'
        if not queue.exists(): return
        for item in json.loads(queue.read_text()):
            url = urlparse(item['video_url'])
            if url.scheme != 'https' or not url.hostname:
                raise APIError('Public HTTPS MP4 URL required')
            if not item.get('caption') or item.get('language') != 'en':
                raise APIError('Factual English caption required')
            digest = hashlib.sha256(item['content_id'].encode()).hexdigest()
            self.db.execute('INSERT OR IGNORE INTO jobs(id,payload,state) VALUES(?,?,?)',
                (digest, json.dumps(item), 'queued'))
        self.db.commit()
    def tick(self, now=None, client=None, budget_checker=None):
        now = now or time.time()
        config_path = self.root / 'instagram_config.json'
        if not config_path.exists(): return self.report(status='blocked', reason='Instagram configuration missing')
        config = json.loads(config_path.read_text())
        if not config.get('enabled'): return self.report(status='disabled')
        try:
            api = client or Instagram()
            profile = api.profile()
            if profile['username'] != config['instagram_username'] or str(profile['id']) != str(config['instagram_user_id']):
                raise APIError('Authorized Instagram account does not match configured account')
            profile_url = 'https://www.instagram.com/' + profile['username'] + '/'
            self.ingest()
            if self.db.execute("SELECT 1 FROM jobs WHERE state='publish_unknown'").fetchone():
                return self.report(status='needs_reconciliation', instagram=profile_url)
            count, first, last = self.db.execute("SELECT SUM(CASE WHEN published_at > ? THEN 1 ELSE 0 END), "
                "MIN(published_at), MAX(published_at) FROM jobs WHERE state='published'", (now-86400,)).fetchone()
            if (count or 0) >= allowed_limit(first, now) or (last and now-last < 4*3600):
                return self.report(status='waiting_cadence', instagram=profile_url)
            row = self.db.execute("SELECT id,payload,state,container FROM jobs WHERE state IN ('queued','processing') ORDER BY rowid LIMIT 1").fetchone()
            if not row: return self.report(status='idle', instagram=profile_url)
            ident, payload, state, container = row
            item = json.loads(payload)
            if item['campaign_url'] != config['campaign_url']:
                raise APIError('Queue campaign does not match selected campaign')
            if not config.get('rules_verified'):
                raise APIError('Campaign rules have not been verified')
            if budget_checker:
                fraction = budget_checker(item['campaign_url'])
            else:
                response = requests.get(item['campaign_url'], timeout=30)
                if response.status_code != 200: raise APIError('Live campaign budget unavailable')
                fraction = parse_budget(response.text)
            if fraction < 0.5:
                return self.report(status='campaign_paused', remaining_fraction=fraction, instagram=profile_url)
            if not in_slot(now, config['posting_slots']):
                return self.report(status='waiting_slot', instagram=profile_url)
            if not container:
                # A creation timeout may leave an orphan container, but cannot create a post.
                container = api.create(item['video_url'], item['caption'])
                self.db.execute("UPDATE jobs SET container=?,state='processing' WHERE id=?", (container, ident))
                self.db.commit()
            status = api.status(container)
            if status in ('ERROR','EXPIRED'):
                self.db.execute("UPDATE jobs SET state='failed' WHERE id=?", (ident,)); self.db.commit()
                return self.report(status='container_failed', instagram=profile_url)
            if status != 'FINISHED': return self.report(status='processing', instagram=profile_url)
            # Intent committed before request: never retry an ambiguous publication.
            self.db.execute("UPDATE jobs SET state='publish_unknown' WHERE id=?", (ident,)); self.db.commit()
            media = api.publish(container)
            self.db.execute("UPDATE jobs SET state='published',media=?,published_at=? WHERE id=?", (media, now, ident)); self.db.commit()
            try:
                link = api.permalink(media)
                self.db.execute('UPDATE jobs SET permalink=? WHERE id=?', (link, ident)); self.db.commit()
            except APIError:
                link = None
            return self.report(status='published', media_id=media, permalink=link, instagram=profile_url,
                whop_submission='pending_verified_submission_method')
        except (APIError, requests.RequestException, ValueError, KeyError, TypeError, OSError) as error:
            return self.report(status='blocked', reason=str(error) if isinstance(error, APIError) else type(error).__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    worker = Worker(os.getenv('DATA_DIR', str(Path(__file__).parent / 'data')))
    while True:
        print(json.dumps(worker.tick()), flush=True)
        if args.once: break
        time.sleep(60)
