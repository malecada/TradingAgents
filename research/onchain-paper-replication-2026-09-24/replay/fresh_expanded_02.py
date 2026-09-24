"""Latest frozen synthetic code in the existing clean locked offline environment."""
import sys
from pathlib import Path
import hashlib
import json
import importlib.metadata


def deny(event, args):
    if event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo', 'urllib.Request'):
        raise RuntimeError('offline reproduction denies network')


sys.addaudithook(deny)
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from tradingagents.research.onchain_replication.resources import assert_guarded_worker
assert_guarded_worker(HERE/'fresh-expanded-02-guard', sys.orig_argv, required_paths=[ROOT],
    wall_seconds=1800, memory_max_bytes=2560*1024**2, memory_high_bytes=2*1024**3)
source = json.loads((HERE/'fresh-expanded-02-source.json').read_bytes())
for name, sha in source['files'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != sha:
        raise ValueError('synthetic source freeze differs: '+name)
previous = json.loads((HERE/'fresh-environment-01.json').read_bytes())
installed = {d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
if installed != previous['installed_distributions']:
    raise ValueError('clean locked environment distributions changed')
import torch
torch.set_num_threads(2)
from tradingagents.research.onchain_replication.replay import replay
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.onchain_replication.environment import inventory
result = replay(HERE/'synthetic-01')
result.update(environment=inventory(ROOT, True), interpreter=sys.executable,
    source_freeze_sha256=hashlib.sha256((HERE/'fresh-expanded-02-source.json').read_bytes()).hexdigest(),
    network='main-process audit hook denied before imports; synthetic subprocess fixtures use local repositories only',
    qualification='existing clean locked offline environment reused with exactly unchanged installed distributions; synthetic checkpoint only')
_immutable(HERE/'fresh-expanded-02-replay.json', result)
import pytest
code = pytest.main(['-q', '--import-mode=importlib', '--disable-warnings',
    str(ROOT/'tests/research/onchain_replication'), '--junitxml='+str(HERE/'fresh-expanded-02.xml')])
for name, sha in source['files'].items():
    if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != sha:
        raise ValueError('synthetic source changed during verification: '+name)
raise SystemExit(code)
