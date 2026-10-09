import ast,hashlib,json,os,resource,signal,struct,datetime,stat
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
R=Path.cwd();H=Path(__file__).resolve().parent;F=H.parent;N=F/'real-data-pilot-final23-2026-10-09';evidence={}
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p,pin=None):
 b=p.read_bytes();h=sha(b)
 if pin:assert h==pin
 evidence[str(p.relative_to(R))]=h;return json.loads(b)
refs=load(N/'ALL_INPUT_REFS01.json');draft=load(N/'INPUT_DRAFT02.json');gate=load(N/'gate03.json');ex=gate['experiments']['eth-paper-real-data-end-to-end-resource-20261009-23']
def header(p):
 before=p.lstat();assert stat.S_ISREG(before.st_mode) and p.resolve()==p
 with p.open('rb') as f:
  prefix=f.read(8);assert prefix[:6]==b'\x93NUMPY';major=prefix[6];assert major in (1,2,3);lenraw=f.read(2 if major==1 else 4);length=int.from_bytes(lenraw,'little');assert 0<length<=65536
  body=f.read(length);assert len(body)==length;meta=ast.literal_eval(body.decode('utf-8' if major==3 else 'latin1'));assert set(meta)=={'descr','fortran_order','shape'}
  assert os.fstat(f.fileno())==before
 assert p.lstat()==before
 return {'path':str(p.relative_to(R)),'version':list(prefix[6:]),'header_sha256':sha(prefix+lenraw+body),'header_bytes_read':len(prefix)+len(lenraw)+len(body),'shape':list(meta['shape']),'dtype':meta['descr'],'fortran_order':meta['fortran_order'],'observed_file_bytes':before.st_size,'metadata':{'device':before.st_dev,'inode':before.st_ino,'mtime_ns':before.st_mtime_ns,'ctime_ns':before.st_ctime_ns},'payload_read':False}
dref=refs['original_dictionary'];dictionary=load(R/dref['path'],dref['sha256']);k=len(dictionary['representatives']);assert k==32
rows=[]
for date,row in sorted(draft['graphs'].items()):
 ref=row['manifest'];assert all(refs[row['role']][x]==ref[x] for x in ['path','sha256']);p=R/ref['path'];m=load(p,ref['sha256']);count=load(R/row['node_count']['path'],row['node_count']['sha256']);hs=[]
 for key in ['node_ids','node_features']:
  a=m['arrays'][key];hp=p.parent/a['path'];h=header(hp);assert h['observed_file_bytes']==a['bytes'];h['manifest_declared_full_payload_file_sha256_not_reverified']=a['sha256'];hs.append(h)
 n=hs[0]['shape'][0];assert hs[0]['shape']==[n] and hs[1]['shape'][0]==n==count['rows'];assert count['graph_manifest_sha256']==ref['sha256'] and count['node_features_sha256']==m['arrays']['node_features']['sha256']
 rows.append({'date':date,'nodes':n,'motifs':k,'scalar_comparisons':n*k,'manifest':ref,'headers':hs})
source_paths=['tradingagents/research/onchain_replication/compact_mcm.py','tradingagents/research/onchain_replication/imported_mcm_identity.py','research/onchain-paper-replication-2026-09-24/full_sources/real-data-pilot-capacity-selection02-2026-10-08/imported_kernel.py','tradingagents/research/onchain_replication/real_pilot_partial_progress.py']
for p in source_paths:raw=(R/p).read_bytes();assert sha(raw)==ex['source_files'][p];evidence[p]=sha(raw)
ktext=(R/source_paths[2]).read_text();assert 'for center in range(n):' in ktext and 'for motif,m in enumerate(motifs):' in ktext and 'value=workload.score(score_pair,purpose,local,m)' in ktext and "require(rows==n and cells==n*k,'incomplete MCM output')" in ktext
snapshots=[]
for identity in ['eth-paper-real-data-end-to-end-resource-20261009-23','eth-paper-real-data-end-to-end-resource-20261008-22']:
 p=R/'research_runs'/identity/'artifacts/scoring-diagnostic/progress.json';raw=p.read_bytes();j=json.loads(raw);snapshots.append({'identity':identity,'path':str(p.relative_to(R)),'snapshot_sha256':sha(raw),'sampled_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),**{key:j.get(key) for key in ['source','claim_sha256','completed_scalar_pairs','matching_elapsed_seconds','scope_elapsed_seconds','pairs_per_second','planned_stop_reached','full_mcm_complete','phase_timings','tail_observation']}})
total=sum(r['scalar_comparisons'] for r in rows);sens=[]
for snap in snapshots:
 c=snap['completed_scalar_pairs'];t=snap['matching_elapsed_seconds'];rate=c/t if c and t else None
 if rate:
  sens.append({'identity':snap['identity'],'observed_prefix_pairs':c,'prefix_seconds':t,'conditional_constant_rate_pairs_per_second':rate,'conditional_all_seven_seconds':total/rate,'conditional_all_seven_days':total/rate/86400,'speedup_needed_8h_scoring_only':total/rate/28800,'speedup_needed_24h_scoring_only':total/rate/86400,'speedup_needed_7days_scoring_only':total/rate/(7*86400)})
x={'status':'header-only-conditional-feasibility','identity':'eth-paper-real-data-end-to-end-resource-20261009-23','evidence':evidence,'graphs':rows,'motifs':k,'total_nodes':sum(r['nodes'] for r in rows),'total_scalar_comparisons':total,'snapshots_once':snapshots,'conditional_sensitivities':sens,'required_rate_8h':total/28800,'required_rate_24h':total/86400,'required_rate_7days':total/(7*86400),'cardinality_proof':'Current source uses compact_mcm rows=len(graph.node_ids), motifs=len(representatives), cells=rows*motifs; imported kernel loops center range(n), motif enumerate(motifs), calls workload.score once per cell and requires rows==n and cells==n*k. Fixed diagnostic stops after1024 acknowledgements; it is not complete pilot authority.','qualification':'Authenticated manifest/count/dictionary metadata and current observed NPY headers only. Recorded full-file hashes inherited from manifests; payload bytes not reread or semantically validated. Prefix is ordered, unrepresentative and censored; neighborhood size/edge cost distribution unknown, active snapshot stale until next checkpoint. No unbiased full-run ETA or universal speedup prediction. Phase timings inclusive/overlapping, not summable; graph startup/extraction/archive/model/training and final recovery add costs. Complete seven-MCM policy/reservation is not admitted by this diagnostic. No empirical job, original array payload, test labels, network or live mutation.'}
(H/'EVIDENCE01.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'evidence_sha256':sha((H/'EVIDENCE01.json').read_bytes()),'graphs':[(r['date'],r['nodes'],r['scalar_comparisons']) for r in rows],'total':total,'sensitivities':sens}))
