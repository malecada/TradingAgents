"""Exact four-lane closed-outcome byte scope; no admission or numerical execution."""
from pathlib import Path
import json,hashlib,os,sys,time,stat
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE),str(HERE/'utilities')]
import recovery_pax01 as R
import space01 as W
from cohort01 import VerifiedCohort
from flat_primitives01 import input_read,restore_archives
ROOT=W.ROOT;F=W.F
CAPTURE='ef82889318080bf2fec673d6c558c4afe3d95260c1a4d783c9b5eb16d8979442'
CAPTURE_PATH='research/onchain-paper-replication-2026-09-24/full_sources/financial-wrapper-compatibility-complete100-outcome-capture01-2026-10-05/CAPTURE01.json'
LANES=(tuple(range(7)),tuple(range(7,14)),tuple(range(14,20)),tuple(range(20,26)))
SOURCE='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41'
def lane_root(i,phase):
 R.require(type(i)is int and 0<=i<4 and phase in ('remote','flat'),'four fixed lane roots')
 return F/('financial-wrapper-compatibility-complete100-outcome-'+phase+'-lane%02d-2026-10-05'%(i+1))
def context(raw):
 R.require(R.digest(raw)==CAPTURE,'actual complete capture pin');c=json.loads(raw)
 R.require(c['kind']=='complete-terminal-opaque-sharded-capture-v1' and c['numerical_authority'] is False and c['POSIX_instantiation'] is False and c['exclusions']=={'capsule':['.git'],'parent':[]},'original opaque scope')
 R.require([p['id'] for p in c['pieces']]==list(range(26)),'all26 pieces exactly once')
 originals={};total=0
 for role,v in c['originals'].items():
  R.validate(v['manifest'])
  for r in v['manifest']['members']:
   if r['kind']=='file':originals[(role,r['path'])]=(r['bytes'],r['sha256']);total+=r['bytes']
 mapped={}
 for p in c['pieces']:
  R.require(sum(b['bytes'] for b in p['bodies'])<=3*1024**2 and len(p['bodies'])<=256,'original piece bounds')
  for b in p['bodies']:
   k=(b['role'],b['path']);R.require(k not in mapped,'no duplicate original');mapped[k]=(b['bytes'],b['sha256'])
 R.require(mapped==originals and len(originals)==845 and total==77970429 and sum(len(v['manifest']['members']) for v in c['originals'].values())==1074,'full original845/1074 exact cover')
 return c

def selected_required(q,i,c):
 lane_root(i,'remote')
 R.require(q['status']=='ROOT_FROZEN_OUTCOME_FOUR_LANES' and q['source']==SOURCE and type(q['lane'])is int and q['lane']==i,'actual fixed request')
 R.require(type(q['commit'])is str and len(q['commit'])==40 and all(x in '0123456789abcdef' for x in q['commit']),'actual final commit')
 required=q['required'];R.require(type(required)is dict,'exact selected population')
 prefix=str(Path(CAPTURE_PATH).parent)+'/'
 names={CAPTURE_PATH}
 for j in LANES[i]:names.update(prefix+c['pieces'][j][k] for k in ('archive','manifest'))
 refs=q['proofs'];R.require(set(refs)=={'source407_basis','outcome_disposition','cleanup','actual_capture_review'},'genuine proof roles')
 for ref in refs.values():
  R.require(type(ref)is dict and set(ref)=={'path','bytes','sha256'},'actual proof refs, no null');names.add(R.path_name(ref['path']))
 R.require(set(required)==names and sum(v['bytes'] for v in required.values())<=28*1024**2,'bounded exact lane selection')
 for n,v in required.items():R.path_name(n);R.require(set(v)=={'bytes','sha256'} and type(v['bytes'])is int and 0<=v['bytes']<=R.FILE and type(v['sha256'])is str and len(v['sha256'])==64 and all(x in '0123456789abcdef' for x in v['sha256']),'exact selected pin')
 R.require(required[CAPTURE_PATH]=={'bytes':705237,'sha256':CAPTURE},'common actual capture')
 for ref in refs.values():R.require(required[ref['path']]=={k:ref[k] for k in ('bytes','sha256')},'proof selected')
 for j in LANES[i]:
  p=c['pieces'][j];R.require(required[prefix+p['archive']]=={k:p['archive_pin'][k] for k in ('bytes','sha256')} and required[prefix+p['manifest']]['sha256']==p['archive_pin']['manifest_sha256'],'exact selected piece pins')
 return required

