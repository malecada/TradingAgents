"""Actual finite canonical delta composition/PAX readback; no restore or NUM."""
from pathlib import Path
import hashlib,json,os,stat,subprocess,sys
H=Path(__file__).resolve().parent;F=H.parent;D=F/'financial-wrapper-continuation-canonical-delta-root01-2026-10-05';C=F/'heartbeat-root-checkpoint10-2026-10-04';CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source');SOURCE='d4c81c0961342bfe4c5771aabbef1d46a14cffb8'
sys.path.insert(0,str(F/'financial-wrapper-compatibility-complete100-recovery-review01-2026-10-05'))
from verify_capture01 import Reader,R
rd=Reader();cr=rd.read(D/'CAPTURE01.json','2716035164b63c4149b7bb74d5e098ca08a40896bc1b4970dbe3a3246c3fe39f');capture=json.loads(cr);mr=rd.read(D/'archive-manifest.json','78421b4186543c242bfdc0ffd62ae2cc34cb5926a0ead4e7615159638e4b87c9');m=json.loads(mr);R.validate(m);ar=rd.read(D/'increment.tar.gz','8d36e9edfe20b588b1aa8f5d6d26ff3a7e81afbff7e081a42970ee61c5f9f0a4')
rd.need(capture['source']==SOURCE and capture['archive_pin']=={'bytes':len(ar),'sha256':R.digest(ar),'manifest_sha256':R.digest(mr)} and capture['regular']==capture['typed']==len(m['members'])==112 and capture['logical_bytes']==sum(r['bytes'] for r in m['members'])==1990361,'full112 archive population and literal pins')
rd.need(not capture['external_recovery'] and not capture['numerical_authority'] and capture['future_release'] is capture['future_final_request'] is None,'honest unavailable future authority')
expected={r['path']:r for r in m['members']};found={};it=R.framed_members(ar);primary=None
try:
 for n,t,b in it:
  rd.need(n in expected and n not in found,'canonical nonduplicate exact archive namespace');row=expected[n];rd.need(row['kind']=='file' and t.isfile() and t.mode==row['mode']==0o600 and t.uid==t.gid==0 and t.mtime==0 and t.uname==t.gname=='' and len(b)==t.size==row['bytes'] and R.digest(b)==row['sha256'],'actual PAX metadata and every body');found[n]=b
except BaseException as error:primary=error
R._cleanup((it.close,),primary=primary)
if primary is not None:raise primary
rd.need(set(found)==set(expected),'all112 archive members present');rd.tree(D/'snapshot',m)
for n,b in found.items():rd.need(rd.read(D/'snapshot'/n,R.digest(b))==b,'actual captured private copy equals archive')
sink=R.Sink();R.tar_stream(D/'snapshot',m,sink);rd.need(sink.count==len(ar) and sink.hash.hexdigest()==R.digest(ar),'complete canonical PAX recompression')
comp=json.loads(found['COMPOSITION01.json']);material=comp['materialized'];rd.need(len(material)==111 and len({r['flat'] for r in material.values()})==111 and {r['flat'] for r in material.values()}==set(found)-{'COMPOSITION01.json'},'exact111 saved-original bodies plus composition')
qraw=rd.read(C/'CANONICAL_DELTA_REQUEST01.json');q=json.loads(qraw);rd.need(q['source']==comp['source']==SOURCE,'actual Root request/current source')
prior=json.loads(rd.read(F/'financial-wrapper-continuation-current-preservation-preparation01-2026-10-05/CURRENT_COMPOSITION02.json','65ee768ba3a6569b125920bbc61f01d64487a90a5ced608df31b505cd008f370'));basis=json.loads(rd.read(Path(comp['basis']['path']),comp['basis']['sha256']));rd.need(comp['basis']==capture['basis'] and comp['basis']['sha256']=='97faaa53f2bcc1cdfd08756480e89632ae6ca6fc4a3f966ace53de3a59cdf19d' and basis['scope']['current_CAP_regular']==823 and basis['scope']['current_Git_logical_objects']==416,'accepted exact immutable prior recovery basis')
origins={};changes={'fixture_inputs/financial_wrapper_continuation01/gates.json','fixture_inputs/financial_wrapper_continuation01/prior.json'};composed=json.loads(json.dumps(prior['capsule']));by={r['path']:r for r in comp['capsule']['members']}
for n in changes:origins['cap/'+n]=CAP/n
for i,row in enumerate(composed['members']):
 if row['path'] in changes:composed['members'][i]=by[row['path']]
