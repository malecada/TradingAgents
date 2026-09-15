"""Build one subordinate source-only package from an already admitted claim.

This command cannot admit/start a claim, request market data or launch the VPS.
It refuses an existing destination and binds exact source bytes from claim.source.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tradingagents.research_options_capture import control,worker


def build(*,root,destination,data_root,host_identity,now_utc):
    root=Path(root).resolve();destination=worker.safe(destination)
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():raise ValueError('new absolute release destination required')
    if data_root!='/opt/thesis-research/options-episode-20260911/data':raise ValueError('sole frozen target data root required')
    if host_identity!='pck-preds-1':raise ValueError('only confirmed research host admitted')
    verified=control.verify_episode(root=root,now_utc=now_utc)
    if verified['status']!='active':raise ValueError('active locally verified episode required')
    claim_path=root/'research_runs'/control.TARGET/'claim.json';raw=claim_path.read_bytes();claim=json.loads(raw)
    protocol=claim['episode_protocol'];start=control.utc(protocol['observation_window']['start'])
    if control.utc(now_utc)>=control.utc(protocol['worker_lease']['not_before']):raise ValueError('release prepared before worker lease')
    def ms(value):return int(control.utc(value).timestamp()*1000)
    worker.validate_entry(ms(start.isoformat()))
    sources={}
    for member in sorted(worker.PACKAGE_FILES):
        tracked='scripts/options_release_bootstrap.py' if member=='release_bootstrap.py' else member
        body=subprocess.check_output(['git','show',claim['source']+':'+tracked],cwd=root)
        if (root/tracked).read_bytes()!=body:raise ValueError('source differs from committed claim')
        pin=claim['experiment']['source_files'].get(tracked)
        if tracked.startswith('tradingagents/research_options_capture/'):
            pin=claim['experiment']['runtime_hashes'].get('research_options_capture/'+Path(tracked).name)
        if pin!=hashlib.sha256(body).hexdigest():raise ValueError('release source not pinned by admitted claim')
        sources[member]=body
    assignment={'schema_version':1,'authority':'raw-worker-only','target':control.TARGET,'source_commit':claim['source'],
        'entry_ms':ms(start.isoformat()),'lease_not_before_ms':ms(protocol['worker_lease']['not_before']),'lease_expires_ms':ms(protocol['worker_lease']['expires_at']),
        'claim_path':'claim.json','claim_sha256':hashlib.sha256(raw).hexdigest(),'package_files':{name:hashlib.sha256(body).hexdigest() for name,body in sources.items()},
        'journal_caps':worker.CAPS,'terminal_reserves':worker.RESERVES,'data_root':data_root,'host_identity':host_identity}
    assignment_raw=control.encoded(assignment)
    destination.mkdir(parents=False)
    for name,body in {**sources,'claim.json':raw,'assignment.json':assignment_raw}.items():
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(body);stream.flush();os.fsync(stream.fileno())
        target.chmod(0o444)
    return {'assignment_sha256':hashlib.sha256(assignment_raw).hexdigest(),'bootstrap_sha256':assignment['package_files']['release_bootstrap.py'],
        'claim_sha256':assignment['claim_sha256'],'source_commit':claim['source'],'destination':str(destination),
        'data_root':data_root,'host_identity':host_identity,'status':'prepared; no remote action'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',required=True,type=Path);parser.add_argument('--data-root',required=True)
    parser.add_argument('--now-utc',required=True)
    args=parser.parse_args()
    print(json.dumps(build(root=ROOT,destination=args.destination,data_root=args.data_root,host_identity='pck-preds-1',now_utc=args.now_utc),indent=2))


if __name__=='__main__':main()
