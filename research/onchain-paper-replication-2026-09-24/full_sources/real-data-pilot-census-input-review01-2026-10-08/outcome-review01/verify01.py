import ast,hashlib,json,os,stat,struct
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[4]
A=R/'research_artifacts/onchain-paper-replication-2026-09-24/engineering/eth-seven-graph-weak-one-hop-census-20261008-01'
read=lambda p:json.loads(p.read_bytes())
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
s=read(A/'results/SUMMARY01.json');g=read(A/'guard/final.json');launch=read(A/'launch.json')
inputs=read(H.parent/'CALLER_INPUTS02.json')
assert s['status']=='completed' and len(s['graphs'])==len(inputs)==7
assert s['settings_sha256']=='c256a5812f9164dec41486397a8d99f6ca45bb719d77909ba0742d664372e869'
assert s['caller_sha256']=='ab3aace38ce2713b92f42f7e731bc63c7da2da9d6adb32c121ccf424a47ad8bb'
assert s['inputs_sha256']==digest(H.parent/'CALLER_INPUTS02.json')
assert s['helper_sha256']=='4ee889efc0c70645f28f4188796718e93f588f98c98ae421eb222c7f54206b42'
assert launch['request_sha256']=='7c80faed623a172fe48600d9647d5b5610e2202d0ef45ff49274d8b2e02d99a7'
assert g['phase']=='complete' and g['child_exit_code']==0 and g['cleanup_verified'] and g['limit_reason'] is None
assert g['kernel_controls']=={'memory.high':'1073741824','memory.max':'1073741824','memory.swap.max':'0'}
assert all(v==0 for v in g['memory_events'].values())
assert g['native_unit_limits']=={'file_size_bytes':4194304}
assert g['wall_seconds']==600 and g['reserve_bytes']==g['start_reserve_bytes']==2684354560
assert g['cwd']==str(A) and g['storage_budget']['root']==str(A) and g['cpus']==[0,1]
assert s['input_list_after']['sha256']==s['inputs_sha256']
rows=[];chunkcount=0;allcount=0;selected=set()
for i,(v,inp) in enumerate(zip(s['graphs'],inputs)):
 assert v==read(A/f'results/graph-{i:02d}/RESULT01.json')
 assert v['status']=='completed' and v['graph_hash']==inp['graph_hash'] and v['week']==inp['week']
 assert v['node_count']==inp['node_count'] and v['edge_count']==inp['edge_index']['shape'][1]
 assert v['inputs_before']==v['inputs_after']
 for name,key in [('manifest','manifest'),('node_count','node_count_reference'),('edge_index','edge_index')]:assert v['inputs_before'][name]['sha256']==inp[key]['sha256']
 cursor=0;low=2**63;high=-1;first=None;above=0;checks={r['center_index']:r for r in v['independent_center_checks']}
 assert set(checks)=={0,v['maximum_center_index']}
 for c in v['chunks']:
  assert c['start_center']==cursor and cursor<c['stop_center']<=inp['node_count']
  p=A/'results'/c['path'];assert p.resolve().is_relative_to(A/'results') and not p.is_symlink()
  assert p.stat().st_size==c['bytes']<=4194304 and digest(p)==c['sha256'];selected.add(str(p.relative_to(A)))
  with p.open('rb') as f:
   magic=f.read(8);assert magic==b'\x93NUMPY\x01\x00';n=int.from_bytes(f.read(2),'little');assert n<=4096
   h=ast.literal_eval(f.read(n).decode('latin1'));assert h=={'descr':'<i8','fortran_order':False,'shape':(c['stop_center']-cursor,)}
   assert 10+n+8*h['shape'][0]==c['bytes']
   while block:=f.read(65536):
    assert len(block)%8==0
    for (value,) in struct.iter_unpack('<q',block):
     assert 1<=value<=inp['node_count'];low=min(low,value)
     if value>high:high=value;first=cursor
     above+=value>10000
     if cursor in checks:assert value==checks[cursor]['returned_cardinality']==checks[cursor]['independent_cardinality']
     cursor+=1
  assert cursor==c['stop_center'];chunkcount+=1
 assert cursor==inp['node_count'] and (low,high,first,above)==(v['minimum_cardinality'],v['maximum_cardinality'],v['maximum_center_index'],v['centers_above_declared_threshold'])
 assert v['declared_threshold']==10000
 rows.append({'week':v['week'],'graph_hash':v['graph_hash'],'counts':cursor,'minimum':low,'maximum':high,'first_maximum_center':first,'above10000':above});allcount+=cursor
assert chunkcount==54 and allcount==12999004
assert selected=={str(p.relative_to(A)) for p in A.rglob('*.npy')}
entries=[]
for p in [A]+sorted(A.rglob('*')):
 st=p.lstat();assert not stat.S_ISLNK(st.st_mode)
 e={'path':'.' if p==A else str(p.relative_to(A)),'mode':stat.S_IMODE(st.st_mode)}
 if stat.S_ISDIR(st.st_mode):e['type']='directory'
 else:
  assert stat.S_ISREG(st.st_mode) and st.st_nlink==1;e.update(type='file',bytes=st.st_size,sha256=digest(p))
 entries.append(e)
selection={'scope':'entire actual owned root only, no historical/input copies','root':str(A.relative_to(R)),'entries':entries}
(H/'SELECTION01.json').write_text(json.dumps(selection,indent=2)+'\n')
result={'status':'PASS','verified_count_chunks':chunkcount,'verified_integer_counts':allcount,'graphs':rows,'original_root_terminal':'Root-reported87630 exit0 chunk2bce77; independent terminal-process receipt pending','native_phase':g['phase'],'native_child_exit':g['child_exit_code'],'native_cleanup_verified':g['cleanup_verified'],'native_elapsed_seconds':g['elapsed_seconds'],'source_commit':launch['source_commit'],'request_sha256':launch['request_sha256'],'scope':'result vectors only, streaming int64; original edge/ID/feature/label payloads not read','qualification':'No financial/MCM capacity/completion or writer-exclusion credit; pilot19 remains FAILED'}
(H/'CHECKS01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
