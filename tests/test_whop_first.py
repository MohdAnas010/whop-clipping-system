import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'orchestrator'))
from agents import llm
import whop_first

class BudgetTests(unittest.TestCase):
    def test_cache_and_failed_request_budget(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            'DATA_DIR': tmp, 'GEMINI_API_KEY': 'test-only', 'LLM_MAX_CALLS_PER_DAY': '1'
        }), patch.object(llm.requests, 'post') as post:
            post.return_value = Mock(status_code=200)
            post.return_value.json.return_value = {'candidates': [{'finishReason': 'STOP',
                'content': {'parts': [{'text': '{"caption":"hello"}'}]}}]}
            self.assertEqual(llm.generate_json('s', 'p')['caption'], 'hello')
            self.assertEqual(llm.generate_json('s', 'p')['caption'], 'hello')
            self.assertEqual(post.call_count, 1)
            with self.assertRaisesRegex(RuntimeError, 'limit reached'):
                llm.generate_json('s', 'different')
            self.assertEqual(post.call_count, 1)
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            'DATA_DIR': tmp, 'GEMINI_API_KEY': 'test-only', 'LLM_MAX_CALLS_PER_DAY': '1'
        }), patch.object(llm.requests, 'post', return_value=Mock(status_code=429)) as post:
            with self.assertRaisesRegex(RuntimeError, 'HTTP 429'):
                llm.generate_json('s', 'p')
            with self.assertRaisesRegex(RuntimeError, 'limit reached'):
                llm.generate_json('s', 'p')
            self.assertEqual(post.call_count, 1)

    def test_missing_campaign_consumes_no_api_calls(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(whop_first, 'DATA', Path(tmp)), \
                patch.object(llm.requests, 'post') as post, contextlib.redirect_stdout(io.StringIO()):
            report = whop_first.run(str(Path(tmp) / 'missing.json'))
            self.assertEqual(report['status'], 'blocked')
            self.assertEqual(report['published'], 0)
            self.assertEqual(report['submitted'], 0)
            post.assert_not_called()

    def test_campaign_requires_user_approval_and_real_source(self):
        with patch.object(whop_first.shutil, 'which', return_value='/usr/bin/ffmpeg'):
            errors = whop_first.validate({'status': 'approved', 'approved_by': 'join_watcher',
                'type': 'affiliate', 'clips': [{'start': 0, 'duration': -1}]})
            self.assertTrue(any('explicitly approve' in e for e in errors))
            self.assertTrue(any('not an affiliate' in e for e in errors))
            self.assertTrue(any('source video missing' in e for e in errors))

class RemotionTests(unittest.TestCase):
    def test_source_props_cache_and_zero_llm_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.mp4'
            source.write_bytes(b'test source')
            campaign = {'status': 'approved', 'approved_by': 'user', 'type': 'content_rewards',
                'campaign_url': 'https://contentrewards.com/c/campaigns/test',
                'source_authorized': True, 'allowed_platforms': ['instagram'],
                'source_video': str(source), 'requirements': {},
                'clips': [{'start': 2, 'duration': 5, 'caption': 'Supplied caption',
                    'hook': 'A real moment', 'subtitles': [{'start': 0, 'end': 2, 'text': 'Actual words'}]}]}
            config = root / 'campaign.json'
            config.write_text(json.dumps(campaign))
            def execute(args, **kwargs):
                if args[0] == 'ffprobe':
                    return Mock(stdout='10')
                self.assertEqual(args[0], 'node')
                props = json.loads(Path(args[args.index('--input') + 1]).read_text())
                self.assertEqual(props['start'], 2)
                self.assertEqual(props['duration'], 5)
                self.assertEqual(props['subtitles'][0]['text'], 'Actual words')
                Path(args[args.index('--output') + 1]).write_bytes(b'rendered')
                return Mock()
            with patch.object(whop_first, 'DATA', root / 'data'), \
                patch.object(whop_first, 'OUT', root / 'out'), \
                patch.object(whop_first, 'validate', return_value=[]), \
                patch.object(whop_first.subprocess, 'run', side_effect=execute) as run, \
                patch.object(whop_first, 'generate_json') as llm_call, \
                contextlib.redirect_stdout(io.StringIO()):
                first = whop_first.run(config)
                second = whop_first.run(config)
                self.assertEqual(first['status'], 'prepared')
                self.assertEqual(second['renderer'], 'remotion')
                self.assertEqual(sum(call.args[0][0] == 'node' for call in run.call_args_list), 1)
                llm_call.assert_not_called()

if __name__ == '__main__':
    unittest.main()
