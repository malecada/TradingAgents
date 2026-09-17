"""Independent recovery accounting on top of the existing independent raw check."""
import json
from pathlib import Path

from check_bulk import check_day as check_raw
from check_capture import digest, require


def check_day(root, date, cell):
    result = check_raw(root, date, cell)
    own = Path(root)/'research/onchain-graph-2026-09-16/comparison'
    cohort = json.loads((own/'recovery-cohort.json').read_bytes())
    require(date in cohort['dates'], 'recovery date outside fixed missing cohort')
    prefix = cohort['prefixes'].get(date)
    reused = cell['reused_requests']
    reused_bytes = 0
    if reused:
        require(prefix is not None and reused == prefix['receipt_count'], 'replayed prefix denominator')
        for entry in prefix['files']:
            path = own/'bulk-artifacts'/date/entry['path']
            raw = path.read_bytes()
            require(len(raw) == entry['bytes'] and digest(raw) == entry['sha256'], 'copied original bytes changed')
            if entry['path'].endswith('.json') and not entry['path'].endswith('-intent.json'):
                record = json.loads(raw)
                require(not record.get('error'), 'failed source response reused')
                reused_bytes += record['bytes']
    elif cell['status'] == 'complete':
        require(prefix is None, 'complete day omitted its existing prefix')
    require(cell['reused_received_bytes'] == reused_bytes, 'reused byte denominator')
    require(cell['logical_requests'] == cell['requests'], 'logical request denominator')
    require(cell['logical_received_bytes'] == cell['received_bytes'], 'logical byte denominator')
    require(cell['actual_network_requests'] == cell['requests']-reused, 'new network request denominator')
    require(cell['actual_network_received_bytes'] == cell['received_bytes']-reused_bytes, 'new network byte denominator')
    result.update(reused_requests=reused, actual_network_requests=cell['actual_network_requests'],
                  actual_network_received_bytes=cell['actual_network_received_bytes'])
    return result
