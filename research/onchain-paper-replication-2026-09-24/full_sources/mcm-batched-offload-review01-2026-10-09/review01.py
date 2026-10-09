import hashlib,importlib,json,os,resource,sys,types,tarfile
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(268435456,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4194304,)*2)
R=Path.cwd();D=Path(__file__).resolve().parent;C=D.parent/'mcm-batched-offload02-2026-10-09'
m=json.loads((C/'MANIFEST.json').read_text())
for name,pin in m['owned'].items():assert hashlib.sha256((C/name).read_bytes()).hexdigest()==pin
for name,pin in m['baseline'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==pin
package=types.ModuleType('root_offload_changed_seam');package.__path__=[str(C),str(R/'tradingagents/research/onchain_replication')];sys.modules[package.__name__]=package
semantic=importlib.import_module(package.__name__+'.batched_offload_semantics');jmod=importlib.import_module(package.__name__+'.batched_journal');adapter=importlib.import_module(package.__name__+'.registered_offload');policy=importlib.import_module(package.__name__+'.typed_payload_policy')
checks=['all_current_owned_and_baseline_pins']
try:adapter._selected(None,None)
except ValueError:checks.append('no_selection_refused_before_transport')
else:raise AssertionError('unselected source admitted')
j=jmod.BatchJournal(D/'journal',batch_cells=2,max_cells=4,max_bytes=200000,max_body_bytes=8192,boundary=lambda:None)
try:
 for batch in (0,1):
  tasks=iter([({'ordinal':i},None,None) for i in range(batch*2,batch*2+2)])
  j.run_batch_stream(2,tasks,lambda *a:(.125,48,'temperature_complete'),{'engineering':True})
  tokens=bytearray();roster=[]
  for suffix in semantic.SUFFIXES:
   p=j.root/(f'{batch:08d}'+suffix);data,pin=j._read(p.name);tokens.extend(semantic.TOKEN.pack(*pin,len(data),hashlib.sha256(data).digest()));s=p.stat();roster.append({'source_path':str(p),'resolved_path':str(p),'bytes':len(data),'mtime_ns':s.st_mtime_ns,'expected_sha256':hashlib.sha256(data).hexdigest()})
  archive=D/f'bundle{batch}.tar';manifest=semantic.preservation.build_bundle(roster,archive,allowed_roots=[j.root],start_index=batch*3);data=archive.read_bytes()
  evidence=semantic.recover(data,manifest,j,batch,tokens,D/f'recovered{batch}');assert evidence['start']==batch*2 and evidence['stop']==batch*2+2
  assert semantic.current(j,batch,tokens)
  checks.append('actual_semantic_recovery_batch_'+str(batch))
  bad=bytearray(tokens);bad[-1]^=1
  try:semantic.recover(data,manifest,j,batch,bad,D/f'wrong_token{batch}')
  except ValueError:checks.append('wrong_token_refused_'+str(batch))
  else:raise AssertionError('token corruption accepted')
  bad_data=bytearray(data);bad_data[512]^=1
  try:semantic.recover(bytes(bad_data),manifest,j,batch,tokens,D/f'wrong_archive{batch}')
  except (ValueError,tarfile.TarError):checks.append('wrong_archive_refused_'+str(batch))
  else:raise AssertionError('archive corruption accepted')
 # No originals deleted; recovered scratch cleanup is separate.
 assert len(list(j.root.iterdir()))==6
 checks.append('all_generated_original_sources_retained')
finally:j.close()
assert 'numpy' not in sys.modules
x={'status':'PASS','checks':checks,'original_files':6,'arrays_interpreted':False,'transport_executed':False,'retirement_executed':False,'qualification':'source/semantic boundary only; genuine selected Owner/Stage/View and physical budgets remain unexecuted; cannot install or launch from this check alone'}
(D/'RESULT01.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(x))