def generate(q,raw):
 """Return concrete receiver and caller bodies; Root alone writes/reviews them."""
 c=context(raw);i=q['lane'];required=selected_required(q,i,c);suffix='compatibility-complete100-outcome-lane%02d'%(i+1)
 s=R.read(HERE,'recover.template01.py').decode();changes=[('REQUIRED = None','REQUIRED = '+repr(required)),('FINAL_POPULATION_COUNT = None','FINAL_POPULATION_COUNT = '+str(len(required))),('compatibility-final-bundle01',suffix),('import watch01 as W','import space01 as W')]
 for a,b in changes:R.require(a in s,'receiver exact seam');s=s.replace(a,b)
 # Preserve original operation/FSIZE/watch/cleanup implementation; replace stale scope prose.
 a="Exact frozen operational source/policy delta, genuine independent policy review and complete closed failed forensic Root02 scope recovered. Original failed histories remain spent; no claim is started. Old385 actual recovered Git plus nine new bodies form an explicitly checked394-object source basis; final registration/caller/runtime-body recovery remain separate."
 b="Exact one of four disjoint complete100 outcome archive lanes; common complete capture and original outcome proofs retained. Separate accepted605/407 source basis is referenced, not reconstructed here. No claim is started and no scientific completion follows."
 R.require(a in s,'original qualification seam');s=s.replace(a,b);changes.append((a,b))
 receipts=R.read(HERE,'receipt01.py').decode().replace('compatibility-final-supplement02',suffix)
 callers={}
 for phase in ('remote','flat'):
  body=R.read(HERE,'caller_'+phase+'01.py').decode()
  body=body.replace('financial-wrapper-compatibility-final-supplement-root02-2026-10-05',lane_root(i,'remote').name).replace('financial-wrapper-compatibility-final-supplement-flat-root02-2026-10-05',lane_root(i,'flat').name)
  body=body.replace('ROOT_BOUND_FINAL_SUPPLEMENT_ENTRY','ROOT_BOUND_OUTCOME_LANE%02d_ENTRY'%(i+1)).replace('ACCEPTED_EXACT_ONE_USE_FINAL_SUPPLEMENT_','ACCEPTED_EXACT_ONE_USE_OUTCOME_LANE%02d_'%(i+1)).replace('ROOT_FINAL_SUPPLEMENT_','ROOT_OUTCOME_LANE%02d_'%(i+1)).replace('fresh-compatibility-final-supplement02.git','fresh-'+suffix+'.git')
  body=body.replace('import owned_io as IO;import watch01 as W','import owned_io as IO;import watch01 as W;import space01;space01.check()')
  body=body.replace("'binding01.py'","'outcome01.py','flat_primitives01.py','space01.py'")
  callers[phase]=body
 return {'receiver':s,'receipt':receipts,'callers':callers,'receiver_changes':changes}

REQUEST_FIELDS={'schema_version','status','lane','source','commit','required','proofs','remote','profile','release'}
def request_core_sha256(q):
 R.require(type(q)is dict and set(q)==REQUEST_FIELDS and type(q['schema_version'])is int and q['schema_version']==1,'exact request signing fields')
 ref=q['release']
 R.require(ref is None or (type(ref)is dict and set(ref)=={'name','sha256'} and type(ref['name'])is str and R.path_name(ref['name'])==ref['name'] and type(ref['sha256'])is str and len(ref['sha256'])==64 and all(c in '0123456789abcdef' for c in ref['sha256'])),'exact nullable release reference')
 return R.digest(R.encode({k:v for k,v in q.items() if k!='release'}))

