"""Exact canonical-plan Root rebinder. Default is read-only; materialization is explicit."""
import argparse,ast,hashlib,json,os,shutil,stat,time
from pathlib import Path
import recovery04 as R
from bounded_git01 import git
H=Path(__file__).resolve().parent;B=H.parent
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
OLD_PARENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-compatibility-root-launch-20261005-01')
TARGET=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-continue100-canonical-plan-root-launch-20261005-01')
SOURCE='d4c81c0961342bfe4c5771aabbef1d46a14cffb8';OLD_SOURCE='664e2ca5fa11d6640ab79f64c5aa222aeb3a9128'
MANIFEST=B/'heartbeat-root-checkpoint10-2026-10-04/CANONICAL_PLAN_SOURCE_MANIFEST01.json'
MANIFEST_SHA='1cc3b8796a656db8df02ecec0c871cdd575f4164ef58decda2326ce3fb42be46'
REG='fixture_inputs/financial_wrapper_continuation01/gates.json';PRIOR='fixture_inputs/financial_wrapper_continuation01/prior.json'
GATE_SHA='1f96b8efd7fdd468cb9ef87059c5bba026c4aa238f21580ed3ae6e961146e18d';PRIOR_SHA='b8b4b4f124aebdd5816c8dc0427814139feedd66682f1092bc76c6d25d50b9a9'
OLD_GATE_SHA='c4f33416f952ee5e9a2177fc4455bff51662e9fe6639016a92373ca16ba1d693'
ID='financial-wrapper-classification-eager-continue100-compatibility-20261004-01'
sha=lambda b:hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def fresh():
 need(TARGET.is_absolute() and TARGET.parent.resolve()==TARGET.parent and not os.path.lexists(TARGET),'fixed canonical fresh Parent required')
 need(not TARGET.is_relative_to(CAP) and not CAP.is_relative_to(TARGET),'disjoint Parent/source')
 need(not os.path.lexists(CAP/'research_runs'/ID) and not os.path.lexists(OLD_PARENT/'attempt'),'unclaimed identity and no old Parent attempt')
class Reads:
 def __init__(self):self.start=time.monotonic();self.charged=0;self.cache={}
 def tick(self):need(time.monotonic()-self.start<120,'120s preparation bound');need(shutil.disk_usage(H).free>=10*1024**3,'10GiB floor')
 def read(self,p):
  self.tick();p=Path(p);need(p.is_absolute() and p.resolve()==p,'canonical input');raw=R.read(p.parent,p.name);self.charged+=len(raw);need(self.charged<=64*1024**2,'64MiB preparation read bound');need(str(p) not in self.cache or self.cache[str(p)]==raw,'input currentness');self.cache[str(p)]=raw;self.tick();return raw
 def get(self,p):return self.cache.get(str(p)) if str(p) in self.cache else self.read(p)
 def finish(self):
  for p in tuple(self.cache):self.read(Path(p))
  self.tick()
