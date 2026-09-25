"""Finite continuation03: reuses verified pilot02 and never relaunches parents."""
from pathlib import Path
import fcntl
import gzip
import hashlib
import json
import re
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tradingagents.research.lifecycle import _immutable
from tradingagents.research.onchain_replication.preservation import plan_batches,sha256,transfer_bundle,receive_bounded
from tradingagents.research.onchain_replication.resources import guarded_run,assert_guarded_worker
from tradingagents.research.onchain_replication.provenance import sync_directory
GIB=1024**3


def load_contract():
    raw=(HERE/'contract.json').read_bytes();c=json.loads(raw)
    for name,wanted in c['source_sha256'].items():
        if sha256(ROOT/name)!=wanted:raise ValueError('frozen source changed: '+name)
    for name,wanted in c['input_sha256'].items():
        if sha256(ROOT/name)!=wanted:raise ValueError('frozen input changed: '+name)
    connection_bytes=(ROOT/c['connection_path']).read_bytes()
    if hashlib.sha256(connection_bytes).hexdigest()!=c['input_sha256'][c['connection_path']]:
        raise ValueError('connection identity changed')
    return c,hashlib.sha256(raw).hexdigest(),json.loads(connection_bytes)


def reused_pilot(c):
    reuse=c['reused_pilot']
    records=[]
    for key in ('complete_path','guard_path'):
        name=reuse[key];raw=(ROOT/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=c['input_sha256'][name]:
            raise ValueError('reused pilot evidence changed')
        records.append(json.loads(raw))
    pilot,guard=records
    if (pilot['status']!='complete' or pilot['contract_sha256']!=reuse['contract_sha256']
            or pilot['files']!=reuse['files'] or pilot['raw_bytes']!=reuse['raw_bytes']
            or [b['index'] for b in pilot['batches']]!=[0]
            or guard['phase']!='complete' or not guard['cleanup_verified']
            or guard['child_exit_code']!=0):
        raise ValueError('reused pilot completion or cleanup differs')
    return pilot


class Transport:
    def __init__(self,connection,rate,maximum_payload_bytes):
        self.rate_bytes=rate*1024//8
        self.remaining=maximum_payload_bytes
        self.sizes={}
        key=connection['public_key_path'].removesuffix('.pub')
        known=str(Path(key).parent/('known_hosts_storagebox_'+connection['user']))
        self.host=connection['user']+'@'+connection['host']
        opts=['-i',key,'-o','IdentitiesOnly=yes','-o','BatchMode=yes',
              '-o','UserKnownHostsFile='+known,'-o','StrictHostKeyChecking=yes',
              '-o','ConnectTimeout=15','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2']
        self.ssh=['ssh','-p',str(connection['port']),*opts,self.host]
        self.scp=['scp','-q','-l',str(rate),'-P',str(connection['port']),*opts]
    def run(self,args):
        # No retries; errors retain the partial remote object under its identity.
        return subprocess.run(args,check=True,capture_output=True,timeout=1800)
    def remote_path(self,path):
        if not re.fullmatch('[a-zA-Z0-9_./-]+',path) or '..' in Path(path).parts or path.startswith('/'):
            raise ValueError('unsafe remote path')
        return path
    def mkdir(self,path):self.run([*self.ssh,'mkdir',self.remote_path(path)])
    def reserve(self,size):
        if size>self.remaining:raise RuntimeError('network payload budget exhausted')
        self.remaining-=size
    def put(self,source,path):
        size=Path(source).stat().st_size;self.reserve(size)
        self.run([*self.scp,str(source),self.host+':'+self.remote_path(path)])
        self.sizes[path]=size
    def get(self,path,destination):
        if Path(destination).exists():raise FileExistsError(destination)
        size=self.sizes[path]
        count=size//32768+1
        self.reserve(count*32768)
        receive_bounded([*self.ssh,'dd','if='+self.remote_path(path),'bs=32768','count='+str(count)],
                        destination,expected_bytes=size,max_seconds=1800,bytes_per_second=self.rate_bytes)
    def available(self):
        lines=self.run([*self.ssh,'df','-k']).stdout.decode().splitlines()
        if len(lines)!=2:raise ValueError('unexpected remote capacity response')
        return int(lines[1].split()[3])*1024


def roundtrip(transport,source,remote,destination):
    before=sha256(source)
    transport.put(source,remote);transport.get(remote,destination)
    if sha256(destination)!=before or sha256(source)!=before:raise ValueError('metadata round-trip mismatch')


def worker(phase):
    c,contract_hash,connection=load_contract()
    pc=c['phases'][phase];work=HERE/phase
    assert_guarded_worker(work/'guard',sys.orig_argv,required_paths=[ROOT],wall_seconds=pc['wall_seconds'],
                          memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2)
    _immutable(work/'intent.json',{'phase':phase,'contract_sha256':contract_hash,
          'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'start_batch':pc['start'],'stop_batch':pc['stop'],'no_financial_computation':True})
    started=time.monotonic()
    try:
        inventory_bytes=(ROOT/c['inventory_path']).read_bytes()
        if hashlib.sha256(inventory_bytes).hexdigest()!=c['input_sha256'][c['inventory_path']]:raise ValueError('inventory changed')
        inventory=json.loads(gzip.decompress(inventory_bytes))
        rows=inventory['files']
        batches=plan_batches(rows,max_raw_bytes=c['maximum_batch_raw_bytes'],max_members=c['maximum_batch_members'])
        batch_bytes=(HERE/'batches.json').read_bytes()
        if hashlib.sha256(batch_bytes).hexdigest()!=c['input_sha256'][str((HERE/'batches.json').relative_to(ROOT))]:raise ValueError('batch plan changed')
        expected=json.loads(batch_bytes)
        if batches!=expected:raise ValueError('batch plan differs')
        if len(rows)!=c['expected_files'] or sum(b['raw_bytes'] for b in batches)!=c['expected_raw_bytes']:
            raise ValueError('inventory denominator differs')
        reused_pilot(c)
        release=json.loads((HERE/'BULK_RELEASE.json').read_bytes())
        if (release['contract_sha256']!=contract_hash or release['status']!='released'
                or release['pilot_complete_sha256']!=sha256(ROOT/c['reused_pilot']['complete_path'])):
            raise ValueError('bulk release missing or mismatched')
        transport=Transport(connection,c['scp_kbit_per_second'],pc['maximum_network_payload_bytes'])
        free=transport.available()
        phase_raw=sum(b['raw_bytes'] for b in batches[pc['start']:pc['stop']])
        occupancy=phase_raw+GIB  # conservative bound for tar padding and all phase metadata
        if free<c['remote_free_floor_bytes']+occupancy:raise RuntimeError('remote capacity cannot retain floor after planned uploads')
        if phase=='bulk01':transport.mkdir(c['remote_parent'])
        remote=c['remote_parent']+'/'+phase
        transport.mkdir(remote)
        _immutable(work/'capacity.json',{'available_bytes':free,'floor_bytes':c['remote_free_floor_bytes'],'reserved_upload_bytes':occupancy})
        # Store the full inventory and contract with each phase for standalone recovery.
        for source,name in [(ROOT/c['inventory_path'],'inventory.json.gz'),(HERE/'contract.json','contract.json'),(HERE/'batches.json','batches.json')]:
            roundtrip(transport,source,remote+'/'+name,work/('recovered-'+name))
        complete=[]
        for batch in batches[pc['start']:pc['stop']]:
            index=batch['index'];bwork=work/f'batch-{index:04d}'
            result=transfer_bundle(rows[batch['start']:batch['stop']],bwork,
                   remote=remote+f'/batch-{index:04d}',transport=transport,
                   allowed_roots=c['allowed_source_roots'],start_index=batch['start'])
            complete.append({'index':index,'receipt_sha256':sha256(bwork/'complete.json'),**result})
            if (bwork/'bundle.tar').exists() or (bwork/'recovered.tar').exists():
                raise RuntimeError('verified temporary copies retained; stop before more disk use')
            progress={'phase':phase,'completed_batches':len(complete),'planned_batches':pc['stop']-pc['start'],
                      'files':sum(x['files'] for x in complete),'raw_bytes':sum(x['raw_bytes'] for x in complete),
                      'elapsed_seconds':time.monotonic()-started}
            print(json.dumps(progress),flush=True)
        result={'status':'complete','phase':phase,'contract_sha256':contract_hash,'batches':complete,
                'files':sum(x['files'] for x in complete),'raw_bytes':sum(x['raw_bytes'] for x in complete),
                'elapsed_seconds':time.monotonic()-started,'originals_preserved':True,
                'scope':'retained ETH transaction bytes only; graph/MCM/scratch artifacts excluded'}
        _immutable(work/'completion-payload.json',result)
        roundtrip(transport,work/'completion-payload.json',remote+'/complete.json',work/'recovered-complete.json')
        _immutable(work/'complete.json',result)
    except BaseException as error:
        _immutable(work/'failed.json',{'status':'failed','phase':phase,'error_type':type(error).__name__,
                                      'retry':False,'partial_outputs_preserved':True})
        raise


def run_phase(phase,c,remaining):
    work=HERE/phase;work.mkdir(exist_ok=False);sync_directory(HERE)
    result=guarded_run([str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__).resolve()),'--worker',phase],
        cwd=ROOT,receipt_dir=work/'guard',memory_max_bytes=256*1024**2,memory_high_bytes=192*1024**2,
        memory_swap_max_bytes=0,reserve_bytes=3*GIB,start_reserve_bytes=4*GIB,
        disk_paths=[ROOT],disk_floor_bytes=20*GIB,wall_seconds=min(c['phases'][phase]['wall_seconds'],remaining))
    if result['phase']!='complete' and not (work/'failed.json').exists() and not (work/'complete.json').exists():
        _immutable(work/'failed.json',{'status':'failed','phase':phase,'reason':'guard terminated or refused worker',
            'guard_reason':result.get('limit_reason'),'partial_outputs_preserved':True,'retry':False})
    print(json.dumps({'transfer_phase':phase,**{k:result.get(k) for k in
        ('phase','child_exit_code','cleanup_verified','elapsed_seconds','peak_sampled_memory_current_bytes')}}),flush=True)
    return result['phase']=='complete' and result['child_exit_code']==0 and result['cleanup_verified']


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--worker':worker(sys.argv[2]);raise SystemExit(0)
    if len(sys.argv)!=2 or sys.argv[1]!='all-bulk':raise ValueError('only all-bulk continuation allowed')
    mode=sys.argv[1];c,ch,_=load_contract()
    with (HERE/'controller.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        reused_pilot(c)
        release=json.loads((HERE/'BULK_RELEASE.json').read_bytes())
        if (release['status']!='released' or release['contract_sha256']!=ch
                or release['pilot_complete_sha256']!=sha256(ROOT/c['reused_pilot']['complete_path'])):
            raise ValueError('exact measured-pilot bulk release required')
        controller=HERE/'bulk-controller';controller.mkdir(exist_ok=False);sync_directory(HERE)
        phases=[name for name in c['phases'] if name!='pilot'];completed=[]
        _immutable(controller/'intent.json',{'contract_sha256':ch,'release_sha256':sha256(HERE/'BULK_RELEASE.json'),
                   'phases':phases,'maximum_wall_seconds':c['bulk_cumulative_wall_seconds']})
        began=time.monotonic()
        try:
            for phase in phases:
                remaining=c['bulk_cumulative_wall_seconds']-(time.monotonic()-began)
                if remaining<=0:raise RuntimeError('cumulative bulk wall limit exceeded')
                if not run_phase(phase,c,remaining):raise RuntimeError('phase did not complete: '+phase)
                completed.append(phase)
            records=[reused_pilot(c),*[json.loads((HERE/name/'complete.json').read_bytes()) for name in phases]]
            total_files=sum(r['files'] for r in records);total_bytes=sum(r['raw_bytes'] for r in records)
            if total_files!=c['expected_files'] or total_bytes!=c['expected_raw_bytes']:raise ValueError('total preservation denominator differs')
            _immutable(controller/'complete.json',{'status':'complete','phases':completed,'files_including_pilot':total_files,
                'raw_bytes_including_pilot':total_bytes,'elapsed_seconds':time.monotonic()-began,
                'scope':c['scope'],'originals_preserved':True})
        except BaseException as error:
            _immutable(controller/'failed.json',{'status':'failed','error_type':type(error).__name__,
                'completed_phases':completed,'pending_or_failed_phases':[p for p in phases if p not in completed],
                'retry':False,'partial_outputs_preserved':True})
            raise