def run(request,request_sha,release,release_sha):
 from receipt01 import validate_remote
 inputs=VerifiedCohort();raw=input_read(inputs,HERE,request);R.require(R.digest(raw)==request_sha,'actual request pin');q=json.loads(raw);i=q['lane'];R.require(HERE==lane_root(i,'flat'),'fixed fresh flat root')
 request_core_sha256(q);R.require(q['release']=={'name':release,'sha256':release_sha},'actual release ref must equal full authenticated request')
 def body(ref):
  b=input_read(inputs,ROOT,ref['path']);R.require(len(b)==ref['bytes'] and R.digest(b)==ref['sha256'],'actual pinned body');return b
 rel=input_read(inputs,HERE,release);R.require(R.digest(rel)==release_sha,'actual release pin')
 R.require(json.loads(rel)=={'schema_version':1,'decision':'ACCEPTED_EXACT_OUTCOME_LANE_FLAT','lane':i,'request_core_sha256':request_core_sha256(q),'source_sha256':R.digest(input_read(inputs,HERE,'outcome01.py')),'numerical_authority':False},'different-author lane release')
 for name in ('outcome01.py','restore_bundle01.py','flat_primitives01.py','cohort01.py','space01.py','watch01.py','receipt01.py','utilities/recovery_pax01.py','utilities/owned_io.py','utilities/bounded_git01.py'):input_read(inputs,HERE,name)
 receiver=lane_root(i,'remote');selected=receiver/'selected';capture_raw=input_read(inputs,selected,CAPTURE_PATH);c=context(capture_raw);required=selected_required(q,i,c)
 remote=json.loads(body(q['remote']));selection={'remote_commit':q['commit'],'rows':[dict(path=n,**v) for n,v in sorted(required.items())]};records=validate_remote(remote,selection,R.digest(R.encode(selection)),required)
 R.require(remote['fresh_git_root']==str(receiver/('fresh-compatibility-complete100-outcome-lane%02d.git'%(i+1))),'actual lane receiver Git root')
 profile=json.loads(body(q['profile']));R.require(profile['actual_selected_root']==str(selected) and R.scan(selected)==profile['full_manifest'],'actual selected modes/full population');m=profile['full_manifest'];files={r['path']:r for r in m['members'] if r['kind']=='file'};dirs={'.':m['root_mode'],**{r['path']:r['mode'] for r in m['members'] if r['kind']=='directory'}}
 R.require(set(files)==set(required),'full selected exact set');inputs.selected_profile={'actual_selected_root':str(selected),'expected_owner_uid':os.geteuid(),'directory_modes':dirs,'files':files}
 for r in records:
  b=input_read(inputs,selected,r['path']);R.require(len(b)==r['bytes'] and R.digest(b)==r['sha256'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['git_object'],'actual selected Git/body join')
 inputs.tree(selected,set(files));bundles=[];prefix=str(Path(CAPTURE_PATH).parent)+'/'
 for j in LANES[i]:
  p=c['pieces'][j];mr={'path':prefix+p['manifest'],**required[prefix+p['manifest']]};ar={'path':prefix+p['archive'],**required[prefix+p['archive']]};manifest=json.loads(input_read(inputs,selected,mr['path']))
  R.require({x['path']:(x['bytes'],x['sha256']) for x in manifest['members'] if x['kind']=='file'}=={b['member']:(b['bytes'],b['sha256']) for b in p['bodies']},'piece map/body hashes');bundles.append({'name':'piece-%03d'%j,'manifest':mr,'archive':ar})
 begun=time.monotonic()
 def boundary():R.require(time.monotonic()-begun<180,'bounded lane restoration');W.census(HERE)
 R.require(not os.path.lexists(HERE/'LANE_RECOVERY01.json'),'fresh lane receipt');boundary();results,outputs=restore_archives({'bundles':bundles},selected,HERE,boundary,True);boundary()
 R.put(HERE/'LANE_RECOVERY01.json',{'schema_version':1,'lane':i,'capture_sha256':CAPTURE,'request_sha256':request_sha,'piece_ids':list(LANES[i]),'scopes':results,'numerical_authority':False,'requires_cross_lane_original_review':True})
 inputs.read(HERE,'LANE_RECOVERY01.json');boundary()
 for attr in ('pins','byte_proofs','trees','anchors'):
  target=getattr(inputs,attr);source=getattr(outputs,attr);R.require(all(k not in target or target[k]==v for k,v in source.items()),'cohort overlaps agree');target.update(source)
 inputs.check()
