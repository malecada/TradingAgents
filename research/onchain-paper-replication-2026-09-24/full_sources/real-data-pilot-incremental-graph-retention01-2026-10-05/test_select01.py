"""Synthetic metadata only; placeholder files are not scientific arrays/SQLite."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timedelta
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('selector',HERE/'select01.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ID='eth-paper-real-pilot-graph-20220502-20261005-01'
def fixture(root):
    def put(p,v):
        p=root/p;p.parent.mkdir(parents=True,exist_ok=True);b=json.dumps(v,sort_keys=True).encode();p.write_bytes(b);return {'path':str(p.relative_to(root)),'sha256':m.sha(b),'bytes':len(b)}
    inputs={};members=[]
    for i in range(7):
        d=(datetime(2022,5,2)+timedelta(days=i)).date().isoformat();e=(datetime(2022,5,3)+timedelta(days=i)).date().isoformat();r=put('inputs/day'+str(i)+'.json',{'synthetic':i});inputs['daily_map_'+str(i).zfill(2)]={'path':r['path'],'sha256':r['sha256']};members.append({'path':str(root/r['path']),'sha256':r['sha256'],'start_utc':d+'T00:00:00Z','end_utc':e+'T00:00:00Z','expected_rows':1})
    src={'status':'complete','expected_members':7,'expected_rows':7,'start_utc':'2022-05-02T00:00:00Z','end_utc':'2022-05-09T00:00:00Z','members':members}
    plan={'schema_version':1,'asset':'ETH','mode':'build','source_inputs':['weekly_source'],'expected_weeks':['2022-05-02T00:00:00Z'],'coverage':[['2022-05-02T00:00:00Z','2022-05-09T00:00:00Z']]}
    for role,value in [('weekly_source',src),('graph_plan',plan),('execution_job',{'kind':'graphs','payload':{'plan_input':'graph_plan'}})]:
        r=put('inputs/'+role+'.json',value);inputs[role]={'path':r['path'],'sha256':r['sha256']}
    ex={'inputs':inputs,'cells':['source-000000','graph-2022-05-02'],'source_files':{'synthetic.py':'a'*64}}
    gate=put('gate.json',{'experiments':{ID:ex}});claim={'experiment_id':ID,'experiment':ex,'source':'b'*40,'registration':'gate.json','registration_sha256':gate['sha256']}
    run='research_runs/'+ID+'/';ch=put(run+'claim.json',claim)['sha256'];base=m.PREFIX+ID+'/';index={}
    def art(p,v):
        ref=put(p,v);index[p]={'bytes':ref['bytes'],'sha256':ref['sha256']};return ref['sha256']
    arrays={}
    for name in ('node_ids','node_features','edge_index','edge_features','edge_aggregates'):
        rel=base+'graph-2022-05-02/'+name+'.npy';p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'placeholder');index[rel]={'bytes':11,'sha256':m.sha(b'placeholder')};arrays[name]={'path':name+'.npy',**index[rel]}
    mp=base+'graph-2022-05-02/manifest.json';mh=art(mp,{'arrays':arrays,'metadata':{'asset':'ETH','start_utc':src['start_utc'],'end_utc':src['end_utc'],'source_hashes':[x['sha256'] for x in members]}})
    coverage_members=[{k:x[k] for k in ('start_utc','end_utc','sha256','expected_rows')}|{'source_input':'weekly_source','source_manifest_sha256':inputs['weekly_source']['sha256']} for x in members]
    ph=inputs['graph_plan']['sha256'];cp=base+'graph-2022-05-02/coverage.json';cov={'schema_version':1,'claim_sha256':ch,'plan_sha256':ph,'graph_manifest_sha256':mh,'week':src['start_utc'],'members':coverage_members};coh=art(cp,cov)
    graph={'id':'graph-2022-05-02','status':'complete','manifest_path':mp,'manifest_sha256':mh,'coverage_path':cp,'coverage_sha256':coh,'source_hashes':[x['sha256'] for x in members]}
    cells=[{'id':'source-000000','status':'complete','rows':7,'manifest_sha256':inputs['weekly_source']['sha256']},graph]
    art(base+'graph-2022-05-02.json',graph);art(base+'intent.json',{'claim_sha256':ch,'source_commit':claim['source'],'plan_sha256':ph,'cells':ex['cells']});art(base+'source-coverage.json',{'plan_sha256':ph,'members':coverage_members})
    summary={'reason':None,'workspace':base+'aggregation','plan_sha256':ph,'expected_weeks':plan['expected_weeks'],'graphs':{src['start_utc']:{k:v for k,v in graph.items() if k not in ('id','status')}}};art(base+'result.json',summary)
    rel=base+'aggregation/ledger.sqlite';p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'placeholder');index[rel]={'bytes':11,'sha256':m.sha(b'placeholder')}
    out={name:put(run+'outputs/'+name,value)['sha256'] for name,value in [('artifact-index.json',index),('cell-ledger.json',cells),('source-summary.json',summary)]}
    terminal={'status':'complete','experiment_id':ID,'claim_sha256':ch,'source':claim['source'],'registration_sha256':gate['sha256'],'cells':cells,'cell_count':2,'unavailable_count':0,'output_sha256':out};put(run+'complete.json',terminal)
    owner={'experiment':ID,'source_commit':claim['source'],'monitor_pid':999999999};gb='research_artifacts/onchain-paper-replication-2026-09-24/runs/'+ID+'/';put(gb+'owner.json',owner);put(gb+'guard/final.json',{'phase':'complete','child_exit_code':0,'cleanup_verified':True,'limit_reason':None,'owner_identity':owner,'cgroup':str(root/'absent-cgroup')})
    return put,run,base
class Checks(unittest.TestCase):
    def test_complete_and_metadata_tamper(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp,patch.object(m.subprocess,'check_output',return_value=b''):
            root=Path(tmp);put,run,base=fixture(root);result=m.select(root,ID)
            self.assertEqual(len(result['files']),1);self.assertEqual(result['status'],'DRAFT');self.assertFalse(result['launch_authority']);self.assertFalse(result['ledger_body_read'])
            put(run+'outputs/artifact-index.json',{})
            with self.assertRaisesRegex(ValueError,'metadata hash'):m.select(root,ID)
    def test_failed_active_and_sqlite_transient_refuse(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp,patch.object(m.subprocess,'check_output',return_value=b''):
            root=Path(tmp);put,run,base=fixture(root);f=root/run/'failed.json';f.write_text('{}')
            with self.assertRaisesRegex(ValueError,'FAILED'):m.select(root,ID)
            f.unlink();put('research_runs/active/claim.json',{'experiment':{'inputs':{'producer':{'path':base+'aggregation'}}}})
            with self.assertRaisesRegex(ValueError,'active consumer'):m.select(root,ID)
            (root/'research_runs/active/claim.json').unlink();(root/(base+'aggregation/ledger.sqlite-wal')).write_text('')
            with self.assertRaisesRegex(ValueError,'transient'):m.select(root,ID)
    def test_guard_and_component_refusal(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp,patch.object(m.subprocess,'check_output',return_value=b''):
            root=Path(tmp);put,run,base=fixture(root)
            gp=root/'research_artifacts/onchain-paper-replication-2026-09-24/runs'/ID/'guard/final.json';g=json.loads(gp.read_text());g['child_exit_code']=1;gp.write_text(json.dumps(g))
            with self.assertRaisesRegex(ValueError,'guard incomplete'):m.select(root,ID)
            g['child_exit_code']=0;gp.write_text(json.dumps(g));t=root/run/'complete.json';v=json.loads(t.read_text());v['cells'][1]['status']='unavailable';t.write_text(json.dumps(v))
            with self.assertRaisesRegex(ValueError,'component denominator'):m.select(root,ID)
    def test_protected_and_not_yet_produced(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            for old in ('eth-paper-resource-pilot-20260924-02','eth-paper-real-pilot-graph-20220613-20261005-01'):
                with self.assertRaisesRegex(ValueError,'legacy/dictionary/June13'):m.select(tmp,old)
            with self.assertRaises(FileNotFoundError):m.select(tmp,ID)
if __name__=='__main__':unittest.main()
