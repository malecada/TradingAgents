"""Actual source-selector fragments; metadata namespace substitutes, no authority."""
import ast,hashlib,json,os,sys
from pathlib import Path
from types import SimpleNamespace as NS
from discover_source01 import HERE,ROOT,OLD,sha
from source_symbols01 import Symbols
inv=json.loads((HERE/'source_inventory02.json').read_bytes());rows={r['target']:r for r in inv['source_inventory']};world=Symbols(rows);required=world.module('tradingagents/research/onchain_replication/compact_native_producer.py').required_sources()
old=os.environ.get('PREDECESSOR')=='1';index=json.loads((OLD/'source_inventory01.json').read_bytes()) if old else inv
selected={r['target']:r['sha256'] for r in index['source_inventory']};root=(OLD if old else HERE)/'source-bodies';pkg=root/'tradingagents/research/onchain_replication'
def require(v,m):
 if not v:raise ValueError(m)
def extracted(path,name,env):
 fn=next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'),env);return env[name]
# Execute the actual source-hash loop from selected(), not a map-self comparison.
fn=next(n for n in ast.parse((pkg/'compact_native_producer.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='selected')
loop=next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.iter,ast.Call) and isinstance(n.iter.func,ast.Name) and n.iter.func.id=='required_sources')
ad=NS(root=root,experiment={'source_files':selected});run=NS(admission=ad)
namespace={'run':run,'ROOT':root,'required_sources':lambda:required,'require':require,'file_hash':lambda p:sha(p.read_bytes())}
exec(compile(ast.Module(body=[loop],type_ignores=[]),'actual-selected-source-loop','exec'),namespace)
# Genuine scientific two/three-pin source functions, with metadata-only ancestry.
constants={}
for name,key in [('compact_dictionary','KERNEL'),('compact_samples','READER'),('compact_mcm','KERNEL')]:constants[name]=world.module('tradingagents/research/onchain_replication/'+name+'.py').get(key)
proof=NS(owner=NS(bound=NS(_run=run)));dictionary=NS(_proof=proof)
denv={'ROOT':root,'KERNEL':constants['compact_dictionary'],'compact_samples':NS(READER=constants['compact_samples']),'require':require,'file_hash':lambda p:sha(p.read_bytes())}
dict_sources=extracted(pkg/'compact_dictionary.py','_sources',denv)
menv={'ROOT':root,'KERNEL':constants['compact_mcm'],'compact_dictionary':NS(_sources=dict_sources),'require':require,'file_hash':lambda p:sha(p.read_bytes()),'_imported':lambda d:False}
ms=extracted(pkg/'compact_mcm.py','_sources',menv)(dictionary);ds=dict_sources(proof);evidence=extracted(pkg/'compact_mcm.py','_source_evidence',menv)(dictionary,ms)
assert len(ds)==2 and len(ms)==3 and evidence==ms and set(ms)<=required
serialize=extracted(pkg/'score_batches.py','_json',{'json':json,'META_LIMIT':8192,'_require':require})
assert len(serialize(ds))==338 and len(serialize(ms))==504
# Actual _prepare start-record AST with finite scalar placeholders of the exact
# fixed-width/hash/name types. This is byte arithmetic, NOT a produced record.
start=next(n for n in ast.walk(ast.parse((pkg/'compact_mcm.py').read_bytes())) if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='start')
h='f'*64;owner=NS(identity=h,required=tuple(range(19)));input_name='compact_mcm';output_input='compact_mcm_output';ad.inputs={n:{'sha256':h} for n in (input_name,output_input)}
context={'owner':owner,'dictionary':NS(receipt_sha256=h),'d':NS(identity=h),'key':h,'expected':{k:h for k in ('graph','node_order','dictionary','ordered_motifs','matching','workflow')},'rows':4,'motifs':32,'pairs':128,'input_name':input_name,'run':run,'output_input':output_input,'io':NS(META_LIMIT=8192),'output_reserved':1048576,'sources':ms,'_source_evidence':lambda d,s:s}
exec(compile(ast.Module(body=[start],type_ignores=[]),'actual-MCM-start-record','exec'),context)
start_bytes=len(serialize(context['start']));assert start_bytes<=8192
result={'status':'source-only-selection-pass','actual_required_sources':len(required),'scientific_dictionary_pins':ds,'scientific_MCM_pins':ms,'dictionary_source_map_bytes':len(serialize(ds)),'MCM_source_map_bytes':len(serialize(ms)),'actual_start_constructor_fixed_scalar_fixture_bytes':start_bytes,'metadata_limit':8192,'complete_record_and_real_run_not_proved':True,'numeric_or_authority_imports':False}
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
print(json.dumps(result,indent=2))
