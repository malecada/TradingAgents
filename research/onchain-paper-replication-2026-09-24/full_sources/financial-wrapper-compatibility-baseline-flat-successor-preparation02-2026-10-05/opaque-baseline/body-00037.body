from pathlib import Path
import importlib.util,json,hashlib,copy
H=Path(__file__).resolve().parent;B=H.parent;P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01');CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
raw=(P/'preclaim01.py').read_bytes();assert hashlib.sha256(raw).hexdigest()=='557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16'
s=importlib.util.spec_from_file_location('_controls_preclaim',P/'preclaim01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
q=json.loads((P/'REQUEST_DRAFT01.json').read_bytes());g=json.loads((CAP/q['registration']).read_bytes());e=g['experiments'][q['identity']];facts=json.loads((H/'INVENTORY_DRAFT01.json').read_bytes());refs=facts['external_refs'];checks=[]
r=m.Reader();i=m.Inputs(CAP,e['inputs'],r);policy=i.json('operational_source_compatibility');v=m._proof_bundle('review',refs,i,policy,r);r.finish();checks.append({'name':'genuine full fixed nested concrete-policy proof bundle and original finish','passed':True,'bytes':r.total,'decision':v['decision']})
for key in ['review_proof','review_machine','review_manifest','review_report']:
 for mutation in ['null','wronghash']:
  x=copy.deepcopy(refs)
  if mutation=='null':x[key]=None
  else:x[key]['sha256']='0'*64
  rr=m.Reader();ii=m.Inputs(CAP,e['inputs'],rr)
  try:m._proof_bundle('review',x,ii,policy,rr)
  except m.Unavailable as error:checks.append({'name':key+'/'+mutation,'refused':True,'reason':str(error)})
  else:raise AssertionError((key,mutation))
r=m.Reader();i=m.Inputs(CAP,e['inputs'],r)
try:m._proof_bundle('recovery',refs,i,policy,r)
except m.Unavailable as error:checks.append({'name':'actual uninstalled recovery machine unavailable; no fabricated proof','refused':True,'reason':str(error)})
else:raise AssertionError('missing actual recovery accepted')
# Exact path cache semantics: two different paths containing the same c5 body
# remain separate; repeats of one path consume no additional first-read bytes.
p1=CAP/e['inputs']['operational_source_compatibility_recovery']['path'];p2=Path(refs['recovery_proof']['path']);r=m.Reader();b=r.read(p1);a=r.total;assert r.read(p1)==b and r.total==a;assert r.read(p2)==b and r.total==2*a;r.finish();assert r.total==4*a;checks.append({'name':'samepath coalescence only, distinct identical c5 paths stay separately charged','passed':True,'bytes':r.total})
(H/'CONTROLS01.json').write_text(json.dumps({'checks':checks,'count':len(checks),'no_actual_Admission_or_fake_handle':True,'no_public_preflight_or_validate_preclaim':True},indent=2)+'\n');print(json.dumps({'controls':len(checks),'actual_known_policy_bundle_bytes':checks[0]['bytes']}))
