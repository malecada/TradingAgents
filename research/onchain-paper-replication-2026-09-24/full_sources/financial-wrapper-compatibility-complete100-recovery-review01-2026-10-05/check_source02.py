"""Only signing-core correction and final real-FD cohort seam; no public lane entry."""
from verify_capture01 import *
import ast,copy,importlib.util
P=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation02-2026-10-05';OLD=F/'financial-wrapper-compatibility-complete100-outcome-recovery-preparation01-2026-10-05'
rd=Reader();seal=json.loads(rd.read(P/'MANIFEST01.json','ae761adf7452dcc23a4d6e03996aae3dc411e9410bd32691e8920f5087d5fd22'))
for row in seal['members']:
 p=P/row['path'];rd.pin(p);rd.need(stat.S_IMODE(p.lstat().st_mode)==row['mode'],'source02 declared modes')
 if row['kind']=='file':rd.need(len(rd.read(p,row['sha256']))==row['bytes'],'source02 entire sealed bytes')
s=rd.read(P/'outcome01.py','2cb992d405a5e5aa99f35c3c5358e8704e20472b15b569decfd6ea3711c797e3').decode();inv=json.loads(rd.read(P/'INVERSE01.json'));back=s
for a,b in reversed(inv['changes']):rd.need(back.count(b)==1,'one exact literal inverse');back=back.replace(b,a,1)
rd.need(back.encode()==rd.read(OLD/'outcome01.py',inv['original_sha256']),'complete inverse to original01')
for row in seal['members']:
 n=row['path']
 if row['kind']=='file' and n.endswith('.py') and n not in ('outcome01.py','check_core01.py'):rd.need(rd.read(P/n)==rd.read(OLD/n),'all other source exact '+n)
sys.path[:0]=[str(P),str(P/'utilities')];spec=importlib.util.spec_from_file_location('reviewed_outcome02',P/'outcome01.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
q=json.loads(rd.read(P/'LANE01_DRAFT01.json'));core=O.request_core_sha256(q)
# Engineering JSON has no accepted release decision and never reaches public run.
ordinary={'engineering_only':True,'request_core_sha256':core};q['release']={'name':'opaque.json','sha256':R.digest(R.encode(ordinary))}
rd.need(O.request_core_sha256(q)==core,'installing exact excluded reference preserves signing core')
mutations=[]
for k in sorted(set(q)-{'release'}):
 x=copy.deepcopy(q);x[k]=2 if k=='schema_version' else 'changed'
 try:h=O.request_core_sha256(x)
 except ValueError:mutations.append(k)
 else:rd.need(h!=core,'all nonrelease fields bound');mutations.append(k)
for change in ({'name':'../bad','sha256':'a'*64},{'name':'opaque.json','sha256':None},{'name':'opaque.json','sha256':'a'*64,'extra':True}):
 x=copy.deepcopy(q);x['release']=change
 try:O.request_core_sha256(x)
 except ValueError:pass
 else:raise AssertionError('malformed release reference accepted')
run=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='run');segment=ast.get_source_segment(s,run)
rd.need("R.digest(raw)==request_sha" in segment and "q['release']=={'name':release,'sha256':release_sha}" in segment and "R.digest(rel)==release_sha" in segment and "'request_core_sha256':request_core_sha256(q)" in segment,'actual full q/ref/body/core binding retained')
# One tiny actual two-piece filesystem control exercises the final merged cohort.
results=[]
for mutate in (False,True):
 base=HERE/('tiny-late-mutation' if mutate else 'tiny-healthy');base.mkdir(mode=0o700);selected=base/'selected';output=base/'output';selected.mkdir(mode=0o700);output.mkdir(mode=0o700);bundles=[]
 for i in range(2):
  source=base/('source%d'%i);source.mkdir(mode=0o700);(source/'body').write_bytes(b'opaque-only-'+str(i).encode());os.chmod(source/'body',0o600);m=R.scan(source);mr=R.encode(m);mn='manifest%d.json'%i;an='archive%d.gz'%i;(selected/mn).write_bytes(mr);os.chmod(selected/mn,0o600);a=R.pack(source,m,selected/an);bundles.append({'name':'p%d'%i,'manifest':{'path':mn,'sha256':R.digest(mr),'bytes':len(mr)},'archive':{'path':an,'sha256':a['sha256'],'bytes':a['bytes']}})
 inputs=O.VerifiedCohort()
 for b in bundles:
  for k in ('manifest','archive'):O.input_read(inputs,selected,b[k]['path'])
 inputs.tree(selected,{b[k]['path'] for b in bundles for k in ('manifest','archive')})
 res,outputs=O.restore_archives({'bundles':bundles},selected,output,lambda:None,True)
 receipt=output/'engineering-receipt.json';target=output/'flat-p0/body-00000.body';realclose=os.close;fired=[]
 def close(fd):
  name=os.readlink('/proc/self/fd/'+str(fd));realclose(fd)
  if mutate and name==str(receipt) and not fired:
   fired.append(fd)
   with target.open('wb') as f:f.write(b'changed-only')
 try:
  os.close=close;R.put(receipt,{'engineering_only':True})
 finally:os.close=realclose
 inputs.read(output,receipt.name)
 for attr in ('pins','byte_proofs','trees','anchors'):
  t=getattr(inputs,attr);u=getattr(outputs,attr);rd.need(all(k not in t or t[k]==v for k,v in u.items()),'exact production merge conflict predicate');t.update(u)
 try:inputs.check()
 except ValueError as e:
  rd.need(mutate and len(fired)==1,'only real final-close mutation refusal');results.append({'mutation':True,'real_closed_fds':fired,'result':'refused','error':str(e)})
 else:rd.need(not mutate,'late mutated prior output accepted');results.append({'mutation':False,'result':'passed'})
rd.finish();result={'schema_version':1,'decision':'ACCEPTED_NARROW_SOURCE02_SIGNING_CORE_AND_COHORT_ONLY','source_sha256':R.digest(s.encode()),'literal_full_inverse':True,'all_other_source_unchanged':True,'nonrelease_bound_fields':mutations,'real_tiny_two_archive_cohort':results,'actual_public_entries_executed':False,'actual_release_authority':False,'checks':rd.checks}
(HERE/'SOURCE02_CHECKS.json').write_bytes(R.encode(result));print(json.dumps(result))
