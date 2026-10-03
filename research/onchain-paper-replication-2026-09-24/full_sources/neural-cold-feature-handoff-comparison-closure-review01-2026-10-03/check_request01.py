import sys,pathlib,json,hashlib,importlib.util,os
R=pathlib.Path('/home/malecada/master_thesis/TradingAgents-audit-fixes/research/onchain-paper-replication-2026-09-24/full_sources')
D=R/'neural-cold-feature-handoff-comparison-closure-review01-2026-10-03'
P=R/'neural-cold-feature-handoff-outcome-retention-preparation02-2026-10-03'
Q=R/'neural-cold-feature-handoff-comparison-outcome01-2026-10-03/COLLECTION_REQUEST01.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(Q.read_bytes())=='89b718215212a5291f684ef86e25a9c099f5732f185bc3eb705682f70aede5c3'
assert sha((P/'collector01.py').read_bytes())=='d3ab84766f8a0e42d1247f5620b9a331fc1975d38e6447ee192bb2b1324d0b69'
class Block:
 def find_spec(self,fullname,*args):
  if fullname.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'}: raise AssertionError('numerical import prohibited')
sys.meta_path.insert(0,Block());sys.path.insert(0,str(P))
os.environ.update(GIT_NO_LAZY_FETCH='1',GIT_NO_REPLACE_OBJECTS='1',GIT_OPTIONAL_LOCKS='0',GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='protocol.allow',GIT_CONFIG_VALUE_0='never')
spec=importlib.util.spec_from_file_location('review_collector',P/'collector01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
q=json.loads(Q.read_bytes());root,sources,raw,api=m.source_context(q)
assert len(sources)==195 and q['source']=='361339125a3f1cd57e7ba8611f5a994ae649fa0b'
dest=pathlib.Path(q['destination']);assert not os.path.lexists(dest) and dest.parent==Q.parent and dest.name=='collection01'
records={}
for phase in m.IDS:
 release=json.loads(m.reference(q['releases'][phase]));wait=json.loads(m.reference(q['wrapper_waits'][phase]));m.reference(q['parent_sources'][phase])
 assert set(wait)=={'schema_version','identity','source','wrapper_pid','wrapper_exit_code','command','request','output_root'}
 assert wait['identity']==m.IDS[phase] and wait['source']==release['source'] and wait['output_root']==q['wrappers'][phase]
 paths=m.reservation_paths(q,root,phase);assert all(p.is_dir() for p in paths.values())
 intent=json.loads((paths['parent']/'intent.json').read_bytes());child=json.loads((paths['parent']/'child.json').read_bytes());wrapper_intent=json.loads((paths['wrapper']/'intent.json').read_bytes())
 assert child['pid']==wait['wrapper_pid']==wrapper_intent['parent_pid'] and intent['request']==wait['request'] and intent['command']==wait['command']
 request=json.loads(m.reference(wait['request']));assert request['release']==q['releases'][phase] and request['capsule']==str(root) and request['phase']==phase
 command=json.loads(m.reference(intent['command_document']));assert command['argv']==wait['command'] and command['request']==wait['request']
 actual=m.authenticate_lifecycle(root,sources,phase,release)
 cleanup=m.cleanup_observation(root,phase,paths['wrapper']);assert cleanup['status']=='original-cleanup-observed'
 assert actual['status']==('complete' if phase=='materialize' else 'failed') and wait['wrapper_exit_code']==(0 if phase=='materialize' else 1)
 records[phase]={'lifecycle':actual,'cleanup':cleanup,'actual_wrapper_exit':wait['wrapper_exit_code']}
assert not any(k.split('.')[0] in {'numpy','torch','scipy','pandas','pyarrow'} for k in sys.modules)
out={'schema_version':1,'decision':'accepted','request_sha256':sha(Q.read_bytes()),'collector_sha256':sha((P/'collector01.py').read_bytes()),'source':q['source'],'scope':'One byte-only collection of both original phases; no rerun, new claim, numerical validation or success upgrade. Comparison FAILED with four missing registered outputs; collection destination absent at review. Actual collection and recovery remain unperformed by reviewer.','actual_read_only_source_context':True,'phases':records,'collection_invoked':False,'destination_reserved':False}
(D/'REQUEST_REVIEW01.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
