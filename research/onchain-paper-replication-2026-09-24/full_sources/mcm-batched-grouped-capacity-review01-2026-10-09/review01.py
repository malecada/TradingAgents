import json,pathlib,hashlib,resource,signal,os
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);signal.alarm(30);os.nice(10);os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
R=pathlib.Path(__file__).resolve().parent;F=R.parent;ROOT=pathlib.Path.cwd()
j=lambda p:json.loads(pathlib.Path(p).read_bytes());h=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
d=[];pins={};historical=[]
for i in (1,2,3):
 c=F/f'mcm-batched-grouped-capacity{i:02d}-2026-10-09';m=j(c/'MANIFEST01.json')
 for n,v in m.items():assert h(c/n)==v,(i,n)
 x=j(c/'CAPACITY01.json');d.append(x);pins[str(c.relative_to(ROOT)/'MANIFEST01.json')]=h(c/'MANIFEST01.json')
 for n,v in x['source_pins'].items():
  p=pathlib.Path(n);p=p if p.is_absolute() else ROOT/p
  assert h(p)==v,n
  pins[n]=v
x,y,z=d
assert len(x['graphs'])==7
assert sum(g['rows'] for g in x['graphs'].values())==12999004
assert sum(g['cells'] for g in x['graphs'].values())==415968128
for g in x['graphs'].values():
 assert g['cells']==32*g['rows'];assert g['batches']==(g['cells']+4095)//4096
 assert g['groups']==(g['batches']+15)//16
 assert g['typed_operations']==2*g['groups'] and g['typed_chunks']==3*g['groups']
assert sum(g['groups'] for g in x['graphs'].values())==6352
assert sum(g['batches'] for g in x['graphs'].values())==101559
assert sum(g['policy_commands'] for g in x['graphs'].values())==76224
assert z['sidecar_files']==sum(r['count'] for r in z['sidecar_roster'])==62
assert z['sidecar_logical_upper']==sum(r['count']*r['max_body_bytes'] for r in z['sidecar_roster'])==1089536
q=z['joined'];p=y['physical_join'];res=z['training_lifecycle_residual']
assert q['whole_logical_source_upper']==p['whole_writer_logical']-67108864+1089536+res['growth_logical']==15487371577
inc=p['increment_allocated']-p['conditional_directory_allowance']-67108864+1089536+62*4095+res['growth_allocated']
assert inc==q['non_directory_increment_allocated_upper']==10330149469
assert q['non_directory_whole_allocated_upper']==p['baseline_allocated']+inc==15479456349
assert q['fixed_allocated_cap']==20*1024**3 and q['fixed_logical_cap']==16*1024**3 and q['floor_bytes']==10*1024**3
assert q['directory_plus_unmodeled_concurrent_writer_remaining_bytes']==min(20*1024**3-q['non_directory_whole_allocated_upper'],p['baseline_filesystem_free']-10*1024**3-inc)==3711618467
ck=F/'mcm-batched-checkpoint-reconciliation-review01-2026-10-09/SOURCE_REVIEW01.json';assert h(ck)==z['checkpoint_review_sha256'] and j(ck)['decision']=='accepted'
assert z['checkpoint_contribution']==273838080 and z['cumulative_checkpoint_allowance_unchanged']==43058298880
out={'decision':'accepted_conditional_source_reconciliation','source_evidence':pins,'independent_checks':{'seven_graph_rows':12999004,'cells':415968128,'batches':101559,'groups':6352,'policy_commands':76224,'named_sidecar_files':62,'named_sidecar_logical_upper':1089536,'whole_logical_forecast':15487371577,'non_directory_whole_allocated_forecast':15479456349,'recorded_sample_remaining_budget':3711618467,'fixed_logical_cap':17179869184,'fixed_allocated_cap':21474836480,'filesystem_floor':10737418240},'source_path_findings':['Schema6 compact producer uses typed grouped offload; local output schema1 routes publication to output.publish without storage_policy.','original_import_stage.complete_import materializes original dictionary in memory; archive attachment births genuine ledger metadata but does not invoke old dictionary writer/read/seal operations.','Named sidecars conservatively include producer success and failure, stage/publication records and fixed ledger failure headroom; selected-route success forecast does not guarantee every possible failure trace fits forecast.','WritableUnion and StorageWatch count regular-file and directory st_blocks*512 and refuse observed aggregate breaches; native guard samples filesystem free space. No hard quota or writer exclusion is claimed.'],'entry_facts_still_required':['Fresh baseline and filesystem-free observation, competing-writer activity/reservations and remaining headroom under unchanged caps/floor.','Actual complete selected source/input closure: schema6 fixed16 groups,4096 cells,1024 journal bodies,local output1,no legacy extra operations or prefix diagnostics.','Actual safe ASCII generated and root paths<=512 bytes,input names<=128 bytes,int63 fields; control record cap16384 and unchanged diagnostic cap2048.','Whole selected local and remote logical reservations, RAM constraints, guard wiring and scan limits must be joined to concrete entry.'],'qualification':'Conditional source forecast plus existing sampled enforcement can support a separately reviewed guarded resource measurement; universal static future success/capacity proof is not asserted or required by this review. Current entry eligibility, release and execution remain ungranted. No arrays, transport or authority created.'}
(R/'SOURCE_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'decision':out['decision'],'sha256':h(R/'SOURCE_REVIEW01.json'),'source_pins':len(pins)}))
