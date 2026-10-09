"""Read-only Root preservation return, separate from the permanently failed Run28.

Uses the existing receive primitive and original public transport identity.
No Run, Owner, numerical execution, remote mutation or credentials inspection.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
from tradingagents.research.onchain_replication import archive_transport as transport

root = Path.cwd()
here = Path(__file__).resolve().parent
original = root / 'research_artifacts/onchain_batched_offload/223798d84810b5f0f49aa89b17b35db96c6ddbcc7c86948472e81ec49573e5d6/mcm-0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba/preserve/00000000/offload.json'
body = original.read_bytes()
body_sha = hashlib.sha256(body).hexdigest()
record = json.loads(body)
connection = {'host': 'u676273.your-storagebox.de', 'user': 'u676273', 'port': 23,
    'identity_file': '/home/malecada/.ssh/id_ed25519_storagebox_u676273',
    'known_hosts_file': '/home/malecada/.ssh/known_hosts_storagebox_u676273'}
identity = hashlib.sha256(json.dumps({'format': 'archive-ssh-transport-v1', 'connection': connection}, sort_keys=True).encode()).hexdigest()
assert identity == record['receipt']['transport_identity']
assert record['manifest']['archive_bytes'] == record['receipt']['bytes'] == 3532800
remote = record['receipt']['remote'] + '/payload.bin'
import re
assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}/payload\.bin', remote)
destination = here / 'original-group-return01.tar'
assert not destination.exists() and not Path(str(destination) + '.transport.json').exists()
resource.setrlimit(resource.RLIMIT_FSIZE, (4*1024**2, 4*1024**2))
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
signal.alarm(75)
def preservation_currentness():
    # Root preservation bounds only; this is explicitly not a ResearchRun lease.
    assert original.read_bytes() == body
    assert shutil.disk_usage(root).free >= 10*1024**3
command = ['ssh', '-p', '23', '-i', connection['identity_file'], '-o', 'IdentitiesOnly=yes',
    '-o', 'BatchMode=yes', '-o', 'UserKnownHostsFile=' + connection['known_hosts_file'],
    '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=15',
    '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2',
    connection['user'] + '@' + connection['host'], 'dd', 'if=' + remote,
    'bs=32768', 'count=' + str(3532800//32768 + 1)]
transport.receive_diagnostic(command, destination, expected_bytes=3532800,
    max_seconds=60, bytes_per_second=4*1024**2, lease_callback=preservation_currentness)
returned = destination.read_bytes()
assert hashlib.sha256(returned).hexdigest() == record['manifest']['archive_sha256']
receipt = {'status': 'actual_read_only_external_return', 'original_offload_path': str(original.relative_to(root)),
    'original_offload_sha256': body_sha, 'transport_identity': identity,
    'remote_member': remote, 'returned_path': str(destination.relative_to(root)),
    'returned_bytes': len(returned), 'returned_sha256': hashlib.sha256(returned).hexdigest(),
    'receiver_source_sha256': hashlib.sha256(Path(transport.__file__).read_bytes()).hexdigest(),
    'qualification': 'Root read-only fresh historical archive preservation return. No original Run reopened, scientific Owner or Binding created, numerical execution, remote writes/deletion, credential contents inspected, member semantics or completed MCM/training asserted.'}
with (here / 'RETURN01.json').open('x') as fp:
    json.dump(receipt, fp, indent=2, sort_keys=True)
    fp.write('\n')
print(json.dumps({'status': receipt['status'], 'bytes': len(returned), 'sha256': receipt['returned_sha256']}))
