from pathlib import Path
import hashlib,json,ast,stat,copy
M=Path.cwd();F=M/'research/onchain-paper-replication-2026-09-24/full_sources';D=Path(__file__).parent;P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-resource-successor-root-launch-20261005-01');R=F/'financial-wrapper-continuation-successor-terminal-remote01-2026-10-05';C=F/'heartbeat-root-checkpoint10-2026-10-04';H=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def ref(p):b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':H(b)}
def put(n,x):p=D/n;assert not p.exists();p.write_text(json.dumps(x,sort_keys=True,indent=2)+'\n');p.chmod(0o444);return ref(p)
r=read(R/'REMOTE_RECOVERY01.json');root=read(R/'ACTUAL_ROOT_EXIT01.json');sel=read(R/'SELECTED_BODIES01.json');assert ref(R/'REMOTE_RECOVERY01.json')['sha256']=='cf8f9f9fc97a59cb41d830798d78cf1c16589ee29e1bed68374527bdc22ccffb';assert ref(R/'ACTUAL_ROOT_EXIT01.json')['sha256']=='b9227a2522145e6e768cd11b84a60c975c677315e253b74f83dc5b3196fbecb7';assert root['actual_root_exit']==0 and root['session_id']==98761 and root['final_chunk']=='447b93'
for n in ['entry','remote_receipt','stdout','stderr']:assert ref(Path(root[n]['path']))==root[n]
assert r['remote_commit']==sel['remote_commit']=='34e8da6656fc0cf7ac28cfe511ec99451f09cadc' and r['selection_sha256']==ref(R/'SELECTED_BODIES01.json')['sha256']
assert len(r['selected_blobs'])==r['selected_count']==8 and r['selected_logical_bytes']==361191
wanted={v['path']:v for v in sel['rows']};bodies={}
for row in r['selected_blobs']:
 b=(R/'selected'/row['path']).read_bytes();assert len(b)==row['bytes']==wanted[row['path']]['bytes'] and H(b)==row['sha256']==wanted[row['path']]['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_object'];assert row['git_mode']=='100644';bodies[row['path']]=b
assert {str(p.relative_to(R/'selected')) for p in (R/'selected').rglob('*') if p.is_file()}==set(wanted)
ops=r['operations'];assert len(ops)==r['expected_operations']==34 and r['unique_selected_objects']==8
expected=['remote','ls-remote','init','remote','config','config','fetch','rev-parse','ls-tree']+['fetch']*8+['cat-file']*16+['ls-remote'];assert [o['operation'] for o in ops]==expected
for o in ops:
 assert o['actual_reaped_exit']==o['exit']==0 and o['cleanup_failures']==[] and o['actual_child_limits']=={'fsize':[4194304,4194304],'pid':o['pid']} and o['seconds']<=60
 assert o['stdout_bytes']<=4194304 and o['stderr_bytes']<=4194304
head=(r['remote_commit']+'\t'+r['branch']+'\n').encode()
for o in [ops[1],ops[-1]]:assert o['stdout_sha256']==H(head) and o['stdout_bytes']==len(head)
assert r['elapsed_seconds']<600 and r['free_bytes']>=10737418240 and r['genuine_run_or_native_started'] is False
policy=r['whole_tree_policy'];rows=[];logical=allocated=0
for p in [R]+list(R.rglob('*')):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode);allocated+=s.st_blocks*512
 if p!=R:rows.append(p)
 if p.is_file():logical+=s.st_size;assert s.st_size<=4194304
assert len(rows)<32768 and logical<67108864 and allocated<100663296
source=C/'SUCCESSOR_TERMINAL_FLAT01.py';baseline=C/'SUCCESSOR_CURRENT_FLAT01.py';assert ref(source)['sha256']=='7f7deed9485368368a19f13ea5dbef4dff614a60f7771350ba5515c390ae3ec4';assert ref(baseline)['sha256']=='710d6bb3d61dd20abdade2de936975fcf4f3c8ce5de3ba5e66fad0eb862ccc5b'
class Inverse(ast.NodeTransformer):
 def visit_Constant(self,n):
  if type(n.value)is str:n.value=n.value.replace('successor-terminal-','successor-current-').replace('actual-terminal-successor','actual-current-successor').replace('34e8da6656fc0cf7ac28cfe511ec99451f09cadc','075361c14c6db16fa78dfb12ded2629de19fa1e4').replace('d26c3af64a99e21162df9effacd9249f749555da059cc19a4e882125810cde17','2ee08c7a2a04041d5b6af306b7f7739f5301fb56b4d008eb1bd43da82ac68a74')
  elif type(n.value)is int:n.value={8:7,34:31,87:506,88:507,848:839,1079:1068,29:12}.get(n.value,n.value)
  return n
assert ast.dump(Inverse().visit(ast.parse(source.read_text())))==ast.dump(ast.parse(baseline.read_text()))
oldentry=read(F/'financial-wrapper-continuation-successor-review01-2026-10-05/CURRENT_FLAT_ENTRY_RELEASE01.json')
for n,h in oldentry['helper_pins'].items():assert ref(P/n)['sha256']==h
out=F/'financial-wrapper-continuation-successor-terminal-flat01-2026-10-05';assert not out.exists()
check={'schema_version':1,'decision':'accepted-actual-terminal-remote-and-literal-flat-source','receiver':ref(R/'REMOTE_RECOVERY01.json'),'actual_root_exit':ref(R/'ACTUAL_ROOT_EXIT01.json'),'selected_count':8,'selected_bytes':361191,'actual_operations':34,'all_reaped_zero':True,'cleanup_failures':[],'independent_sha256_size_git_oid_mode_joins':True,'remote_head_stable':True,'current_whole_tree':{'members':len(rows),'logical_bytes':logical,'allocated_bytes':allocated},'flat_source':ref(source),'flat_baseline':ref(baseline),'flat_ast_exact_inverse_except_approved_literals':True,'historical_body_rescan':False,'archive_flat_recovery_pending':True};print(put('TERMINAL_REMOTE_CHECK01.json',check))
entry=oldentry;entry.update(decision='ACCEPTED_EXACT_ONE_USE_SUCCESSOR_TERMINAL_FLAT',actual_receiver_Root_exit_sha256=ref(R/'ACTUAL_ROOT_EXIT01.json')['sha256'],archive_bodies=88,original_bodies=87,argv=[str(M/'.venv/bin/python'),'-B',str(source)],owned_output_root=str(out),receiver_receipt_sha256=ref(R/'REMOTE_RECOVERY01.json')['sha256'],source_path=str(source),source_sha256=ref(source)['sha256'])
prefix='research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-continuation-successor-terminal-capture01-2026-10-05/'
entry['inputs']={n:{'path':str(R/'selected'/prefix/n),'sha256':H(bodies[prefix+n])} for n in ['CAPTURE01.json','archive-manifest.json','increment.tar.gz']};print(put('TERMINAL_FLAT_ENTRY_RELEASE01.json',entry))
