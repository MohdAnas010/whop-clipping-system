"""Organic account launch cadence; no fake views, likes, follows or comments.

Target-country reach comes from audience response to actual content. Posting
slots and English content are hypotheses to measure, not a region switch.
"""
from datetime import datetime, timezone

def warm_up(dry_run=True):
    return {'status': 'managed_by_instagram_worker', 'dry_run': dry_run,
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'cadence': '1/day for first 3 days; 2/day through day 7; then 3/day',
        'target_countries': ['US', 'GB', 'CA', 'AU'],
        'synthetic_engagement': False, 'region_guaranteed': False}

def run():
    return warm_up()
