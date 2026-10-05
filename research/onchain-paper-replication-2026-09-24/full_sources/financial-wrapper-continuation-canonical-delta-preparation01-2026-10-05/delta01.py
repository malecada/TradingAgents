"""Two-body/six-object incremental materialization. Root alone invokes after exact review."""
import argparse,copy,hashlib,json,os,stat
from pathlib import Path
import bind03 as B
import recovery_pax01 as R
H=Path(__file__).resolve().parent;F=H.parent;CAP=B.CAP
OLD='664e2ca5fa11d6640ab79f64c5aa222aeb3a9128';SOURCE='d4c81c0961342bfe4c5771aabbef1d46a14cffb8'
PARENT=CAP.parent.parent/'genuine-financial-wrapper-continue100-canonical-plan-root-launch-20261005-01'
OUTPUT=F/'financial-wrapper-continuation-canonical-delta-root01-2026-10-05'
CHANGED={'fixture_inputs/financial_wrapper_continuation01/prior.json','fixture_inputs/financial_wrapper_continuation01/gates.json'}
BASIS=F/'financial-wrapper-continuation-current-preservation-review01-2026-10-05/CURRENT_FULL_RECOVERY_PROOF01.json'
BASIS_PIN='97faaa53f2bcc1cdfd08756480e89632ae6ca6fc4a3f966ace53de3a59cdf19d'
COMPOSITION=F/'financial-wrapper-continuation-current-preservation-preparation01-2026-10-05/CURRENT_COMPOSITION02.json'
COMPOSITION_PIN='65ee768ba3a6569b125920bbc61f01d64487a90a5ced608df31b505cd008f370'
TAIL=F/'heartbeat-root-checkpoint10-2026-10-04/CANONICAL_PLAN_GIT_TAIL01'
TAIL_PIN='270ad2b6047809442ab2e1f75579d83c08d3d6a4fa980aff99cc645a0549294d'
ROLES={'source_review','parent_review','source_input_runtime','cumulative'}
def schema(q):
 R.require(type(q)is dict and set(q)=={'schema_version','source','parent_manifest','parent_request','dependencies','proofs'} and type(q['schema_version'])is int and q['schema_version']==1 and q['source']==SOURCE,'exact delta request')
 R.require(type(q['parent_manifest'])is dict and type(q['parent_request'])is dict and type(q['dependencies'])is list and 0<len(q['dependencies'])<=8 and type(q['proofs'])is dict and set(q['proofs'])==ROLES and all(type(v)is dict for v in q['proofs'].values()),'actual complete Parent and dependencies required')
def merge(base,changed):
 R.require(set(changed)==CHANGED,'exact two changed CAP bodies');out=copy.deepcopy(base);by={r['path']:r for r in out['members']}
 for n,r in changed.items():R.require(n in by and r['kind']=='file' and r['path']==n,'existing regular delta');by[n]=r
 out['members']=[by[n] for n in sorted(by)];R.require(len(out['members'])==1049 and sum(r['kind']=='file' for r in out['members'])==823,'complete inherited CAP denominator');return out
def metadata_population(root,manifest,c):
 expected={r['path']:r for r in manifest['members']};seen=set();pending=[root]
 while pending:
  directory=pending.pop();c.tick();R.require(directory.resolve()==directory,'canonical census directory');before=B.sig(directory.lstat());iterator=None
  try:
   iterator=os.scandir(directory);entries=sorted(iterator,key=lambda e:e.name)
  finally:
   if iterator is not None:B.IO._cleanup((iterator.close,))
  for entry in entries:
   path=directory/entry.name;name=path.relative_to(root).as_posix()
   if name=='.git':continue
   R.require(name in expected,'unknown current CAP member');row=expected[name];info=path.lstat();seen.add(name)
   R.require(stat.S_IMODE(info.st_mode)==row['mode'],'current CAP literal mode')
   if row['kind']=='directory':R.require(stat.S_ISDIR(info.st_mode),'CAP directory type');pending.append(path)
   else:R.require(stat.S_ISREG(info.st_mode) and info.st_size==row['bytes'],'CAP regular extent')
  R.require(B.sig(directory.lstat())==before,'CAP namespace changed during metadata census')
  key=str(directory);R.require(key not in c.seen or c.seen[key]==before,'CAP earlier namespace changed');c.seen[key]=before
 R.require(seen==set(expected),'complete current CAP metadata membership')