def build():
 fresh();reader=Reads();pinraw=reader.read(H/'BODY_PINS01.json');need(sha(pinraw)=='1b18c23dbe0e58031561f50292d0bd7ed87585c4857b0219942f6bc28bf754c1','exact original body-pin table');pins=json.loads(pinraw)
 for name,ref in pins.items():
  raw=reader.read(H/name);need(sha(raw)==ref['sha256'] and len(raw)==ref['bytes'],'copied original dependency');need(reader.read(Path(ref['origin']))==raw,'actual old Parent dependency retained')
 original=reader.get(H/'original_parent01.py');need(sha(original)=='b50d1e727979a989f3da1e18a5b204cc3d29169ad425806e8550aa88af5ed0be','exact old caller')
 oldq=json.loads(reader.get(H/'original_REQUEST_DRAFT01.json'));mraw=reader.read(MANIFEST);need(sha(mraw)==MANIFEST_SHA,'actual Root source manifest');m=json.loads(mraw)
 need(set(m)=={'schema_version','source','registration','registration_sha256','source_files','tracked_count'} and m['source']==SOURCE and m['registration']==REG and m['registration_sha256']==GATE_SHA and len(m['source_files'])==359 and m['tracked_count']==360,'actual360/359 source schema')
 need(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE and git(CAP,['rev-parse',SOURCE+'^'],cap=128).decode().strip()==OLD_SOURCE,'actual direct source ancestry')
 names=git(CAP,['diff-tree','--no-commit-id','--name-only','-r',OLD_SOURCE,SOURCE]).decode().splitlines();need(set(names)=={REG,PRIOR} and len(names)==2,'exact two metadata changes')
 oldmap=oldq['source_files'];need(set(oldmap)==set(m['source_files']) and {n for n in oldmap if oldmap[n]!=m['source_files'][n]}=={PRIOR} and m['source_files'][PRIOR]==PRIOR_SHA,'only prior changes in359 source map')
 tree={}
 for entry in git(CAP,['ls-tree','-r','-z',SOURCE]).split(b'\0'):
  if not entry:continue
  header,name=entry.split(b'\t',1);mode,kind,oid=header.decode().split();name=name.decode();need(kind=='blob' and mode in ('100644','100755') and name not in tree,'regular unique committed source');tree[name]=(mode,oid)
 need(set(tree)==set(m['source_files'])|{REG} and len(tree)==360,'whole actual tracked membership')
 for name,(mode,oid) in tree.items():
  R.path_name(name);raw=reader.read(CAP/name);expected=GATE_SHA if name==REG else m['source_files'][name];need(sha(raw)==expected and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid,'actual body/hash/Git blob joins');need(bool((CAP/name).stat().st_mode&0o111)==(mode=='100755'),'Git executable class')
 oldgate=json.loads(git(CAP,['show',OLD_SOURCE+':'+REG]));gate=json.loads(reader.get(CAP/REG));need(sha(git(CAP,['show',OLD_SOURCE+':'+REG]))==OLD_GATE_SHA,'old committed gate')
 # The exact candidate literal inverse authenticates all historical definitions and controls.
 graw=reader.get(CAP/REG);oldprior=oldmap[PRIOR];restored=graw.replace(b'"historical_plan"',b'"historical_wrapper_plan"').replace(PRIOR_SHA.encode(),oldprior.encode());need(sha(restored)==OLD_GATE_SHA,'exact gate metadata inverse')
 e=gate['experiments'][ID];need(len(e['inputs'])==29 and e['source_files']==m['source_files'],'exact continuation roles/map')
 for role,ref in e['inputs'].items():
  need(type(ref['path'])is str and sha(reader.get(CAP/R.path_name(ref['path'])))==ref['sha256'],'actual29 input bytes')
 need(json.loads(reader.get(CAP/e['inputs']['runtime_mapping']['path']))==oldq['runtime_mapping'],'unchanged runtime251 metadata mapping')
 contract_raw=reader.get(H/'original_proof_reuse_contract01.json');need(contract_raw.count(OLD_SOURCE.encode())==1,'one original current-source literal');contract=json.loads(contract_raw);need(contract['current_source']==OLD_SOURCE,'old genuine reuse context');newcontract=contract_raw.replace(OLD_SOURCE.encode(),SOURCE.encode());newc=json.loads(newcontract);need({k:v for k,v in newc.items() if k!='current_source'}=={k:v for k,v in contract.items() if k!='current_source'} and newc['current_source']==SOURCE,'seven anchors and actual recovery unchanged')
 binding={'source':SOURCE,'registration_sha256':GATE_SHA,'source_map_sha256':sha(R.encode(m['source_files'])),'source_count':359,'tracked_count':360};need(binding['source_map_sha256']=='a43dd6ead208ce661ddb01c3d030fba1effefc123945ee78068f0e4a6947b44b','actual source-map pin')
 text=original.decode();lines=text.splitlines(keepends=True);oldline=next(x for x in lines if x.startswith('SOURCE_BINDING='));newline='SOURCE_BINDING='+repr(binding)+'\n';parent=text.replace(oldline,newline);oldpath="PARENT=Path('"+str(OLD_PARENT)+"')";newpath="PARENT=Path('"+str(TARGET)+"')";need(parent.count(oldpath)==1,'one original Parent literal');parent=parent.replace(oldpath,newpath);need(parent.replace(newpath,oldpath).replace(newline,oldline)==text,'full original caller inverse')
 q=dict(oldq);q.update(source=SOURCE,design_source=SOURCE,parent_root=str(TARGET),registration_sha256=GATE_SHA,source_files=m['source_files'],input_hashes={k:v['sha256'] for k,v in e['inputs'].items()},caller_sha256=sha(parent.encode()),helper_hashes=dict(oldq['helper_hashes']),proofs={k:None for k in oldq['proofs']},final_review=None,status='DRAFT_NOT_RELEASED');q['helper_hashes']['proof_reuse_contract01.json']=sha(newcontract)
 files={name:reader.get(H/name) for name in oldq['helper_hashes'] if name!='proof_reuse_contract01.json'};files.update({'parent01.py':parent.encode(),'proof_reuse_contract01.json':newcontract,'REQUEST_DRAFT01.json':R.encode(q)})
 reader.finish();fresh();need(git(CAP,['rev-parse','HEAD'],cap=128).decode().strip()==SOURCE,'final actual source');reader.tick()
 return files,{'schema_version':1,'status':'DRAFT_NOT_RELEASED','target':str(TARGET),'source':SOURCE,'binding':binding,'files':{n:{'bytes':len(v),'sha256':sha(v)} for n,v in files.items()},'actual_preparation_reads_including_finish':reader.charged,'caller_inverse':[{'old':oldline,'new':newline},{'old':oldpath,'new':newpath}],'proofs':q['proofs'],'final_review':None,'native_execution':False}
def materialize(files):
 start=time.monotonic()
 def tick():need(time.monotonic()-start<120,'finite materialization');need(shutil.disk_usage(H).free>=10*1024**3,'materialization10GiB floor')
 tick();fresh();need(len(files)==10 and all(type(v)is bytes and len(v)<=4*1024**2 for v in files.values()) and sum(map(len,files.values()))<=64*1024**2,'exact bounded draft bodies');TARGET.mkdir(mode=0o700)
 for name,raw in files.items():
  tick()
  with R.new_file(TARGET/name) as fd:
   offset=0
   while offset<len(raw):n=os.write(fd,raw[offset:]);need(n>0,'short write');offset+=n
   os.fsync(fd)
  need(R.read(TARGET,name)==raw,'fresh Root body readback')
 need(set(p.name for p in TARGET.iterdir())==set(files),'complete fresh Root body set');tick()
def main():
 p=argparse.ArgumentParser();p.add_argument('--materialize',action='store_true');a=p.parse_args();files,receipt=build()
 if a.materialize:materialize(files)
 print(json.dumps(dict(receipt,Root_materialized=a.materialize),sort_keys=True))
if __name__=='__main__':main()
