"""Metadata-only synthetic controls; no job import or numerical module/claim API."""
import ast,copy,hashlib,json,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sha=lambda b:hashlib.sha256(b).hexdigest()
file_hash=lambda p:sha(p.read_bytes())

def functions():
    tree=ast.parse((HERE/'job.py').read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_terminal','_resource_pilot_rows')]
    ns={'Path':Path,'json':json,'digest':sha,'file_hash':file_hash,'__package__':'tradingagents.research.onchain_replication'}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(HERE/'job.py'),'exec'),ns)
    return ns

def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))

class ObserverTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.ns=functions();self.run=self.root/'research_runs/synthetic-resource';self.out=self.run/'outputs';self.out.mkdir(parents=True)
        self.job={'kind':'compact_resource','payload':{'representation_jobs':{'one':{'real_pilot_input':'pilot'}}}}
        self.policy={'kind':'real-data-import-training-pilot-v1','schema_version':2,'outputs':{'ledger':'cell-ledger.json'},'cell_id':'cell'}
        write(self.root/'job.json',self.job);write(self.root/'pilot.json',self.policy)
        self.claim={'experiment_id':'synthetic-resource','source':'s','registration_sha256':'r','inputs':{'execution_job':{'path':'job.json','sha256':file_hash(self.root/'job.json')},'pilot':{'path':'pilot.json','sha256':file_hash(self.root/'pilot.json')}},'experiment':{'cells':['cell'],'outputs':['cell-ledger.json']}}
        write(self.run/'claim.json',self.claim);self.claimsha=file_hash(self.run/'claim.json')
        self.row={'id':'cell','status':'failed','reason':'synthetic retained failure','resource_only':True,'financial_fit_complete':False,'paper_financial_fits':0}
        write(self.out/'cell-ledger.json',[self.row]);self.seal()
    def seal(self,status='failed'):
        self.terminal={'status':status,'experiment_id':'synthetic-resource','claim_sha256':self.claimsha,'output_sha256':{p.name:file_hash(p) for p in self.out.iterdir()}}
        if status=='complete':self.terminal.update(source='s',registration_sha256='r',cells=[self.row],cell_count=1,unavailable_count=0)
        write(self.run/(status+'.json'),self.terminal)
    def recover(self):return self.ns['_resource_pilot_rows'](self.root,self.claim,self.claimsha)
    def test_failed_ledger_retained_exactly(self):self.assertEqual(self.recover(),{'cell':self.row})
    def test_complete_ledger_not_financial_completion(self):
        (self.run/'failed.json').unlink();self.row['status']='complete';self.row.pop('reason');write(self.out/'cell-ledger.json',[self.row]);self.seal('complete')
        self.assertEqual(self.recover(),{'cell':self.row})
    def test_corrupt_output_rejected(self):
        write(self.out/'cell-ledger.json',[])
        with self.assertRaisesRegex(ValueError,'output bytes differ'):self.recover()
    def test_missing_hashed_output_rejected(self):
        (self.out/'cell-ledger.json').unlink()
        with self.assertRaisesRegex(ValueError,'output bytes differ'):self.recover()
    def test_absent_unrecorded_output_not_invented(self):
        (self.out/'cell-ledger.json').unlink();self.seal();self.assertEqual(self.recover(),{})
    def test_no_terminal_not_invented(self):
        (self.run/'failed.json').unlink();self.assertEqual(self.recover(),{})
    def test_contradictory_terminal_rejected(self):
        write(self.run/'complete.json',self.terminal)
        with self.assertRaisesRegex(ValueError,'contradictory'):self.recover()
    def test_terminal_claim_hash_rejected(self):
        self.terminal['claim_sha256']='0'*64;write(self.run/'failed.json',self.terminal)
        with self.assertRaisesRegex(ValueError,'exact owner claim'):self.recover()
    def test_original_claim_object_rejected(self):
        self.claim['experiment']['cells']=['cell','extra']
        with self.assertRaisesRegex(ValueError,'original claim'):self.recover()
    def test_selected_input_mutation_rejected(self):
        write(self.root/'pilot.json',{})
        with self.assertRaisesRegex(ValueError,'registered metadata'):self.recover()
    def test_invalid_row_denominator_and_financial_fields(self):
        for field,value in [('id','other'),('status','unavailable'),('resource_only',False),('financial_fit_complete',True),('paper_financial_fits',1),('paper_financial_fits',False),('reason','')]:
            with self.subTest(field=field,value=value):
                row={**self.row,field:value};write(self.out/'cell-ledger.json',[row]);self.seal()
                with self.assertRaises(ValueError):self.recover()
        write(self.out/'cell-ledger.json',[self.row,self.row]);self.seal()
        with self.assertRaisesRegex(ValueError,'denominator'):self.recover()
    def test_nonresource_route_unchanged(self):
        self.job['kind']='fit';write(self.root/'job.json',self.job);self.claim['inputs']['execution_job']['sha256']=file_hash(self.root/'job.json')
        self.assertEqual(self.recover(),{})
    def test_changed_terminal_during_final_join_rejected(self):
        original=self.ns['_terminal']
        def changed(*args):
            result=original(*args);self.terminal['extra']='mutation';write(self.run/'failed.json',self.terminal);return result
        self.ns['_terminal']=changed
        with self.assertRaisesRegex(ValueError,'changed during recovery'):self.recover()
    def test_actual_reconstruction_merge_and_conflict(self):
        tree=ast.parse((HERE/'job.py').read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_reconcile')
        start=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='resource_rows' for t in n.targets))
        stop=next(i for i,n in enumerate(function.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='cells' for t in n.targets))
        code=compile(ast.Module(body=function.body[start:stop+1],type_ignores=[]),'actual observer reconstruction','exec')
        ns={**self.ns,'root':self.root,'claim':self.claim,'claim_path':self.run/'claim.json','recorded':{}}
        exec(code,ns);self.assertEqual(ns['cells'],[self.row])
        ns['recorded']={'cell':{'id':'cell','status':'unavailable'}}
        with self.assertRaisesRegex(ValueError,'conflicting durable resource disposition'):exec(code,ns)

    def test_actual36_readonly_red_green(self):
        run=ROOT/'research_runs/eth-paper-real-data-end-to-end-resource-20261011-36'
        base=ROOT/'research_artifacts/onchain-paper-replication-2026-09-24/runs/eth-paper-real-data-end-to-end-resource-20261011-36'
        names=[run/'claim.json',run/'failed.json',run/'outputs/cell-ledger.json',base/'postmortem-cells.json',base/'observer.json']
        before={str(p.relative_to(ROOT)):file_hash(p) for p in names}
        claim=json.loads((run/'claim.json').read_bytes());old=json.loads((base/'postmortem-cells.json').read_bytes())
        rows=self.ns['_resource_pilot_rows'](ROOT,claim,file_hash(run/'claim.json'))
        self.assertEqual(old[0]['status'],'unavailable');self.assertEqual(list(rows.values())[0]['status'],'failed')
        self.assertEqual(list(rows.values()),json.loads((run/'outputs/cell-ledger.json').read_bytes()))
        self.assertEqual(before,{str(p.relative_to(ROOT)):file_hash(p) for p in names})
        (HERE/'READONLY36_JOIN01.json').write_text(json.dumps({'status':'READONLY_DISPOSITION_REPRODUCTION_NOT_OBSERVER_REWRITE','original_observer_cells':old,'authenticated_retained_rows':list(rows.values()),'original_body_sha256_before_and_after':before,'terminal_remains':'failed'},indent=2)+'\n')

if __name__=='__main__':unittest.main(verbosity=2)
