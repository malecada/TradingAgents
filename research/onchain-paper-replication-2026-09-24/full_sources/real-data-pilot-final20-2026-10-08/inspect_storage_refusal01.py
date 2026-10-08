"""Read-only diagnosis of actual metadata refusal; no success coercion or run."""
import datetime,hashlib,json,os,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent;F=HERE.parent
HELP=F/'real-data-pilot-fixed20-metadata-successor01-2026-10-08/successor03.py'
mod=types.ModuleType('pilot20_metadata_refusal');mod.__file__=str(HELP)
exec(compile(HELP.read_bytes(),str(HELP),'exec'),vars(mod))
draft=json.loads((HERE/'INPUT_DRAFT02.json').read_bytes())
try:mod.prepare(ROOT,draft)
except ValueError as original:
 assert str(original)=='aggregate writable scope underfunded: logical_bytes'
 tb=original.__traceback__;matching=[]
 while tb is not None:
  if tb.tb_frame.f_code.co_name=='calculate' and tb.tb_frame.f_code.co_filename.endswith('/candidate/controls01.py'):
   matching.append(dict(tb.tb_frame.f_locals))
  tb=tb.tb_next
 assert len(matching)==1;v=matching[0]
 fs=os.statvfs(ROOT);free=fs.f_bavail*fs.f_frsize;floor=10*1024**3
 growth=v['logical']+v['overhead']
 result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ACTUAL_METADATA_STORAGE_REFUSAL','failure':str(original),'current_budget':v['budget'],'conditional_required_totals':v['totals'],'conditional_new_logical_bytes':v['logical'],'conditional_allocation_overhead_bytes':v['overhead'],'conditional_allocated_growth_bytes':growth,'categories':v['categories'],'observed_disk_free_bytes':free,'disk_floor_bytes':floor,'conditional_minimum_free_bytes':growth+floor,'conditional_space_gap_bytes':max(0,growth+floor-free),'inputs_sha256':hashlib.sha256((HERE/'INPUT_DRAFT02.json').read_bytes()).hexdigest(),'helper_sha256':hashlib.sha256(HELP.read_bytes()).hexdigest(),'qualification':'Original pure metadata refusal retained. Trace locals expose computed conditional bounds without weakening/patching predicates or publishing successful preparation. Snapshot disk free, modeled slots/blocks and declarations are not hard quotas or measured future capacity. No metadata success, transport binding, native launch, claim or allowance adoption.'}
 with (HERE/'ACTUAL_STORAGE_REFUSAL01.json').open('x') as out:json.dump(result,out,sort_keys=True,indent=2);out.write('\n')
 print(json.dumps({k:result[k] for k in ('status','conditional_required_totals','conditional_allocated_growth_bytes','observed_disk_free_bytes','conditional_minimum_free_bytes','conditional_space_gap_bytes')}))
else:raise RuntimeError('Expected original refusal absent; no outcome inferred')
