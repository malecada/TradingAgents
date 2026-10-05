"""Exact continuation increment byte scope; no admission or numerical execution."""
from pathlib import Path
import json,hashlib,os,sys,time,stat
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE/'utilities')]
import recovery_pax01 as R
import space01 as W
from cohort01 import VerifiedCohort
from receipt01 import encode as selection_encode
from flat_primitives01 import input_read,restore_archives
ROOT=W.ROOT;F=W.F
CAPTURE=None
CAPTURE_PATH='research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-continuation-canonical-delta-root01-2026-10-05/CAPTURE01.json'
LANES=((0,),)
SOURCE='d4c81c0961342bfe4c5771aabbef1d46a14cffb8'
def lane_root(i,phase):
 R.require(type(i)is int and i==0 and phase in ('remote','flat'),'one fixed incremental route')
 return F/('financial-wrapper-continuation-canonical-'+phase+'01-2026-10-05')
HELPERS=('outcome01.py','restore_bundle01.py','flat_primitives01.py','cohort01.py','space01.py','watch01.py','receipt01.py','recover.template01.py','caller_remote01.py','caller_flat01.py','bind_entry01.py','bind_capture01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py')
def context(raw):
 R.require(R.digest(raw)==CAPTURE,'actual incremental capture pin');c=json.loads(raw)
 R.require(c['kind']=='continuation-current-incremental-byte-capture' and c['source']==SOURCE and c['numerical_authority'] is False and c['external_recovery'] is False and c['old818_copied'] is False,'exact scope and exclusions')
 R.require(c['archive']=='increment.tar.gz' and c['manifest']=='archive-manifest.json','fixed actual archive pair')
 return c

def expected_required(c):
 prefix=str(Path(CAPTURE_PATH).parent)+'/'
 required={}
 for name in ('CAPTURE01.json',c['archive'],c['manifest']):
  raw=R.read(HERE,name);required[prefix+name]={'bytes':len(raw),'sha256':R.digest(raw)}
 R.require(required[CAPTURE_PATH]['sha256']==CAPTURE and required[prefix+c['archive']]=={k:c['archive_pin'][k] for k in ('bytes','sha256')} and required[prefix+c['manifest']]['sha256']==c['archive_pin']['manifest_sha256'],'exact pinned three-body archive closure')
 return required

def selected_required(q,i,c):
 lane_root(i,'remote');R.require(q['status']=='ROOT_FROZEN_CONTINUATION_CANONICAL' and q['source']==SOURCE and type(q['lane'])is int and q['lane']==0,'actual fixed request')
 R.require(type(q['commit'])is str and len(q['commit'])==40 and all(x in '0123456789abcdef' for x in q['commit']),'actual final commit')
 required=q['required'];R.require(required==expected_required(c),'exact complete incremental and helper selection')
 R.require(q['proofs']=={'captured_preservation_source_release':True,'historical_basis_reused':True,'future_full_current_recovery':None},'no fabricated future proof')
 R.require(len(required)<=506 and sum(v['bytes'] for v in required.values())<=28*1024**2,'finite receiver selection')
 for n,v in required.items():R.path_name(n);R.require(type(v['bytes'])is int and 0<=v['bytes']<=R.FILE,'actual body bound')
 return required

def generate(q,raw):
 """Return concrete receiver and caller bodies; Root alone writes/reviews them."""
 c=context(raw);i=q['lane'];required=selected_required(q,i,c);suffix='continuation-canonical01'
 s=R.read(HERE,'recover.template01.py').decode();changes=[('REQUIRED = None','REQUIRED = '+repr(required)),('FINAL_POPULATION_COUNT = None','FINAL_POPULATION_COUNT = '+str(len(required))),('compatibility-final-bundle01',suffix),('import watch01 as W','import space01 as W')]
 for a,b in changes:R.require(a in s,'receiver exact seam');s=s.replace(a,b)
 # Preserve original operation/FSIZE/watch/cleanup implementation; replace stale scope prose.
 a="Exact frozen operational source/policy delta, genuine independent policy review and complete closed failed forensic Root02 scope recovered. Original failed histories remain spent; no claim is started. Old385 actual recovered Git plus nine new bodies form an explicitly checked394-object source basis; final registration/caller/runtime-body recovery remain separate."
 b="Exact current continuation incremental capture and all declared closed source/review dependencies. Accepted complete capsule and416 Git basis are reused; two corrected metadata bodies, six new Git objects and the complete actual canonical Parent/proof population are retained. No claim is started; full current recovery still requires independent actual composition."
 R.require(a in s,'original qualification seam');s=s.replace(a,b);changes.append((a,b))
 receipts=R.read(HERE,'receipt01.py').decode().replace('compatibility-final-supplement02',suffix)
 callers={}
 for phase in ('remote','flat'):
  body=R.read(HERE,'caller_'+phase+'01.py').decode()
  body=body.replace('financial-wrapper-compatibility-final-supplement-root02-2026-10-05',lane_root(i,'remote').name).replace('financial-wrapper-compatibility-final-supplement-flat-root02-2026-10-05',lane_root(i,'flat').name)
  body=body.replace('ROOT_BOUND_FINAL_SUPPLEMENT_ENTRY','ROOT_BOUND_CONTINUATION_CANONICAL_ENTRY').replace('ACCEPTED_EXACT_ONE_USE_FINAL_SUPPLEMENT_','ACCEPTED_EXACT_ONE_USE_CONTINUATION_CANONICAL_').replace('ROOT_FINAL_SUPPLEMENT_','ROOT_CONTINUATION_CANONICAL_').replace('fresh-compatibility-final-supplement02.git','fresh-'+suffix+'.git')
  body=body.replace('import owned_io as IO;import watch01 as W','import owned_io as IO;import watch01 as W;import space01;space01.check()')
  body=body.replace("'binding01.py'","'outcome01.py','flat_primitives01.py','space01.py'")
  callers[phase]=body
 selection={'remote_commit':q['commit'],'rows':[dict(path=n,**v) for n,v in sorted(required.items())]}
 return {'receiver':s,'receipt':receipts,'callers':callers,'receiver_changes':changes,'selection_body':selection_encode(selection)}

