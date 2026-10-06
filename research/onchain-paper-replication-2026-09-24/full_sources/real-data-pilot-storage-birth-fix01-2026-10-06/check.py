"""Tiny temporary trees only; deterministic scan-boundary race injection."""
import hashlib,importlib.util,json,os,tempfile,time
from pathlib import Path
from unittest.mock import patch
D=Path(__file__).resolve().parent

def module(which):
 spec=importlib.util.spec_from_file_location('tradingagents.research.onchain_replication.birth_'+which,D/which/'real_pilot_storage.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
baseline=module('baseline');candidate=module('candidate');cases=[]

def run(m,mode):
 with tempfile.TemporaryDirectory(dir=D) as tmp:
  root=Path(tmp);art=root/'research_artifacts';art.mkdir();parent=root/'research_runs';parent.mkdir();(parent/'.lock').touch()
  target=parent/m.EXPERIMENT
  limits=dict(max_allocated_bytes=2**20,max_logical_bytes=64,max_entries=100,max_depth=8,max_scan_seconds=1)
  budget=dict(schema_version=2,kind=m.KIND,authority_root=str(root),experiment=m.EXPERIMENT,roots=[str(art),str(target)],shared_files=[str(parent/'.lock')],limits=limits)
  union=m.WritableUnion(budget,root);original=m.StorageWatch._check;passes=[];begins=[];clock=[time.monotonic()]
  def injected(w,begin,history):
   begins.append(begin)
   result=original(w,begin,history)
   if w.root==art:
    passes.append(True)
    if len(passes)==1:
     target.mkdir();(target/'payload').write_bytes(b'x'*(65 if mode=='size' else 13))
     if mode=='link':(target/'payload').unlink();(target/'payload').symlink_to(root/'absent')
     if mode=='residual':(target/'payload').unlink();(target/'payload').write_bytes(b'x'*33)
    elif mode=='rebirth':
     target.rename(parent/'retained-original');target.mkdir()
    elif mode=='deletion':
     (target/'payload').unlink();target.rmdir()
    elif mode=='lock':
     (parent/'.lock').rename(parent/'old-lock');(parent/'.lock').touch()
    elif mode=='parent':
     parent.rename(root/'retained-parent');parent.mkdir();(parent/'.lock').touch()
    if mode=='time':clock[0]+=.6
   return result
  if mode=='residual':m.RESIDUAL_POLICY['training_and_lifecycle']=dict(m.RESIDUAL_POLICY['training_and_lifecycle'],logical_bytes=32)
  try:
   with patch.object(m.StorageWatch,'_check',injected),patch.object(time,'monotonic',lambda:clock[0]):
    observed=union.check()
  except (ValueError,FileNotFoundError) as error:
   return {'mode':mode,'accepted':False,'reason':str(error),'artifact_scans':len(passes),'single_begin':len(set(begins))==1}
  finally:
   if mode=='residual':m.RESIDUAL_POLICY['training_and_lifecycle']=dict(m.RESIDUAL_POLICY['training_and_lifecycle'],logical_bytes=32*1024**2)
  assert observed['logical_file_bytes']==13
  assert observed['residual_domains']['training_and_lifecycle']['logical_file_bytes']==13
  assert any(row.get('root')==str(target) and row.get('logical_file_bytes')==13 for row in observed['roots'])
  assert union.target_identity==(target.stat().st_dev,target.stat().st_ino)
  return {'mode':mode,'accepted':True,'logical_file_bytes':observed['logical_file_bytes'],'artifact_scans':len(passes),'single_begin':len(set(begins))==1}
red=run(baseline,'birth');assert not red['accepted'] and 'born during scan' in red['reason'];cases.append(red)
green=run(candidate,'birth');assert green['accepted'] and green['artifact_scans']==2 and green['single_begin'];cases.append(green)
for mode in ('rebirth','deletion','link','size','residual','lock','parent','time'):
 row=run(candidate,mode);assert not row['accepted'],row;assert row['artifact_scans']<=2 and row['single_begin'];cases.append(row)
print(json.dumps({'checks':cases,'count':len(cases),'scope':'tiny temporary trees only; no empirical reads or claims'},indent=2))
