from pathlib import Path
import ast,hashlib,json,stat,subprocess
H=Path(__file__).resolve().parent;R=H.parents[5];F=R/'research/onchain-paper-replication-2026-09-24/full_sources';D=F/'real-data-pilot-sixth-graph-ledger-retirement01-2026-10-06';A=F/'real-data-pilot-sixth-graph-retirement-preparation01-2026-10-06';B=R/'research/onchain-paper-replication-2026-09-24/storage/real-pilot-sixth-graph-preservation-20261006-01';ev={}
def raw(p):
 s=p.lstat();assert p.resolve()==p and stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=4*1024**2;b=p.read_bytes();t=p.stat();assert (s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns);ev[str(p.relative_to(R))]=hashlib.sha256(b).hexdigest();return b
def read(p):return json.loads(raw(p))
draft=read(D/'BOUND_RELEASE_DRAFT01.json');assert ev[str((D/'BOUND_RELEASE_DRAFT01.json').relative_to(R))]=='8f9bc3d66df1fcff629df8eab5e57c2f0011d5c689b25501460473ba19a11c1f'
for p,sha in draft['evidence'].items():assert 'connection.json' not in p and hashlib.sha256(raw(R/p)).hexdigest()==sha
source=raw(D/'retire01.py');assert hashlib.sha256(source).hexdigest()==draft['entry_sha256']=='3b394554e1f74b34724c1fb3144c450127ab8ba53f5ba72170555c25f6cedbe4' and source==raw(A/'ledger01.py')
man=read(A/'MANIFEST01.json');assert ev[str((A/'MANIFEST01.json').relative_to(R))]=='d3421b8e5915787311c65f15af4b1a5c37bc2e05fe1fe863b4367b03451fe21f'
for n in ('ledger01.py','INVERSE01.json','CHECK01.json'):assert hashlib.sha256(raw(A/n)).hexdigest()==man[n]
inv=read(A/'INVERSE01.json')['ledger01.py'];base=raw(R/inv['baseline']);assert hashlib.sha256(base).hexdigest()==inv['baseline_sha256'];rev=source.decode()
for p in inv['literal_changes']:assert rev.count(p['new'])==p['count'];rev=rev.replace(p['new'],p['old'])
assert rev.encode()==base and ast.dump(ast.parse(rev))==ast.dump(ast.parse(base))
fn=next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef) and x.name=='execute');predicate=next(x.test for x in fn.body if isinstance(x,ast.If) and 'retire_only_fourth_graph' in ast.unparse(x.test));code=compile(ast.Expression(predicate),'release-predicate','eval');env={'ID':draft['retirement_identity'],'__file__':'fixed-entry','digest':lambda path:draft['entry_sha256']}
try:eval(code,{**env,'review':{**draft,'decision':'accepted'}})
except KeyError as error:assert error.args==('retire_only_fourth_graph_ledger_and_successful_get',)
else:raise AssertionError('draft missing alias did not refuse')
fixed={**draft,'decision':'accepted','retire_only_fourth_graph_ledger_and_successful_get':True};assert eval(code,{**env,'review':fixed}) is False
for key,val in [('retirement_identity','different'),('full_scope_byte_recovery',False),('retire_only_fourth_graph_ledger_and_successful_get',False)]:assert eval(code,{**env,'review':{**fixed,key:val}}) is True
out=read(R/draft['backup_outcome_review']['path']);assert ev[draft['backup_outcome_review']['path']]==draft['backup_outcome_review']['sha256']=='1e76c7a937cc3de2bd04491001ca408f5a09d2209fc3d5ff949bcaa2e93f55ee' and out['full_scope_byte_recovery'] is True and out['decision']=='accepted'
c=read(B/'complete.json');assert raw(B/'complete.json')==raw(B/'recovered-complete.json');s=read(B/'selection01.json');assert c['selection']==s and c['count']==36
row=s['files'][11];kept=read(B/'11-kept.json');assert kept==c['files'][11] and all(kept[k]==v for k,v in row.items())
assert row['bytes']==3099119616 and row['path']==draft['original_ledger_path'] and draft['successful_recovery_path']==str((B/'11-recovered.bin').relative_to(R)) and draft['payload_bytes_to_retire']==6198239232
prior=out['rows'][11];assert prior['path']==row['path'] and prior['sha256']==row['sha256'] and prior['bytes']==row['bytes']
for p,sig,mode in [(R/row['path'],prior['original_stat_identity'],prior['original_mode']),(B/'11-recovered.bin',prior['recovered_stat_identity'],prior['recovered_mode'])]:
 t=p.lstat();assert p.resolve()==p and stat.S_ISREG(t.st_mode) and t.st_nlink==1 and [t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns]==sig and stat.S_IMODE(t.st_mode)==mode
assert not (R/row['path']).with_name('ledger.sqlite.remote.json').exists()
for n in ('attempt01.json','complete01.json','failed01.json','RELEASE_REVIEW01.json'):assert not (D/n).exists() and not (D/n).is_symlink()
g=read(B/'guard01/final.json');rt=read(B/'ROOT_TERMINAL01.json');o=read(B/'outer-exit01.json');assert g['phase']=='complete' and g['child_exit_code']==rt['actual_root_tool_exit_code']==o['entry_selected_exit_code']==0 and g['cleanup_verified'] is True and g['cleanup_stop_returncode']==5 and g['memory_events']['high']==19369
assert not Path(g['cgroup']).exists() and all(not Path('/proc',str(p)).exists() for p in rt['selected_recorded_pids'])
u=subprocess.run(['systemctl','--user','list-units','--state=active,activating','--no-legend','onchain-replication-*.service'],capture_output=True,text=True);assert u.returncode==0 and not u.stdout.strip()
active=[]
for p in (R/'research_runs').glob('*/claim.json'):
 q=json.loads(p.read_bytes())
 if q.get('program_id')=='onchain-paper-replication-2026-09-24' and not any((p.parent/n).exists() for n in ('complete.json','failed.json')):active.append(p.parent.name)
assert not active
result={'decision':'pass-exact-ledger-only-entry','identity':draft['retirement_identity'],'entry_sha256':draft['entry_sha256'],'original_path':row['path'],'recovery_path':draft['successful_recovery_path'],'bytes_to_retire':6198239232,'bounded_evidence_count':len(draft['evidence']),'source_byte_AST_inverse':True,'draft_schema_mismatch':'missing legacy fourth-named boolean; final release adds explicit alias constrained to exact June6 ID/source/row11','alias_refusal_controls':3,'current_original_recovery_stat_joins':True,'active_paper_claims':active,'active_native_rows':0,'payload_reads':0,'evidence':ev}
(H/'CHECK01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence'}))
