"""Explicit mocked Binding/readback integration; no real claims or NumPy imports."""
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType,SimpleNamespace
import sys
import unittest
from unittest.mock import patch
from test_candidate01 import Candidate,fixture,canonical,sha

class BindingTests(Candidate):
    @contextmanager
    def configured(self):
        m=self.m;p,blobs=fixture();root=Path(__file__).resolve().parents[4]
        controls=canonical(p);descriptor={'original_dictionary_import':{'input':'control','sha256':sha(controls)},'required_graphs':p['required_graphs'],'configs':{'matching':{'alpha':0.5}}}
        item={'original_dictionary_input':'control','descriptor':descriptor}
        selected=item|{'plan_input':'plan'}
        blobs=blobs|{'control':controls,'job':canonical({'payload':{'representation_jobs':{'r':selected}}}),'plan':canonical({'producers':{'p':item}})}
        inputs={k:{'path':k+'.json','sha256':sha(v)} for k,v in blobs.items()}
        source=Path(m.__file__).resolve();ad=SimpleNamespace(root=root,inputs=inputs,experiment={'source_files':{str(source.relative_to(root)):sha(source.read_bytes())}})
        run=SimpleNamespace(admission=ad,_claim_sha256='c'*64)
        class Binding:
            def __init__(self):
                self._run=run;self.record={'representation':'r','producer':'p','workflow_identity':sha(canonical(descriptor))};self.context={};self.limits={};self.active=True
            def lease(self):
                if not self.active:raise ValueError('terminal binding')
            def check(self):self.lease()
        bound=Binding();pkg=ModuleType('tradingagents.research.onchain_replication');owner=ModuleType(pkg.__name__+'.matching_owner');owner.Binding=Binding;pkg.matching_owner=owner
        prov=ModuleType(pkg.__name__+'.provenance');prov.thaw=lambda x:x;prov.file_hash=lambda x:sha(Path(x).read_bytes())
        mods={pkg.__name__:pkg,owner.__name__:owner,prov.__name__:prov}
        with patch.dict(sys.modules,mods),patch.object(m,'_read_registered',lambda run,name:blobs[name]):
            yield m,p,blobs,bound
    def test_public_selection_and_revocation(self):
        with self.configured() as (m,p,b,bound):
            cap=m.admit(bound,input_name='control',job_input='job');self.assertEqual(cap.check().representative_indices,(2,0));bound.active=False
            with self.assertRaises(ValueError):cap.check()
    def test_changed_original_bound_record_refused(self):
        with self.configured() as (m,p,b,bound):
            cap=m.admit(bound,input_name='control',job_input='job');bound.record['foreign']='changed'
            with self.assertRaises(ValueError):cap.check()
    def test_wrong_required_population_refused(self):
        with self.configured() as (m,p,b,bound):
            p['required_graphs']=['d'*64];b['control']=canonical(p);bound._run.admission.inputs['control']['sha256']=sha(b['control'])
            # Keep both selected descriptor/control hash joins coherent, but give
            # the control a different graph denominator than the descriptor.
            job=__import__('json').loads(b['job']);plan=__import__('json').loads(b['plan'])
            desc=job['payload']['representation_jobs']['r']['descriptor'];desc['original_dictionary_import']['sha256']=sha(b['control'])
            plan['producers']['p']['descriptor']=desc;bound.record['workflow_identity']=sha(canonical(desc));b['job']=canonical(job);b['plan']=canonical(plan)
            with self.assertRaises(ValueError):m.admit(bound,input_name='control',job_input='job')

if __name__=='__main__':unittest.main()
