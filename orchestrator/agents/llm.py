"""Gemini JSON generation with persistent cache and a daily request ceiling."""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import requests


def generate_json(system, prompt):
    model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    key = os.getenv('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY missing; no request made')
    maximum = max(1, min(2048, int(os.getenv('LLM_MAX_OUTPUT_TOKENS', '768'))))
    root = Path(os.getenv('DATA_DIR', str(Path(__file__).resolve().parents[1] / 'data')))
    cache = root / 'llm_cache'
    cache.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(json.dumps([model, system, prompt, maximum]).encode()).hexdigest()
    cached = cache / (digest + '.json')
    if cached.exists():
        return json.loads(cached.read_text())
    today = datetime.now(timezone.utc).date().isoformat()
    ledger = root / 'llm_budget.json'
    usage = json.loads(ledger.read_text()) if ledger.exists() else {}
    if usage.get('date') != today:
        usage = {'date': today, 'requests': 0, 'reported_tokens': 0}
    limit = max(0, int(os.getenv('LLM_MAX_CALLS_PER_DAY', '2')))
    if usage['requests'] >= limit:
        raise RuntimeError('Daily Gemini request limit reached; no request made')
    # Reserve before the request: failed requests also consume the request budget.
    usage['requests'] += 1
    ledger.write_text(json.dumps(usage))
    config = {'responseMimeType': 'application/json', 'maxOutputTokens': maximum,
              'temperature': 0.4}
    if model.startswith('gemini-2.5-flash'):
        config['thinkingConfig'] = {'thinkingBudget': 0}
    response = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
        headers={'x-goog-api-key': key},
        json={'systemInstruction': {'parts': [{'text': system}]},
              'contents': [{'role': 'user', 'parts': [{'text': prompt[:6000]}]}],
              'generationConfig': config}, timeout=60)
    if response.status_code != 200:
        # Never log request URLs, headers, or raw exceptions with credentials.
        raise RuntimeError(f'Gemini HTTP {response.status_code}; no automatic retry')
    body = response.json()
    usage['reported_tokens'] += body.get('usageMetadata', {}).get('totalTokenCount', 0)
    ledger.write_text(json.dumps(usage))
    candidate = body.get('candidates', [{}])[0]
    if candidate.get('finishReason') != 'STOP':
        raise RuntimeError('Gemini response incomplete or blocked')
    raw = ''.join(p.get('text', '') for p in candidate.get('content', {}).get('parts', [])
                  if not p.get('thought'))
    result = json.loads(raw)
    if not isinstance(result, dict):
        raise RuntimeError('Expected a JSON object')
    cached.write_text(json.dumps(result))
    return result
