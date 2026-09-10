"""Read-only VPS metadata probe. Run via SSH stdin; writes nothing remotely.

Never imports the trading application, reads secrets/environment/cron, or calls
an exchange. Journal values are restricted to dates, versions and status.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


def command(argv):
    proc = subprocess.run(argv, text=True, capture_output=True, timeout=20)
    return {'exit_code': proc.returncode, 'output': proc.stdout.strip()}


def metadata(path):
    if not path.is_file():
        return {'exists': False}
    stat = path.stat()
    return {'exists': True, 'bytes': stat.st_size,
            'modified_utc': datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()}


source_names = ['scripts/predlab_s1_paper.py', 'scripts/predlab_s1_live.py',
                'scripts/predlab_journal_backup.sh', 'tradingagents/accounting.py',
                'tradingagents/event_accounting.py', 'tradingagents/predlab/live_exec.py',
                'tradingagents/monitor/predlab.py']
repos = {}
for dirname in ['/opt/tradingagents/predlab', '/opt/tradingagents/repo', '/opt/tradingagents']:
    root = Path(dirname)
    git = command(['git', '-C', dirname, 'rev-parse', '--show-toplevel', 'HEAD'])
    if git['exit_code']:
        repos[dirname] = {'git_checkout': False}
        continue
    code = {}
    for name in source_names:
        path = root / name
        info = metadata(path)
        if info['exists']:
            info['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        code[name] = info
    repos[dirname] = {'git': git, 'source': code}

services = command(['systemctl', 'show', 'ta-monitor.service', 'caddy.service', 'cron.service',
                    'ta-cycle.timer', 'ta-hybrid-cycle.timer',
                    '-p', 'Id', '-p', 'ActiveState', '-p', 'SubState', '-p', 'Result',
                    '-p', 'ExecMainStatus', '-p', 'User', '-p', 'WorkingDirectory'])

base = Path('/opt/tradingagents/predlab-data')
journals = {}
safe = ['asof', 'trade_day', 'written_utc', 'journal_version', 'accounting_version',
        'measurement_status', 'measurement_reason', 'mark_coverage', 'status']
names = {
    's1_paper': ['journal.jsonl', 'journal_champion.jsonl', 'journal_v2.jsonl', 'journal_champion_v2.jsonl'],
    's1_testnet': ['journal_live.jsonl', 'journal_live_v2.jsonl', 'journal_dry_v2.jsonl'],
    's1_live': ['journal_live.jsonl', 'journal_live_v2.jsonl', 'journal_dry_v2.jsonl'],
}
for dirname, filenames in names.items():
    folder = base / 'predlab' / dirname
    for name in filenames:
        path = folder / name
        info = metadata(path)
        if info['exists']:
            rows, malformed, versions, states, last = 0, 0, Counter(), Counter(), None
            with path.open() as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                        if not isinstance(row, dict):
                            raise ValueError()
                    except ValueError:
                        malformed += 1
                        continue
                    rows += 1
                    versions[str(row.get('journal_version', 'legacy'))] += 1
                    states[str(row.get('measurement_status', row.get('status', 'unspecified')))] += 1
                    last = {key: row[key] for key in safe if key in row}
            info.update(rows=rows, malformed=malformed, versions=dict(versions),
                        measurement_states=dict(states), last=last)
        journals[f'{dirname}/{name}'] = info
    if dirname != 's1_paper':
        journals[f'{dirname}/halt.flag'] = {'exists': (folder/'halt.flag').is_file()}

funding_dir = base / 'xsect/funding'
funding_files = sorted(funding_dir.glob('*.parquet')) if funding_dir.is_dir() else []
funding = {'directory_exists': funding_dir.is_dir(), 'parquet_files': len(funding_files)}
if funding_files:
    dates = [p.stat().st_mtime for p in funding_files]
    funding.update(oldest_file_mtime_utc=datetime.fromtimestamp(min(dates), timezone.utc).isoformat(),
                   newest_file_mtime_utc=datetime.fromtimestamp(max(dates), timezone.utc).isoformat(),
                   qualification='File mtime only; event coverage not established')

print(json.dumps({'captured_utc': datetime.now(timezone.utc).isoformat(),
                  'checkouts': repos, 'services': services, 'journals': journals,
                  'funding_store': funding, 'exchange_api_calls': 0, 'remote_mutations': 0}, indent=2))