rd.need(composed==comp['capsule'] and len(by)==1049 and sum(r['kind']=='file' for r in by.values())==823,'complete823/1049 with only exact two-row delta')
rd.tree(CAP,comp['capsule'],('.git',))
for role,scope in comp['origins'].items():
 root=Path(scope['root']);om=scope['manifest'];R.validate(om)
 if role=='parent':prefix='parent/';rd.need(q['parent_request']['path'].startswith(str(root)+'/'),'actual Parent root');rd.tree(root,om);pm=json.loads(rd.read(Path(q['parent_manifest']['path']),q['parent_manifest']['sha256']));rd.need(pm==om and len(om['members'])==11,'actual complete eleven-file source-bound Parent')
 else:
  index=int(role.removeprefix('dependency-'));prefix='dependencies/%02d/'%index;dep=q['dependencies'][index];rd.need(dep['root']==str(root),'exact declared dependency root');sealpath=Path(dep['manifest']['path']);sealraw=rd.read(sealpath,dep['manifest']['sha256']);seal=json.loads(sealraw);rd.need([r for r in om['members'] if r['path']!=sealpath.name]==seal['members'],'exact immutable dependency snapshot; future additive files excluded')
 for row in om['members']:
  p=root/row['path'];s=p.lstat();rd.need(stat.S_IMODE(s.st_mode)==row['mode'],'original literal mode retained')
  if row['kind']=='file':rd.need(stat.S_ISREG(s.st_mode) and s.st_size==row['bytes'],'actual original regular extent');origins[prefix+row['path']]=p
  else:rd.need(row['kind']=='directory' and stat.S_ISDIR(s.st_mode),'actual original directory')
tail=C/'CANONICAL_PLAN_GIT_TAIL01';oldset=set(prior['git']['current416']);newrows=comp['Git']['new_objects'];rd.need(comp['Git']['basis']==416 and comp['Git']['complete']==422 and len(newrows)==6,'exact416+6 Git composition')
for row in newrows:origins['git/'+row['name']]=tail/row['name']
rd.need(set(origins)==set(material),'complete exact original-body denominator with no missing role')
for key,p in origins.items():
 row=material[key];body=found[row['flat']];rd.need(len(body)==row['bytes'] and R.digest(body)==row['sha256'] and rd.read(p,row['sha256'])==body,'every111 captured body rejoins actual original')
for row in newrows:
 body=found[material['git/'+row['name']]['flat']];rd.need(len(body)==row['bytes'] and R.digest(body)==row['sha256'] and hashlib.sha1(row['type'].encode()+b' '+str(len(body)).encode()+b'\0'+body).hexdigest()==row['oid'],'all6 actual logical Git object bodies/OIDs')
p=subprocess.run(['git','--no-optional-locks','-C',str(CAP),'rev-list','--objects',SOURCE],capture_output=True,timeout=10,check=True);rd.need(not p.stderr and len(p.stdout)<1024*1024,'bounded actual Git closure');newset={line.split()[0] for line in p.stdout.decode().splitlines()};rd.need(oldset<=newset and len(newset)==422 and newset-oldset=={r['oid'] for r in newrows},'actual full422 closure with accepted416 reused')
for role,ref in q['proofs'].items():
 rd.need(str(Path(ref['path'])) in {str(p) for p in origins.values()},'all4 genuine proof roles inside actual payload');rd.read(Path(ref['path']),ref['sha256'])
parent=Path(q['parent_request']['path']).parent;boundraw=rd.read(Path(q['parent_request']['path']),q['parent_request']['sha256']);bound=json.loads(boundraw);draft=json.loads(rd.read(parent/'REQUEST_DRAFT01.json','678667541715d562dc03a09ef12c84a51c8ef08c70c393fca1322352401da7ef'));want=json.loads(json.dumps(draft));want['proofs']['cumulative']=q['proofs']['cumulative'];want['proofs']['independent_source_input_runtime']=q['proofs']['source_input_runtime'];rd.need(bound==want and bound['proofs']['full_recovery'] is None and bound['final_review'] is None,'actual source-bound draft only fills genuine two metadata proofs')
rd.need(comp['full_current_recovery'] is None and comp['old821_CAP_files_reused_not_read'] and comp['old_runtime251_not_reread'] and not comp['numerical_authority'],'explicit historical reuse and future exclusion')
rd.finish();result={'schema_version':1,'decision':'ACCEPTED_ACTUAL_LOCAL_CANONICAL_DELTA_CAPTURE_ONLY','source':SOURCE,'capture_sha256':R.digest(cr),'archive_sha256':R.digest(ar),'archive_bytes':len(ar),'archive_manifest_sha256':R.digest(mr),'composition_sha256':R.digest(found['COMPOSITION01.json']),'request_sha256':R.digest(qraw),'source_bound_Parent_request_sha256':R.digest(boundraw),'saved_original_bodies':111,'archive_regular':112,'archive_typed':112,'archive_logical_bytes':1990361,'current_CAP_files':823,'current_CAP_typed':1049,'Git_basis':416,'new_Git_objects':6,'current_Git_objects':422,'changed_CAP_bodies':2,'old821_body_hashes_reused_not_reread':True,'runtime251_not_reread':True,'dependency_snapshots':q['dependencies'],'external_recovery':False,'numerical_authority':False,'checks':rd.checks,'read_bytes':rd.total};R.put(H/'DELTA_CAPTURE_READBACK01.json',result);print(json.dumps(result))
