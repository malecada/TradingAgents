"""Focused synthetic metadata seams; no real draft, arrays or numerical imports."""
import copy,hashlib,importlib.util,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def audit(event,args):
    if event.startswith(('socket.','subprocess.')):raise RuntimeError('offline only')
    if event=='import' and args[0].split('.')[0] in {'numpy','torch','pandas','scipy','tradingagents'}:raise RuntimeError('scientific package import prohibited')
sys.addaudithook(audit)
spec=importlib.util.spec_from_file_location('packed_successor',HERE/'successor02.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class Check(unittest.TestCase):
    def test_pins_and_pure_import_injection(self):
        deps=json.loads((HERE/'DEPENDENCIES02.json').read_text())
        for name,pin in deps.items():
            self.assertEqual(hashlib.sha256((s.ROOT/pin['path']).read_bytes()).hexdigest(),pin['sha256'])
            module=s.load(name);self.assertEqual(Path(module.__file__),s.ROOT/pin['path'])
        controls=s.load('controls');self.assertEqual(controls.read_capacity(2950,s.load('read_capacity').POLICY)['logical_bytes'],3939492)
        self.assertEqual(controls.capacity(s.HISTORY,625996)['control_bytes'],3306307456)
        self.assertFalse(hasattr(s,'generate'))
    def synthetic_inventory(self,packed):
        c=s.load('controls');select=s.load('selected');M=8192;Q=3;R=16;G=160;ordinary=8*(1+R)
        kinds=select.kind_alloc(2);allow={k:{key:value for key,value in v.items() if key!='chunk_bytes'} for k,v in kinds.items()}
        attempts=7*sum(v['max_chunks'] for v in kinds.values());ops=7*sum(v['max_operations'] for v in kinds.values())
        graphs={w:{'rows':2,'tail_part_bytes':kinds['score-tail-f64']['chunk_bytes'],'output_part_bytes':kinds['mcm-output-f32']['chunk_bytes'],'allowances':copy.deepcopy(allow),'count_evidence_sha256':'0'*64} for w in c.WEEKS}
        selection=s.load('read_capacity').POLICY
        read=s.load('read_capacity').capacity(Q,selection if packed else None)['logical_bytes'];stage=read+40*G+8*M;writer=(7*Q+8)*M
        archive={'max_stage_verifications':R,'max_writer_metadata_bytes':writer,'max_read_metadata_bytes':read,'max_stage_bytes':stage,'max_workflow_metadata_bytes':(4+3*ordinary+8)*M+8*(writer+8*M+R*stage)}
        if packed:archive['read_controls']=selection
        history=s.load('history').capacity(s.HISTORY,1000)
        residual={k:{'logical_bytes':5*1024**2,'regular_files':5,'directories':1,'max_file_bytes':4*1024**2,'additional_scratch_bytes':0,'scratch_files':0,'scratch_max_file_bytes':0,'evidence_sha256':'1'*64,'bound_basis':'INVENTED SYNTHETIC TEST DECLARATION ONLY'} for k in c.REQUIRED}
        root=str(HERE.resolve())
        return {'schema_version':1,'graphs':graphs,'chunk_cells':65536,'typed_control_bytes':(3*ops+attempts)*M,'stage':{'max_events':Q*49152,'chunk_events':49152,'max_total_checkpoints':G},'archive':archive,'transport':{'max_commands':1000,'max_payload_bytes':1,'max_diagnostic_bytes':history['diagnostic_bytes'],'max_control_bytes':history['control_bytes'],'control_history':s.HISTORY},'residual_domains':residual,'filesystem':{'allocation_unit_bytes':4096,'per_regular_inode_overhead_bytes':512,'per_directory_allocated_bytes':4096,'extra_allocated_bytes':16777216,'extra_entries':256,'max_native_file_bytes':1073741824,'evidence_sha256':'2'*64},'baseline':{'logical_bytes':0,'allocated_bytes':0,'entries':0,'evidence_sha256':'3'*64},'storage_budget':{'schema_version':2,'kind':'real-pilot-writable-union','authority_root':root,'experiment':c.EXPERIMENT,'roots':[root+'/research_artifacts',root+'/research_runs/'+c.EXPERIMENT],'shared_files':[root+'/research_runs/.lock'],'limits':{'max_logical_bytes':16*1024**3,'max_allocated_bytes':20*1024**3,'max_entries':1000000,'max_depth':64,'max_scan_seconds':5}}}
    def test_actual_calculator_packed_and_legacy_synthetic(self):
        c=s.load('controls');packed=self.synthetic_inventory(True);legacy=self.synthetic_inventory(False)
        new=c.calculate(packed);old=c.calculate(legacy)
        key='archive_ledger_writer_reads';self.assertLess(new['categories'][key]['logical_bytes'],old['categories'][key]['logical_bytes']);self.assertLess(new['categories'][key]['regular_files'],old['categories'][key]['regular_files'])
        for k in set(new['categories'])-{key}:self.assertEqual(new['categories'][k],old['categories'][k])
        bad=copy.deepcopy(packed);bad['archive']['max_read_metadata_bytes']-=1
        with self.assertRaisesRegex(ValueError,'underfunded'):c.calculate(bad)
        bad=copy.deepcopy(packed);bad['archive']['read_controls']['shard_bytes']=4194304.0
        with self.assertRaisesRegex(ValueError,'exact packed'):c.calculate(bad)
    def test_exact_handoff_propagates_both_selectors(self):
        # Stub already-reviewed IO/build boundaries only; execute the exact adopted handoff.
        c=s.load('controls');inventory=self.synthetic_inventory(True);captured={};roles=dict(pilot='pilot',population='population',job='job',producer_plan='plan',dictionary='dictionary',compact='compact',archive='archive',output='output')
        templates={k:{} for k in roles};templates['compact']={'stage_policy':{'score_chunk_cells':65536,'log':inventory['stage'],'schedule':{'max_total_checkpoints':160}}}
        templates['job']={'resources':{'storage_budget':inventory['storage_budget'],'native_unit_limits':{'file_size_bytes':1073741824}}};templates['pilot']={'max_checkpoint_bytes':4194304};templates['archive']=inventory['archive']
        graphs={w:{'rows':2,'node_count':{'sha256':'0'*64}} for w in c.WEEKS}
        def check_ref(root,ref):
            if ref is None:raise ValueError('synthetic baseline evidence missing')
        builder=types.SimpleNamespace(WEEKS=c.WEEKS,graphs=lambda root,gs:graphs,metadata=lambda root,ref:templates[ref],ref_path=check_ref,build=lambda root,spec:{'status':'SYNTHETIC_CAPTURE','spec':spec})
        def calculate(v):captured['inventory']=v;return {'builder03_physical_fragment':{}}
        dependencies={'builder':builder,'residuals':types.SimpleNamespace(resolve=lambda *a,**k:{'residual_domains':inventory['residual_domains']}),'controls':types.SimpleNamespace(calculate=calculate)}
        original=s.load
        def selected(name):return dependencies[name] if name in dependencies else original(name)
        draft={'status':'DRAFT_NOT_RELEASED','graphs':{w:{} for w in c.WEEKS},'protocol':{'references':{v:k for k,v in roles.items()},'template_roles':roles,'typed_input_role':'typed','typed_allocations':{'chunk_cells':65536,'max_control_bytes':inventory['typed_control_bytes'],'by_week':{w:s.load('selected').kind_alloc(2) for w in c.WEEKS}},'transport_limits':inventory['transport'],'physical_baseline':{'evidence':{'sha256':'3'*64},'logical_bytes':0,'allocated_bytes':0,'entries':0},'filesystem':inventory['filesystem'],'runtime_reservation':{'synthetic':True},'lifecycle_reservation':{'synthetic':True}}}
        with patch.object(s,'load',selected):
            result=s.prepare(HERE,draft)
            self.assertEqual(captured['inventory']['archive']['read_controls'],inventory['archive']['read_controls']);self.assertEqual(captured['inventory']['transport']['control_history'],s.HISTORY)
            self.assertFalse(result['independent_approval']);self.assertEqual(result['status'],'DRAFT_NOT_REGISTERED_NOT_ADMITTED')
            draft['protocol']['physical_baseline']['evidence']=None
            with self.assertRaisesRegex(ValueError,'baseline evidence missing'):s.prepare(HERE,draft)

if __name__=='__main__':unittest.main(verbosity=2)