def collect(q):
 schema(q);c=B.Census();saved={};origins={};refs={}
 def body(p,pin=None):
  p=Path(p);c.tick();before=B.sig(p.lstat());raw=R.read(p.parent,p.name);R.require(B.sig(p.lstat())==before,'input postcleanup changed');R.require(pin is None or R.digest(raw)==pin,'actual input pin');R.require(str(p) not in c.seen or c.seen[str(p)]==before,'earlier verified identity changed');c.seen[str(p)]=before;c.read_bytes+=len(raw);R.require(c.read_bytes<=32*1024**2,'finite32MiB new reads');refs[str(p)]=R.digest(raw);return raw
 def tree(root,expected,save):
  prior=dict(c.seen);value=c.tree(root,expected,save);R.require(all(k not in c.seen or c.seen[k]==v for k,v in prior.items()),'earlier input signatures cannot be overwritten');c.seen.update(prior);return value
 def ref(v):
  R.require(type(v)is dict and set(v)=={'path','sha256'},'exact input ref');return body(v['path'],v['sha256'])
 basis=json.loads(body(BASIS,BASIS_PIN));ref(basis['review']);prior=json.loads(body(COMPOSITION,COMPOSITION_PIN));tail=json.loads(body(TAIL/'MANIFEST01.json',TAIL_PIN))
 R.require(basis['source']==prior['source']==OLD and basis['scope']['current_CAP_regular']==823 and basis['scope']['current_CAP_typed']==1049 and basis['scope']['current_Git_logical_objects']==416,'accepted complete immutable basis')
 R.require(tail['before']==OLD and tail['after']==SOURCE and tail['source_root']==str(CAP) and len(tail['logical_objects'])==6,'exact six-object tail')
 R.require(B.git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE,'current source')
 diff=set(B.git(CAP,['diff-tree','--no-commit-id','--name-only','-r',OLD,SOURCE]).decode().splitlines());R.require(diff==CHANGED,'only prior/gate committed changes')
 changes={}
 for n in sorted(CHANGED):
  raw=body(CAP/n);R.require(B.git(CAP,['show',SOURCE+':'+n])==raw,'new committed/current body');changes[n]={'path':n,'kind':'file','mode':stat.S_IMODE((CAP/n).stat().st_mode),'bytes':len(raw),'sha256':R.digest(raw)};saved['cap/'+n]=raw
 composed=merge(prior['capsule'],changes);oldoids=set(prior['git']['current416']);newoids={x.split()[0] for x in B.git(CAP,['rev-list','--objects',SOURCE]).decode().splitlines()};R.require(newoids-oldoids=={x['oid'] for x in tail['logical_objects']} and oldoids<=newoids and len(newoids)==422,'complete416+6 original Git ancestry')
 for row in tail['logical_objects']:
  raw=body(TAIL/row['name'],row['sha256']);R.require(len(raw)==row['bytes'] and hashlib.sha1(row['type'].encode()+b' '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['oid'],'Git original type/OID');saved['git/'+row['name']]=raw
 pm=json.loads(ref(q['parent_manifest']));R.validate(pm);expected={r['path']:r['kind'] for r in pm['members']};R.require(all(v in ('file','directory') for v in expected.values()),'ordinary complete Parent only');actual=tree(PARENT,expected,{n for n,k in expected.items() if k=='file'});R.require(actual==pm,'complete actual Parent bytes/modes');origins['parent']={'root':str(PARENT),'manifest':pm}
 request=json.loads(ref(q['parent_request']));R.require(Path(q['parent_request']['path']).parent==PARENT and request['source']==request['design_source']==SOURCE and request['parent_root']==str(PARENT) and request['identity']==B.ID and len(request['source_files'])==359 and len(request['input_hashes'])==29,'actual new Parent context');R.require(request['caller_sha256']==B.sha(c.saved[(str(PARENT),'parent01.py')]) and all(B.sha(c.saved[(str(PARENT),n)])==pin for n,pin in request['helper_hashes'].items()),'actual complete caller/helper joins')
 by={r['path']:r for r in composed['members']};R.require(all(by[n]['sha256']==pin for n,pin in request['source_files'].items()),'new source pins plus immutable basis');reg=json.loads(saved['cap/'+B.REG]);R.require(B.sha(saved['cap/'+B.REG])==request['registration_sha256'] and reg['experiments'][B.ID]['source_files']==request['source_files'],'new actual gate');R.require(all(by[v['path']]['sha256']==v['sha256']==request['input_hashes'][k] for k,v in reg['experiments'][B.ID]['inputs'].items()),'29 role pins via complete composition')
 for n in expected:
  if expected[n]=='file':saved['parent/'+n]=c.saved[(str(PARENT),n)]
 covered=set()
 for i,scope in enumerate(q['dependencies']):
  R.require(set(scope)=={'root','manifest'},'exact dependency scope');root=Path(scope['root']);R.require(root.is_relative_to(F) and root.resolve()==root and root!=H and root!=OUTPUT and root not in (CAP,PARENT),'closed owned evidence scope');seal=json.loads(ref(scope['manifest']));rows=seal['members'];types={r['path']:r['kind'] for r in rows};sealpath=Path(scope['manifest']['path']);R.require(sealpath.parent==root and sealpath.name not in types,'one excluded root seal');types[sealpath.name]='file';R.require(all(k in ('file','directory') for k in types.values()),'ordinary frozen dependency types');m=tree(root,types,{n for n,k in types.items() if k=='file'});R.require([r for r in m['members'] if r['path']!=sealpath.name]==rows,'complete dependency seal');origins['dependency-%02d'%i]={'root':str(root),'manifest':m}
  for n,k in types.items():
   if k=='file':saved['dependencies/%02d/'%i+n]=c.saved[(str(root),n)];covered.add(str(root/n))
 values={k:json.loads(ref(r)) for k,r in q['proofs'].items()};R.require(all(r['path'] in covered for r in q['proofs'].values()),'all proof roles contained in complete preserved dependencies');meta=values['source_input_runtime'];cum=values['cumulative'];R.require(meta['source']==meta['design_source']==SOURCE and meta['caller_sha256']==request['caller_sha256'] and meta['identity']==B.ID and meta['decision']=='accepted-source-input-runtime-metadata-only','genuine actual current metadata proof');R.require(cum['source']==SOURCE and cum['spent_claims']==4 and cum['effective_attempt_budget']==20 and cum['remaining']==16,'unchanged real cumulative accounting')
 R.require(not os.path.lexists(PARENT/'attempt') and not os.path.lexists(CAP/'research_runs'/B.ID),'no new attempt/claim');R.require(sum(map(len,saved.values()))<=16*1024**2,'finite16MiB delta payload');R.require(B.git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE,'final sourceHEAD')
 for scope in origins.values():
  expected={r['path']:r['kind'] for r in scope['manifest']['members']};R.require(tree(Path(scope['root']),expected,set())==scope['manifest'],'final complete small-scope rejoin')
 metadata_population(CAP,composed,c);c.finish()
 result={'schema_version':1,'kind':'canonical-plan-current-byte-delta','source':SOURCE,'basis':{'path':str(BASIS),'sha256':BASIS_PIN},'prior_composition_sha256':COMPOSITION_PIN,'capsule':composed,'origins':origins,'Git':{'basis':416,'new_objects':tail['logical_objects'],'complete':422},'read_pins':refs,'old821_CAP_files_reused_not_read':True,'old_runtime251_not_reread':True,'full_current_recovery':None,'numerical_authority':False,'POSIX_restoration':False}
 return result,saved,c

def main():
 p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--sha256',required=True);a=p.parse_args();request=Path(a.request);raw=R.read(request.parent,request.name);R.require(R.digest(raw)==a.sha256,'actual Root request pin');request_sig=B.sig(request.lstat());result,saved,c=collect(json.loads(raw));R.require(not os.path.lexists(OUTPUT) and OUTPUT.parent.resolve()==OUTPUT.parent,'fresh fixed materialization');OUTPUT.mkdir(mode=0o700);snapshot=OUTPUT/'snapshot';snapshot.mkdir(mode=0o700)
 for i,(name,b) in enumerate(sorted(saved.items())):
  dest=snapshot/('body-%04d'%i)
  with R.new_file(dest) as fd:
   view=memoryview(b)
   while view:
    n=os.write(fd,view);R.require(n>0,'write progress');view=view[n:]
  saved[name]={'flat':dest.name,'bytes':len(b),'sha256':R.digest(b)}
 result['materialized']=saved;R.put(snapshot/'COMPOSITION01.json',result);manifest=R.scan(snapshot)
 for row in manifest['members']:
  if row['path']!='COMPOSITION01.json':R.require(any(v['flat']==row['path'] and v['sha256']==row['sha256'] for v in saved.values()),'complete output bytes')
 R.require(R.read(snapshot,'COMPOSITION01.json')==R.encode(result),'intended composition bytes');R.require(R.read(request.parent,request.name)==raw and B.sig(request.lstat())==request_sig,'request still current')
 R.put(OUTPUT/'archive-manifest.json',manifest);archive_pin=R.pack(snapshot,manifest,OUTPUT/'increment.tar.gz')
 capture={'schema_version':1,'kind':'continuation-current-incremental-byte-capture','source':SOURCE,'archive':'increment.tar.gz','manifest':'archive-manifest.json','archive_pin':archive_pin,'regular':sum(r['kind']=='file' for r in manifest['members']),'typed':len(manifest['members']),'logical_bytes':sum(r.get('bytes',0) for r in manifest['members']),'basis':result['basis'],'original_CAP_files':823,'original_CAP_typed':1049,'Git_objects':422,'new_CAP_bodies':2,'new_Git_objects':6,'old821_copied':False,'old818_copied':False,'external_recovery':False,'numerical_authority':False,'future_final_request':None,'future_release':None}
 R.put(OUTPUT/'CAPTURE01.json',capture);output_pins={str(OUTPUT):B.sig(OUTPUT.lstat()),str(snapshot):B.sig(snapshot.lstat()),**{str(snapshot/r['path']):B.sig((snapshot/r['path']).lstat()) for r in manifest['members']},**{str(OUTPUT/n):B.sig((OUTPUT/n).lstat()) for n in ('archive-manifest.json','increment.tar.gz','CAPTURE01.json')}}
 R.same(snapshot,manifest);R.require(R.read(OUTPUT,'archive-manifest.json')==R.encode(manifest) and R.read(OUTPUT,'CAPTURE01.json')==R.encode(capture),'intended output receipts');R.require(R.digest(R.read(OUTPUT,'increment.tar.gz'))==archive_pin['sha256'],'final archive bytes');R.require(set(p.name for p in OUTPUT.iterdir())=={'snapshot','archive-manifest.json','increment.tar.gz','CAPTURE01.json'},'complete output namespace');c.finish()
 for path,pin in output_pins.items():R.require(B.sig(Path(path).lstat())==pin,'late materialized output change')
 print(json.dumps({'status':'MATERIALIZED_LOCAL_ONLY','output':str(OUTPUT),'new_files':len(saved),'external_recovery':False}))
if __name__=='__main__':main()
