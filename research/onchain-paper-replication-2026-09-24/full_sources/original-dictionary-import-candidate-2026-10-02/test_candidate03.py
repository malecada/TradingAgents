"""Tiny metadata-only proof; no empirical artifacts or numerical imports."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

PATH=Path(__file__).with_name('candidate03.py')

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(x):return hashlib.sha256(x).hexdigest()

def fixture():
    cfg={'size':2,'sample_count':3,'hop_depth':1,'maximum_neighborhood_nodes':10}
    matching={'alpha':0.5}; gh='a'*64
    graphs=[{'node_ids':[f'n{i}'],'node_features':[[float(i),0,0,0]],'edge_index':[[],[]],
             'edge_features':[],'edge_width':2,'center_id':f'n{i}','parent_hash':gh} for i in range(3)]
    records=[{'graph_hash':gh,'center_id':f'n{i}','center_index':i,'probability':1/(3-i),'node_count':1,'edge_count':0} for i in range(3)]
    rng={'bit_generator':'PCG64','state':{'state':123,'inc':5},'has_uint32':0,'uinteger':0}
    scfg=cfg|{'train_start':'2022-01-03T00:00:00Z','train_end':'2026-01-01T00:00:00Z'}
    sampleid=sha(canonical({'training_graphs':[gh],'config':scfg,'seed':11,'records':records,'rng_state':rng}))
    samples={'graphs':graphs,'records':records,'source_hashes':[gh],'rng_state':rng,'seed':11,'identity':sampleid}
    dictionary={'representatives':[graphs[2],graphs[0]],'memberships':[[1,2],[0]],'sample_hash':sampleid,
      'training_graph_hashes':[gh],'config':cfg,'matching_config_hash':sha(canonical(matching)),'hierarchy':[]}
    science={'graphs':[{'nodes':g['node_ids'],**{k:g[k] for k in ('node_features','edge_index','edge_features','parent_hash','center_id')}} for g in dictionary['representatives']],
      'sample_hash':sampleid,'training_graph_hashes':[gh],'config':cfg,'matching_hash':dictionary['matching_config_hash'],'memberships':dictionary['memberships'],'hierarchy':[]}
    dictionary['identity']=sha(canonical(science))
    values={'dictionary':dictionary,'samples':samples,'dictionary_config':cfg,'matching_config':matching,
      'graph_manifest':{'graph_hash':gh,'metadata':{'start_utc':scfg['train_start'],'available_at':'2022-01-11T00:00:00Z'}},
      'gate':{'experiments':{'old':{'parent':None}}}}
    paths={k:'/original/'+k+'.json' for k in values}
    values['claim']={'experiment_id':'old','source':'b'*40,'design_source':'b'*40,'registration':'gate.json','registration_sha256':sha(canonical(values['gate'])),'experiment':{'parent':None},'prior_exposures':[{'state':'spent'}]}
    values['terminal']={'experiment_id':'old','status':'failed','claim_sha256':sha(canonical(values['claim']))}
    values['dictionary_intent']={'source_commit':'b'*40,'phase':'dictionary','week':'2022-01-03','bindings':{paths['samples']:sha(canonical(samples)),paths['dictionary_config']:sha(canonical(cfg)),paths['matching_config']:sha(canonical(matching))}}
    values['sample_intent']={'source_commit':'b'*40,'phase':'neighborhoods','week':'2022-01-03','bindings':{paths['graph_manifest']:sha(canonical(values['graph_manifest'])),paths['dictionary_config']:sha(canonical(cfg))}}
    values['dictionary_result']={'phase':'dictionary','week':'2022-01-03','status':'complete','details':{'identity':dictionary['identity'],'motifs':2,'resource_only':True}}
    for k in values:paths.setdefault(k,'/original/'+k+'.json')
    blobs={k:canonical(v) for k,v in values.items()}
    policy={'schema_version':1,'kind':'original-dictionary-import-v1','original_claim':'old','original_source':'b'*40,
      'week':'2022-01-03','dictionary_identity':dictionary['identity'],'sample_identity':sampleid,'sample_config':scfg,'seed':11,
      'sample_count':3,'motif_count':2,'required_graphs':[gh],'max_json_bytes':1048576,'max_total_json_bytes':4194304,
      'max_total_nodes':16,'max_total_edges':16,'refs':{k:{'input':k,'original_path':paths[k],'sha256':sha(v)} for k,v in blobs.items()}}
    return policy,blobs

class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('original_dictionary_candidate03',PATH)
        cls.m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=cls.m;spec.loader.exec_module(cls.m)
    def test_preserves_order_original_identity_and_parent_failure(self):
        p,b=fixture();v=self.m.validate(p,b)
        self.assertEqual(v.representative_indices,(2,0));self.assertEqual(v.dictionary_identity,p['dictionary_identity'])
        self.assertEqual(v.original_terminal,'failed');self.assertNotIn('pair_execution',v.dictionary_record()['config'])
    def test_mutated_body_rejected(self):
        p,b=fixture();b['samples']=b['samples']+b' '
        with self.assertRaises(ValueError):self.m.validate(p,b)
    def test_representative_reorder_with_repinned_body_rejected(self):
        p,b=fixture();d=json.loads(b['dictionary']);d['representatives'].reverse();b['dictionary']=canonical(d);p['refs']['dictionary']['sha256']=sha(b['dictionary'])
        with self.assertRaises(ValueError):self.m.validate(p,b)
    def test_missing_intermediate_graph_join_rejected(self):
        p,b=fixture();d=json.loads(b['sample_intent']);d['bindings'].clear();b['sample_intent']=canonical(d);p['refs']['sample_intent']['sha256']=sha(b['sample_intent'])
        with self.assertRaises(ValueError):self.m.validate(p,b)
    def test_capacity_before_parse_and_duplicate_key_refusal(self):
        p,b=fixture();p['max_json_bytes']=8
        with self.assertRaises(ValueError):self.m.validate(p,b)
        p,b=fixture();b['dictionary']=b'{"identity":1,"identity":2}';p['refs']['dictionary']['sha256']=sha(b['dictionary'])
        with self.assertRaises(ValueError):self.m.validate(p,b)
    def test_output_copy_cannot_mutate_evidence(self):
        p,b=fixture();v=self.m.validate(p,b);x=v.dictionary_record();x['representatives'].clear()
        self.assertEqual(len(v.dictionary_record()['representatives']),2)
    def test_original_rng_and_source_mismatch_rejected(self):
        p,b=fixture();p['seed']=12
        with self.assertRaises(ValueError):self.m.validate(p,b)
        p,b=fixture();p['original_source']='c'*40
        with self.assertRaises(ValueError):self.m.validate(p,b)
    def test_live_capability_revocation_and_late_mutation(self):
        p,b=fixture();state={'active':True}; lease=lambda:self.assertTrue(state['active'])
        cap=self.m._bind_for_test(p,lambda k:b[k],lease,'current-owner')
        self.assertEqual(cap.check().representative_indices,(2,0))
        b['samples']+=b' '
        with self.assertRaises(ValueError):cap.check()
        state['active']=False
        with self.assertRaises(AssertionError):cap.check()
    def test_post_callback_rejoin_and_one_shot_close(self):
        p,b=fixture();cap=self.m._bind_for_test(p,lambda k:b[k],lambda:None,'owner')
        def action(v):b['dictionary']+=b' ';return 'not published'
        with self.assertRaises(ValueError):cap.with_evidence(action)
        cap.close()
        with self.assertRaises(ValueError):cap.check()
        with self.assertRaises(ValueError):cap.close()
    def test_original_fatal_preserved_when_postcheck_fails(self):
        p,b=fixture();cap=self.m._bind_for_test(p,lambda k:b[k],lambda:None,'owner');fatal=MemoryError('first')
        def action(v):b['dictionary']+=b' ';raise fatal
        with self.assertRaises(MemoryError) as caught:cap.with_evidence(action)
        self.assertIs(caught.exception,fatal)

    def test_non_utc_or_naive_availability_rejected(self):
        for value in ('2025-12-31T23:00:00-12:00','2022-01-11T00:00:00','0000-malformed'):
            with self.subTest(value=value):
                p,b=fixture();graph=json.loads(b['graph_manifest']);graph['metadata']['available_at']=value
                b['graph_manifest']=canonical(graph);p['refs']['graph_manifest']['sha256']=sha(b['graph_manifest'])
                intent=json.loads(b['sample_intent']);intent['bindings'][p['refs']['graph_manifest']['original_path']]=sha(b['graph_manifest'])
                b['sample_intent']=canonical(intent);p['refs']['sample_intent']['sha256']=sha(b['sample_intent'])
                with self.assertRaises(ValueError):self.m.validate(p,b)

    def test_chronology_and_explicit_utc_equivalence(self):
        config={'train_start':'2022-01-03T00:00:00Z','train_end':'2022-02-01T00:00:00Z'}
        metadata={'start_utc':config['train_start'],'end_utc':'2022-01-10T00:00:00Z','available_at':'2022-01-11T00:00:00+00:00'}
        self.m._availability(metadata,config)
        for bad in (config|{'train_end':config['train_start']},config|{'train_end':'2021-01-01T00:00:00Z'}):
            with self.assertRaises(ValueError):self.m._availability(metadata,bad)
        for bad in (metadata|{'end_utc':'2022-01-12T00:00:00Z'},metadata|{'available_at':'2022-02-01T00:00:00Z'}):
            with self.assertRaises(ValueError):self.m._availability(bad,config)

if __name__=='__main__':unittest.main()