REQUEST_FIELDS={'schema_version','status','lane','source','commit','required','proofs','remote','profile','release'}
def request_core_sha256(q):
 R.require(type(q)is dict and set(q)==REQUEST_FIELDS and type(q['schema_version'])is int and q['schema_version']==1,'exact request signing fields')
 ref=q['release']
 R.require(ref is None or (type(ref)is dict and set(ref)=={'name','sha256'} and type(ref['name'])is str and R.path_name(ref['name'])==ref['name'] and type(ref['sha256'])is str and len(ref['sha256'])==64 and all(c in '0123456789abcdef' for c in ref['sha256'])),'exact nullable release reference')
 return R.digest(R.encode({k:v for k,v in q.items() if k!='release'}))

def run(request,request_sha,release,release_sha):
 from receipt_current01 import validate_remote
 inputs=VerifiedCohort();raw=input_read(inputs,HERE,request);R.require(R.digest(raw)==request_sha,'actual request pin');q=json.loads(raw);i=q['lane'];R.require(HERE==lane_root(i,'flat'),'fixed fresh flat root')
 request_core_sha256(q);R.require(q['release']=={'name':release,'sha256':release_sha},'actual release ref must equal full authenticated request')
 def body(ref):
  b=input_read(inputs,ROOT,ref['path']);R.require(len(b)==ref['bytes'] and R.digest(b)==ref['sha256'],'actual pinned body');return b
 rel=input_read(inputs,HERE,release);R.require(R.digest(rel)==release_sha,'actual release pin')
 R.require(json.loads(rel)=={'schema_version':1,'decision':'ACCEPTED_EXACT_CONTINUATION_CANONICAL_FLAT','lane':i,'request_core_sha256':request_core_sha256(q),'source_sha256':R.digest(input_read(inputs,HERE,'outcome01.py')),'numerical_authority':False},'different-author lane release')
 for name in HELPERS+('CAPTURE01.json','archive-manifest.json','increment.tar.gz','receipt_current01.py'):input_read(inputs,HERE,name)
 receiver=lane_root(i,'remote');selected=receiver/'selected';capture_raw=input_read(inputs,selected,CAPTURE_PATH);c=context(capture_raw);required=selected_required(q,i,c)
 remote=json.loads(body(q['remote']));selection={'remote_commit':q['commit'],'rows':[dict(path=n,**v) for n,v in sorted(required.items())]};records=validate_remote(remote,selection,R.digest(selection_encode(selection)),required)
 R.require(remote['fresh_git_root']==str(receiver/'fresh-continuation-canonical01.git'),'actual lane receiver Git root')
 profile=json.loads(body(q['profile']));R.require(profile['actual_selected_root']==str(selected) and R.scan(selected)==profile['full_manifest'],'actual selected modes/full population');m=profile['full_manifest'];files={r['path']:r for r in m['members'] if r['kind']=='file'};dirs={'.':m['root_mode'],**{r['path']:r['mode'] for r in m['members'] if r['kind']=='directory'}}
 R.require(set(files)==set(required),'full selected exact set');inputs.selected_profile={'actual_selected_root':str(selected),'expected_owner_uid':os.geteuid(),'directory_modes':dirs,'files':files}
 for r in records:
  b=input_read(inputs,selected,r['path']);R.require(len(b)==r['bytes'] and R.digest(b)==r['sha256'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['git_object'],'actual selected Git/body join')
 inputs.tree(selected,set(files));bundles=[];prefix=str(Path(CAPTURE_PATH).parent)+'/'
 mr={'path':prefix+c['manifest'],**required[prefix+c['manifest']]};ar={'path':prefix+c['archive'],**required[prefix+c['archive']]};manifest=json.loads(input_read(inputs,selected,mr['path']));R.validate(manifest)
 R.require(len(manifest['members'])==c['typed'] and sum(x['kind']=='file' for x in manifest['members'])==c['regular'] and sum(x.get('bytes',0) for x in manifest['members'])==c['logical_bytes'],'complete actual incremental population')
 bundles.append({'name':'current-increment','manifest':mr,'archive':ar})
 begun=time.monotonic()
 def boundary():R.require(time.monotonic()-begun<180,'bounded lane restoration');W.census(HERE)
 R.require(not os.path.lexists(HERE/'LANE_RECOVERY01.json'),'fresh lane receipt');boundary();results,outputs=restore_archives({'bundles':bundles},selected,HERE,boundary,True);boundary()
 receipt={'schema_version':1,'lane':i,'capture_sha256':CAPTURE,'request_sha256':request_sha,'scope':'current-increment','scopes':results,'numerical_authority':False,'requires_actual_composition_review':True}
 expected_receipt=R.encode(receipt)
 R.put(HERE/'LANE_RECOVERY01.json',receipt)
 R.require(inputs.read(HERE,'LANE_RECOVERY01.json')==expected_receipt,'published receipt differs from intended canonical bytes');boundary()
 for attr in ('pins','byte_proofs','trees','anchors'):
  target=getattr(inputs,attr);source=getattr(outputs,attr);R.require(all(k not in target or target[k]==v for k,v in source.items()),'cohort overlaps agree');target.update(source)
 inputs.check()
