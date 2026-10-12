from pathlib import Path
import json,hashlib,os,stat,struct,math
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');D=F/'real-data-pilot-full39-entry-preparation01-2026-10-12'
sha=lambda b:hashlib.sha256(b).hexdigest()
evidence={};stats={};held={}
def read(p):
 a=p.lstat();assert stat.S_ISREG(a.st_mode) and a.st_size<=262144
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:b=os.read(fd,262145);z=os.fstat(fd)
 finally:os.close(fd)
 assert a==z==p.lstat() and len(b)==a.st_size
 evidence[str(p)]=sha(b);stats[str(p)]={'inode':a.st_ino,'device':a.st_dev,'mode':a.st_mode,'bytes':a.st_size,'mtime_ns':a.st_mtime_ns};held[p]=b
 return b
obs=json.loads(read(D/'FIRST_COMPLETED_BATCHES_OBSERVATION04.json'));priorraw=read(D/'FIRST_COMPLETED_BATCHES_OBSERVATION03.json');prior=json.loads(priorraw)
assert obs['prior_observation_sha256']==sha(priorraw)
assert obs['observer_sha256']==sha(read(D/'observe_prefix_increment01.py'))
stdout=json.loads(read(D/'PREFIX_OBSERVER_RUN01.stdout'));assert stdout['pairs']==40960 and stdout['new_batches']==2
assert read(D/'PREFIX_OBSERVER_RUN01.stderr')==b''
assert obs['previous_hash_joined_pairs']==prior['hash_joined_local_completed_pairs']==32768
assert obs['hash_joined_local_completed_pairs']==40960
assert [x['batch'] for x in obs['new_batches']]==[8,9] and len(obs['sources'])==10
bodies={}
for x in obs['sources']:
 b=read(Path(x['path']));assert len(b)==x['bytes'] and sha(b)==x['sha256'];bodies[x['path']]=b
H=struct.Struct('>8sIQQ32s32s');R=struct.Struct('>Q32sdIB');O=struct.Struct('>BQ');prev=prior['new_batches'][-1];results=[]
for item in obs['new_batches']:
 i=item['batch']; start=item['start'];stop=item['stop'];assert start==prev['stop'] and stop-start==4096
 def get(suffix):
  key=next(k for k in bodies if k.endswith(f'{i:08d}.'+suffix));return key,bodies[key]
 pr,praw=get('pending.json');cr,craw=get('complete.json');xr,xraw=get('prefix.json');rr,raw=get('records.bin')
 p,c,x=map(json.loads,[praw,craw,xraw]);sr=next(k for k in bodies if k.endswith(f'numeric-batches/{i:012d}.json'));sraw=bodies[sr];s=json.loads(sraw)
 assert p['schema']==3 and p['kind']=='engineering_pending' and p['disposition']=='attempted_unknown_without_complete'
 assert p['start']==start and p['stop']==stop and p['workload_sha256']=='21caf839b2b526ca0c270e23aeea4247c1c73853bc666b2922141ebde1c203c5f'.replace('23aee','23ee')
 assert c['schema']==3 and c['kind']=='engineering_complete' and c['pending_sha256']==sha(praw) and c['payload_sha256']==sha(raw) and c['payload_bytes']==len(raw)
 assert c['record_bytes']==R.size and len(raw)==H.size+4096*R.size
 assert H.unpack_from(raw)==(b'MCMBAT03',R.size,start,stop,bytes.fromhex(sha(praw)),bytes.fromhex(c['purposes_sha256']))
 ph=hashlib.sha256()
 for expected,(ordinal,purpose,score,iterations,status) in enumerate(R.iter_unpack(raw[H.size:]),start):
  assert ordinal==expected and math.isfinite(score) and 0<=score<=1 and status in (0,1);ph.update(purpose)
 assert ph.hexdigest()==c['purposes_sha256']
 assert x['batch']==s['batch']==i and x['start']==s['start']==start and x['stop']==s['stop']==stop
 assert x['contract_sha256']=='19a0c30e0001e706e00ccfe1981ad0e09f21decea858114f73b313fdb704d648'
 assert x['score_sha256']==[sha(praw),sha(raw),sha(craw)] and x['summary_sha256']==sha(sraw)
 originpath=Path(sr).parent.parent/'numeric-origins.bin';fd=os.open(originpath,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  a=os.fstat(fd);o=os.pread(fd,4096*9,start*9);again=os.pread(fd,4096*9,start*9);z=os.fstat(fd)
 finally:os.close(fd)
 q=originpath.lstat();assert stat.S_ISREG(a.st_mode) and (a.st_dev,a.st_ino)==(z.st_dev,z.st_ino)==(q.st_dev,q.st_ino) and min(a.st_size,z.st_size)>=9*stop
 assert o==again and len(o)==4096*9 and sha(o)==x['origin_sha256']==s['origin_sha256']
 modes=[0,0]
 for ordinal,(mode,owner) in enumerate(O.iter_unpack(o),start):
  assert mode in (0,1) and (owner==ordinal if mode==0 else owner<ordinal);modes[mode]+=1
 assert modes==[s['computed'],s['reused']]==[item['computed'],item['reused']]
 assert s['phase_totals']['phases']==item['cumulative_phases'] and s['counters']==item['cumulative_counters'] and s['elapsed_seconds']==item['numeric_call_elapsed_seconds']
 assert item['phase_deltas']=={k:{q:v[q]-prev['cumulative_phases'][k][q] for q in v} for k,v in item['cumulative_phases'].items() if k in prev['cumulative_phases']}
 span=(item['prefix_modified_ns']-prev['prefix_modified_ns'])/1e9
 assert item['prefix_modified_ns']==stats[xr]['mtime_ns'] and item['publication_span_seconds']==span and item['publication_pairs_per_second']==4096/span
 results.append({'batch':i,'origin_slice_sha256':sha(o),'origin_observed_inode':a.st_ino,'origin_size_before':a.st_size,'origin_size_after':z.st_size,'computed':modes[0],'reused':modes[1],'source_admission':item['phase_deltas']['source_admission'],'pair_numeric':item['phase_deltas']['pair_numeric'],'publication_pairs_per_second':4096/span,'summary_geometry':s.get('geometry')})
 prev=item
for p,b in list(held.items()):assert read(p)==b
print(json.dumps({'status':'PASS','new_batches':results,'evidence':evidence,'captured_file_stats':stats,'qualifications':'Two batches only. Matching stable reads/inode/stat and repeated origin slices are observations, not atomic writer exclusion or independent numerical agreement.'},indent=2))
