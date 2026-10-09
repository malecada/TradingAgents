import ast, hashlib, json, pathlib, resource, signal, os
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2)
resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2)
signal.alarm(30);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
R=pathlib.Path(__file__).resolve().parent
F=R.parent; C=F/'mcm-batched-checkpoint-reconciliation01-2026-10-09'
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
j=lambda p:json.loads(pathlib.Path(p).read_text())
m=j(C/'MANIFEST01.json');r=j(C/'RESULT01.json')
for p,h in m['files'].items():assert sha(C/p)==h,p
for p,h in r['source_pins'].items():assert sha(p)==h,p
pair=j(F/'real-data-pilot-final23-2026-10-09/templates02/pair_policy01.json')
compact=j(F/'real-data-pilot-capacity-selection03-2026-10-08/compact_policy.json')
assert compact['stage_policy']['pair']==pair['limits']
p=pair['limits'];s=compact['stage_policy']['schedule'];assert s==r['schedule']
assert s['max_checkpoints']==p['max_publications']==1
N=p['max_pair_entries_override'];c=p['checkpoint_layout']['chunk_entries']
assert N==8402640 and c==262144
sizes=[8*min(c,N-i)+128 for i in range(0,N,c)]
A=sum(sizes);snapshot=4*A+3*65536
assert len(sizes)==33 and snapshot==p['max_checkpoint_bytes']==269097984
round4=lambda n:((n+4095)//4096)*4096
allocated=4*sum(map(round4,sizes))+3*round4(65536)+round4(8192)+3*4096
assert allocated==269635584
assert allocated+8192+4*1024**2==273838080
assert snapshot+8192==269106176 and 4*len(sizes)+3+1==136
assert s['max_total_checkpoints']==160
assert (snapshot+2*8192)*160==s['max_total_checkpoint_bytes']==43058298880
# Read actual AST, without imports or numerical arrays; require terminal raise after outer loop.
P=pathlib.Path(next(p for p in r['source_pins'] if p.endswith('/batched_pair_executor.py')))
t=ast.parse(P.read_text());cl=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='PairExecutor')
call=next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='__call__')
tr=next(n for n in call.body if isinstance(n,ast.Try));loop=next(n for n in tr.body if isinstance(n,ast.For))
assert ast.unparse(loop.iter)=="range(self.schedule['max_checkpoints'])"
assert isinstance(tr.body[tr.body.index(loop)+1],ast.Raise)
assert ast.unparse(tr.body[tr.body.index(loop)+1].exc).startswith('CheckpointStop(')
assert len([n for n in ast.walk(call) if isinstance(n,ast.Call) and ast.unparse(n.func)=='self.checkpoint'])==1
out={'decision':'accepted','scope':'source-derived conditional single fatal snapshot contribution only','candidate_manifest_sha256':sha(C/'MANIFEST01.json'),'candidate_result_sha256':sha(C/'RESULT01.json'),'source_pins':r['source_pins'],'independent_checks':{'all_candidate_and_source_pins':True,'pair_compact_schedule_join':True,'single_callback_loop_terminal_raise':True,'independent_per_file_rounding':True,'snapshot_body':snapshot,'snapshot_sidecar':snapshot+8192,'files':136,'snapshot_directories':3,'conditional4096_allocation':allocated,'plus_failure_and_training':allocated+8192+4*1024**2,'logical_cumulative_allowance_unchanged':43058298880},'reused_control_tests':{'path':str(C/'TEST01.log'),'sha256':sha(C/'TEST01.log'),'cases':4,'rerun':False},'qualifications':['No numerical arrays, snapshot save or genuine pilot execution performed.','Ordinary frozen runtime and exact selected max_checkpoints=1/layout/limits required; future entry must join these values.','4096-byte rounding and three 4096-byte directory contributions are conditional, not a filesystem allocation measurement. Seven checkpoint parent directories and filesystem metadata remain separate.','Partial failure retains a prefix of one exclusive snapshot namespace; no disk staging copy or retry in inspected save path.','No full-job capacity, zero-checkpoint assumption, launch admission or source-context record-cap acceptance. Separate policy16384/capacity02 remains outside this review.']}
(R/'SOURCE_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'decision':out['decision'],'receipt_sha256':sha(R/'SOURCE_REVIEW01.json'),'source_pins_checked':len(r['source_pins']),'bound':allocated+8192+4*1024**2}))
