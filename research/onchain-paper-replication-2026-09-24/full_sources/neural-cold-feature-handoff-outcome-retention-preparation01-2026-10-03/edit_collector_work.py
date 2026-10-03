from pathlib import Path
p=Path(__file__).parent/'collector01.py'
s=p.read_text()
pos=s.index('\ndef collect(')
s=s[:pos]+'''
def capture_external(q,directory):
 """Finite referenced metadata closure; never recursively reads arbitrary paths."""
 directory.mkdir(exist_ok=False);pending=[q];seen={};records=[];total=0
 while pending:
  value=pending.pop()
  if type(value)is list:
   require(len(value)<=32768,'metadata list bound');pending.extend(value);continue
  if type(value)is not dict:continue
  if set(value)=={'path','sha256'} and type(value['path'])is str and Path(value['path']).is_absolute():
   key=(value['path'],value['sha256'])
   if key in seen:continue
   require(len(records)<1024,'external metadata reference bound');raw=reference(value);total+=len(raw);require(total<=32*1024**2,'external metadata aggregate bound')
   name=f"reference-{len(records):04d}";source=Path(value['path']);row={'signature':store.sig(source.lstat()),'mode':source.stat().st_mode&0o777,'bytes':len(raw)}
   got=store.copy_file(source,directory/name,row,time.monotonic()+10);require(got==value['sha256'],'external reference changed during copy');seen[key]=name;records.append({'original':value,'retained':name,'sha256':got,'bytes':len(raw)})
   try:decoded=json.loads(raw)
   except (ValueError,UnicodeDecodeError):decoded=None
   if decoded is not None:pending.append(decoded)
  else:pending.extend(value.values())
 store.write(directory,'reference-index.json',{'schema_version':1,'references':records,'scope':'all bounded absolute path/SHA metadata refs recursively reachable from request; complete recovery trees are separately retained inputs, not duplicated here'})
 return records

def failure_observation(phase,error):
 return {'phase':phase,'identity':IDS[phase],'original_lifecycle_observation':'unverified','observation_error_type':type(error).__name__,'original_receipts':None,'registered_outputs':None,'protocol_outputs':OUTPUTS[phase],'present_output_names':None,'absent_registered_outputs':None,'unavailable_registered_output_names':None,'scientific_authentication':None,'wrapper_authentication':None,'cleanup':None,'numerical_results_synthesized':False}
''' +s[pos:]
s=s.replace("release=None if q['releases'][phase] is None else json.loads(reference(q['releases'][phase]));wrapper=None if q['wrappers'][phase] is None else store.direct(q['wrappers'][phase]);value=observed_phase(root,phase,release);outcomes[phase]=value", "release=None;wrapper=None\n   try:\n    release=None if q['releases'][phase] is None else json.loads(reference(q['releases'][phase]));wrapper=None if q['wrappers'][phase] is None else store.direct(q['wrappers'][phase]);value=observed_phase(root,phase,release)\n   except Exception as error:\n    if isinstance(error,(MemoryError,RecursionError)):raise\n    value=failure_observation(phase,error)\n   outcomes[phase]=value")
s=s.replace("copies['capsule']=store.snapshot", "external=capture_external(q,data/'external-evidence');copies['external-evidence']=store.census(data/'external-evidence',32*1024**2,time.monotonic()+120)\n  copies['external-evidence']=[{k:v for k,v in row.items() if k!='signature'}|({'sha256':store.hash_file(data/'external-evidence'/row['path'],row,time.monotonic()+10)} if row['kind']=='file' else {}) for row in copies['external-evidence']]\n  copies['capsule']=store.snapshot")
s=s.replace("'member_pages':indexes", "'member_pages':indexes,'external_evidence_count':len(external)")
p.write_text(s)
