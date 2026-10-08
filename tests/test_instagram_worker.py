import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'orchestrator'))
from instagram_worker import Worker, APIError, parse_budget, allowed_limit

class InstagramWorkerTests(unittest.TestCase):
    def setup_worker(self, root):
        config = {'enabled': True, 'instagram_username': 'test_creator', 'instagram_user_id': '123',
                  'campaign_url': 'https://contentrewards.com/c/campaigns/test', 'rules_verified': True,
                  'posting_slots': [{'timezone': 'UTC', 'hour': 0}]}
        (root / 'instagram_config.json').write_text(json.dumps(config))
        (root / 'instagram_queue.json').write_text(json.dumps([{'content_id': 'unique-test',
            'video_url': 'https://example.com/video.mp4', 'caption': 'Real clip', 'language': 'en',
            'campaign_url': config['campaign_url']}]))
        api = Mock()
        api.profile.return_value = {'id': '123', 'username': 'test_creator'}
        api.create.return_value = 'container'
        api.status.return_value = 'FINISHED'
        api.publish.return_value = 'media'
        api.permalink.return_value = 'https://www.instagram.com/reel/test/'
        return Worker(root), api

    def test_budget_and_cadence(self):
        self.assertEqual(parse_budget('<div>Budget</div><div>$0</div><div>$1,000 remaining</div>'), 1)
        self.assertEqual(parse_budget('Budget $500 $500 remaining'), .5)
        with self.assertRaises(APIError): parse_budget('No budget')
        self.assertEqual(allowed_limit(None, 1), 1)
        self.assertEqual(allowed_limit(1, 4*86400), 2)
        self.assertEqual(allowed_limit(1, 8*86400), 3)

    def test_publish_once_and_budget_pause(self):
        with tempfile.TemporaryDirectory() as tmp:
            worker, api = self.setup_worker(Path(tmp))
            now = 86400 * 20000 + 10
            self.assertEqual(worker.tick(now, api, lambda url: .49)['status'], 'campaign_paused')
            api.create.assert_not_called()
            self.assertEqual(worker.tick(now, api, lambda url: .75)['status'], 'published')
            worker.tick(now+60, api, lambda url: .75)
            api.publish.assert_called_once()
            self.assertEqual(worker.db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 1)
            worker.db.close()

    def test_ambiguous_publish_pauses_without_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            worker, api = self.setup_worker(Path(tmp))
            now = 86400 * 20000 + 10
            api.publish.side_effect = APIError('Instagram response unavailable')
            self.assertEqual(worker.tick(now, api, lambda url: 1)['status'], 'blocked')
            self.assertEqual(worker.tick(now+60, api, lambda url: 1)['status'], 'needs_reconciliation')
            api.publish.assert_called_once()
            worker.db.close()

    def test_wrong_account_never_uploads(self):
        with tempfile.TemporaryDirectory() as tmp:
            worker, api = self.setup_worker(Path(tmp))
            api.profile.return_value['username'] = 'different_account'
            self.assertEqual(worker.tick(86400 * 20000 + 10, api, lambda url: 1)['status'], 'blocked')
            api.create.assert_not_called()
            worker.db.close()

if __name__ == '__main__': unittest.main()
