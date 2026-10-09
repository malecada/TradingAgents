"""Tiny actual original-journal/bundle group semantics; no genuine transport claim."""
import ast,copy,hashlib,importlib,json,os,types,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[3];S=R/'tradingagents/research/onchain_replication'
pkg=types.ModuleType('group_fixture');pkg.__path__=[str(P),str(S)];sys.modules[pkg.__name__]=pkg
m=importlib.import_module('group_fixture.grouped_offload_semantics');jmod=importlib.import_module('group_fixture.batched_journal');pres=importlib.import_module('group_fixture.preservation')
f=P/'fixtures04';f.mkdir();j=jmod.BatchJournal(f/'matching',batch_cells=2,max_cells=6,max_bytes=65536,max_body_bytes=1024,boundary=lambda:None);items=[];checks=[]
def ck(name,value):assert value,name;checks.append(name)
def refuses(fn):
 try:fn()
 except (ValueError,OSError):return True
 return False
for batch in range(3):
 j.run_batch_stream(2,iter([({'ordinal':2*batch+i},None,None) for i in range(2)]),lambda *args:(.5,1,'iteration_cap'),{'schema_version':2,'cells':6})
 tokens=b''
 for suffix in m.SUFFIXES:
  body,pin=j._read(f'{batch:08d}{suffix}');tokens+=m.TOKEN.pack(*pin,len(body),hashlib.sha256(body).digest())
 items.append((batch,tokens))
items=tuple(items);artifacts=[]
for count in (2,3):
 selected=items[:count];rows=m.source_rows(j,selected);bound=m.archive_bound(rows);archive=f/f'group{count}.tar';manifest=pres.build_bundle(rows,archive,allowed_roots=[j.root],start_index=0)
 ck(f'group{count}_actual_ustar_extent',manifest['archive_bytes']==bound<=m.LIMIT)
 observed=[];evidence=m.recover(archive.read_bytes(),manifest,j,selected,f/f'recovered{count}',consume=lambda batch,rows:observed.extend((row[0],row[1],row[2],row[3],row[4]) for row in rows))
 expected=[row for batch,_ in selected for row in j.read_complete(batch)]
 ck(f'group{count}_exact_records_and_range',observed==expected and evidence['start']==0 and evidence['stop']==2*count and evidence['files']==3*count)
 ck(f'group{count}_binding_roundtrip',m.from_binding(evidence['binding'])==selected)
 artifacts.append((archive,manifest,selected))
archive,manifest,selected=artifacts[-1]
ck('nonconsecutive_refusal',refuses(lambda:m.roster((items[0],items[2]))))
ck('duplicate_refusal',refuses(lambda:m.roster((items[0],items[0]))))
ck('missing_source_batch_refusal',refuses(lambda:m.current(j,((3,items[0][1]),))))
ck('token_extent_refusal',refuses(lambda:m.roster(((0,b'short'),))))
ck('over16_refusal',refuses(lambda:m.roster(tuple((i,items[0][1]) for i in range(17)))))
ck('actual_archive_oversize_refusal',refuses(lambda:m.archive_bound([{'bytes':m.LIMIT}])))
wrong=bytearray(archive.read_bytes());wrong[512]^=1
ck('corrupt_member_refusal',refuses(lambda:m.recover(bytes(wrong),manifest,j,selected,f/'corrupt')))
missing=copy.deepcopy(manifest);missing['members']=missing['members'][:-1];missing['files']-=1
ck('missing_member_refusal',refuses(lambda:m.recover(archive.read_bytes(),missing,j,selected,f/'missing')))
changed=list(selected);b,t=changed[0];bad=bytearray(t);bad[-1]^=1;changed[0]=(b,bytes(bad))
ck('original_token_hash_refusal',refuses(lambda:m.recover(archive.read_bytes(),manifest,j,tuple(changed),f/'wrong-token')))
def mutate_previous(batch,rows):
 if batch==2:
  path=f/'consumer-change/tree/00000000.records.bin';body=bytearray(path.read_bytes());body[-1]^=1;path.write_bytes(body)
ck('earlier_member_mutation_after_callback_refusal',refuses(lambda:m.recover(archive.read_bytes(),manifest,j,selected,f/'consumer-change',consume=mutate_previous)))
ck('original_sources_unchanged',all(hashlib.sha256((j.root/f'{batch:08d}{suffix}').read_bytes()).digest()==m.TOKEN.unpack_from(tokens,index*m.TOKEN.size)[3] for batch,tokens in items for index,suffix in enumerate(m.SUFFIXES)));j.close()
# Check the genuine source seam without constructing Owner/Stage/View capabilities.
tree=ast.parse((P/'typed_payload_operations.py').read_text());method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='retire_batched_group');calls=[ast.unparse(n.func) for n in ast.walk(method) if isinstance(n,ast.Call)]
lines={name:min(n.lineno for n in ast.walk(method) if isinstance(n,ast.Call) and ast.unparse(n.func)==name) for name in ('self.recover','semantic.recover','semantic.current','os.unlink')}
ck('genuine_recover_semantics_current_before_retirement',lines['self.recover']<lines['semantic.recover']<lines['semantic.current']<lines['os.unlink'])
for name in ('grouped_offload.py','grouped_offload_semantics.py','typed_payload_operations.py'):compile((P/name).read_text(),str(P/name),'exec')
ck('no_numerical_imports','numpy' not in sys.modules)
r={'status':'PASS_SEMANTIC_FIXTURES_ONLY','checks':checks,'affinity':sorted(os.sched_getaffinity(0)),'genuine_owner_transport_retirement_executed':False,'all_original_fixture_sources_preserved':True,'archives':[{'batches':len(it),'bytes':ma['archive_bytes'],'members':ma['files']} for ar,ma,it in artifacts]}
(P/'RESULT01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
