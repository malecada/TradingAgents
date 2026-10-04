from pathlib import Path
import types,json,hashlib,stat,ast
H=Path(__file__).resolve().parent;M=types.ModuleType('local_opaque_copier');M.__file__=str(H/'copy_layout01.py');exec(compile((H/'copy_layout01.py').read_bytes(),M.__file__,'exec'),M.__dict__)
reader=M.PC.Reader();raw=reader.read(H/'INPUTS01.json');assert M.h(raw)==M.INPUTS_SHA;spec=json.loads(raw);out=H/'owned-complete-metadata03';assert not M.OUTPUT.exists();result=M.copy_layout(spec,out,reader);assert not M.OUTPUT.exists();assert len(spec['rows'])==57 and result['receipt_bodies']==38
# This is only an owned local byte-copy control, not the fixed Root entry.
manifest=json.loads((out/'concrete-policy/MANIFEST01.json').read_bytes());ref={'path':str(out/'concrete-policy/MANIFEST01.json'),'sha256':M.h((out/'concrete-policy/MANIFEST01.json').read_bytes())};r2=M.PC.Reader()
for n in ['MACHINE01.json','REPORT01.md','REVIEW_PROOF01.json']:
 p=out/'concrete-policy'/n;M.PC._sealed(manifest,ref,{'path':str(p),'sha256':M.h(p.read_bytes())},r2)
r2.finish();result['fixed_Root_entry_called']=False;result['local_control_only']=True;result['original_concrete_policy_seal_joins']=3;result['policy_component_reader_bytes']=r2.total;result['source_sha256']=M.h((H/'copy_layout01.py').read_bytes());result['logical_copy_bytes']=sum(x['bytes'] for x in spec['rows']);result['draft_bytes']=(out/'DRAFT_LAYOUT01.json').stat().st_size;result['origin_map_bytes']=(out/'ORIGIN_MAP01.json').stat().st_size
(H/'FULL_CONTROLS03.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['initial_output_observation','output_observation']}))
