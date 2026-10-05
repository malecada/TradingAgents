from pathlib import Path
import json,hashlib,os,sys,stat
H=Path(__file__).resolve().parent;B=H.parent;F=B/'financial-wrapper-compatibility-baseline-flat-root02-2026-10-05';sha=lambda b:hashlib.sha256(b).hexdigest()
pins={'ROOT_BASELINE_FLAT02_EXIT.json':'9c3a1a9431db91016e92bc58784f566de1e1f9ebabd647e7705d575264040909','ROOT_TOOL_EXIT_FLAT02.json':'cef62671505d84f2dada39be67b9f937ab03012ee7e0e006212c91a4e7dfaa21','BUNDLE_FLAT02_RECOVERY01.json':'e56d13dcedf5c125d4b0317a32ea6e34115a62e634c6457d226e5dd727dcee0a','watch01.py':'bdeacaadc053e615245b3e2175089842708719448ec7da970d981e5dc077ca18','utilities/owned_io.py':'09d1fbcc03f2c9303db95f34ca6c07ddb47bfdb49b35452f4cb6829a5d667aeb'}
for n,h in pins.items():assert sha((F/n).read_bytes())==h
get=lambda n:json.loads((F/n).read_bytes());tool=get('ROOT_TOOL_EXIT_FLAT02.json');outer=get('ROOT_BASELINE_FLAT02_EXIT.json');inner=get('BUNDLE_FLAT02_RECOVERY01.json');spawn=get('ROOT_BASELINE_FLAT02_SPAWN.json');intent=get('ROOT_BASELINE_FLAT02_INTENT.json');innintent=get('BUNDLE_FLAT02_INTENT01.json')
assert tool['actual_child_start_ticks']==spawn['start_ticks']==21840304
assert tool['recorded_parent_child_absent']==[intent['parent_pid'],spawn['pid']]==[1172171,1172174]
assert tool['original_parent_exit_field'] is outer['actual_parent_exit'] is None
assert tool['actual_exit']==outer['child_exit']==0 and outer['cleanup_failures']==[]
assert tool['session_id']==87078 and tool['start_chunk']=='270020' and tool['completion_chunk']=='1affab'
assert innintent=={'new_claim':False,'request_sha256':'f26bbe693932d614491280e223e51beb4dc5dcad330d80c7b258f8da8a79ccbc'}
assert len(outer['observations'])==10 and len(inner['observations'])==14
for p in tool['recorded_parent_child_absent']:assert not Path('/proc',str(p)).exists()
try:os.killpg(spawn['pid'],0)
except ProcessLookupError:pass
else:raise AssertionError('actual child group remains')
sys.path.insert(0,str(F/'utilities'));sys.path.insert(0,str(F));import watch01 as W
sample=W.census(F);v=os.statvfs(F);free=v.f_bavail*v.f_frsize;assert free>=10*1024**3
result={'schema_version':1,'actual_root_exit':0,'original_parent_exit':None,'actual_child_exit':0,'cleanup_failures':[],'actual_child_start_ticks':spawn['start_ticks'],'current_parent_child_pids_absent':tool['recorded_parent_child_absent'],'current_known_child_process_group_absent':True,'outer_samples':len(outer['observations']),'inner_samples':len(inner['observations']),'outer_elapsed_seconds':outer['elapsed_seconds'],'outer_max_sampled_logical_bytes':max(r['logical_bytes'] for r in outer['observations']),'outer_max_sampled_allocated_bytes':max(r['allocated_bytes'] for r in outer['observations']),'current_whole_root_sample':sample,'current_free_bytes':free,'historical_parent_process_group':None,'historical_native_cgroup_path':None,'numerical_authority':False}
with (H/'TERMINAL_READBACK01.json').open('x') as f:json.dump(result,f,sort_keys=True,separators=(',',':'));f.write('\n')
print(json.dumps(result))
