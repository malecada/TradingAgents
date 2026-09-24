"""Fresh locked interpreter checks with explicit network denial."""
from pathlib import Path
import json
import sys
import platform
import importlib.metadata

def deny(event,args):
    if event in ('socket.connect','socket.connect_ex','socket.getaddrinfo','urllib.Request'):raise RuntimeError('offline reproduction denies network')
sys.addaudithook(deny)
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import torch
from tradingagents.research.onchain_replication.replay import replay
from tradingagents.research.onchain_replication.environment import inventory
from tradingagents.research.lifecycle import _immutable
torch.set_num_threads(2)
result=replay(Path(__file__).resolve().parent/'synthetic-01')
result.update(environment=inventory(ROOT,True),interpreter=sys.executable,network='denied by audit hook before neural imports',setup_command='UV_PROJECT_ENVIRONMENT=/tmp/onchain-paper-replay-env-20260924-01 uv sync --locked --all-extras --offline --no-install-project --python 3.13.13',installed_distributions={d.metadata['Name']:d.version for d in importlib.metadata.distributions()})
_immutable(Path(__file__).resolve().parent/'fresh-environment-01.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('installed_distributions','environment')},sort_keys=True))
