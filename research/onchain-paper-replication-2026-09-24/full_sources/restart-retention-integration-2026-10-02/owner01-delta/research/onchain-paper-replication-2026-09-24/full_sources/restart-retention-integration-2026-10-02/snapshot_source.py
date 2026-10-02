"""Copy only explicit source/config/test closure; no jobs or historical outcomes."""
import hashlib
import json
import os
from pathlib import Path
import sys
root=Path.cwd().resolve();base=Path(__file__).resolve().parent;name=sys.argv[1]
assert name.isalnum()
target=base/(name+'-source');target.mkdir()
files={p for folder in ('tradingagents/research','tests/research/onchain_replication') for p in (root/folder).rglob('*.py') if '__pycache__' not in p.parts}
files|=set((root/'tests/research').glob('*.py'))
files|={root/p for p in ('tradingagents/__init__.py','tests/__init__.py','tests/conftest.py','conftest.py','pyproject.toml','uv.lock') if (root/p).is_file()}
study=root/'research/onchain-paper-replication-2026-09-24'
files|=set((study/'full_sources').glob('*/*.py'))
files|=set((study/'config').glob('*.json'))
manifest={}
for path in sorted(files):
 relative=path.relative_to(root);raw=path.read_bytes();destination=target/relative
 destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw);destination.chmod(0o444)
 manifest[str(relative)]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
for relative,record in manifest.items():
 assert hashlib.sha256((root/relative).read_bytes()).hexdigest()==record['sha256'],('source changed during copy',relative)
assert {str(p.relative_to(root)) for p in (root/'tradingagents/research/onchain_replication').glob('*.py')}<=set(manifest)
(base/(name+'-manifest.json')).write_text(json.dumps({'source':str(target),'files':manifest},indent=2,sort_keys=True)+'\n')
print(target,len(manifest))
