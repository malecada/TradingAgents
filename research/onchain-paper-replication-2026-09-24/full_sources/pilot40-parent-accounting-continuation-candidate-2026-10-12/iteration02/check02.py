"""Actual-byte finite proof parser controls; no genuine admission or numerical imports."""
from pathlib import Path
import ast,json,hashlib,copy,unittest
P=Path(__file__).resolve().parent;R=P.parents[3]
def digest(raw):return hashlib.sha256(raw).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
ns=dict(require=require,digest=digest,_json=json.loads)
tree=ast.parse((P/'batched_continuation.py').read_text());tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_original39_contract','_original39_accounting')];exec(compile(tree,str(P/'batched_continuation.py'),'exec'),ns)
fixed=ns['_original39_contract']()
class Checks(unittest.TestCase):
 def fixture(self):
  evidence={k:(R/p['path']).read_bytes() for k,p in fixed['evidence'].items()}
  d=R/'research_runs'/fixed['parent'];evidence.update(claim=(d/'claim.json').read_bytes(),failed=(d/'failed.json').read_bytes())
  sources={path:(P/'original_source'/Path(path).name).read_bytes() for path in fixed['sources']}
  a=dict(format=fixed['format'],parent_experiment=fixed['parent'],parent_claim_sha256=fixed['claim_sha256'],parent_failed_sha256=fixed['failed_sha256'],evidence={k:{'role':'synthetic-role-'+k,'sha256':v['sha256']} for k,v in fixed['evidence'].items()},source_bodies={k:{'role':'synthetic-source-'+Path(k).name,'sha256':v} for k,v in fixed['sources'].items()},spent_counters=fixed['costs'].copy(),retained_partial_work={k:0 for k in fixed['costs']},preserved_unknowns=['telemetry','cache','transport','outer_disposition'])
  m=dict(parent_accounting_mode=fixed['format'],parent_experiment=fixed['parent'],spent_counters=fixed['costs'].copy(),batches=[[{'role':'synthetic-batch','sha256':s} for s in b] for b in fixed['batches']])
  return a,m,json.loads(evidence['claim']),json.loads(evidence['failed']),evidence,sources
 def call(self,data):
  a,m,c,f,e,s=data;raw=json.dumps(a,sort_keys=True).encode();review={'parent_accounting_mode':fixed['format'],'parent_accounting_sha256':digest(raw)}
  return ns['_original39_accounting'](raw,m,review,c,f,e,s)
 def test_original_predicate_red_new_byte_parser_green(self):
  data=self.fixture();raw=json.dumps(data[0],sort_keys=True).encode();self.assertNotIn(digest(raw),data[3]['output_sha256'].values());self.assertEqual(self.call(data),data[0])
 def test_wrong_parent_failed_counter_and_partial(self):
  for mutation in (lambda a,m,c,f,e,s:a.update(parent_experiment='wrong'),lambda a,m,c,f,e,s:a.update(parent_failed_sha256='0'*64),lambda a,m,c,f,e,s:a['spent_counters'].update(advance_calls=1),lambda a,m,c,f,e,s:a['retained_partial_work'].update(advance_calls=1),lambda a,m,c,f,e,s:a.update(preserved_unknowns=[])):
   data=self.fixture();mutation(*data)
   with self.assertRaises(ValueError):self.call(data)
 def test_forged_evidence_source_recovery(self):
  for key in ('traceback','return_review','recovery','selection','capture','guard_final','output:pilot-summary.json'):
   data=self.fixture();data[4][key]+=b' '
   with self.assertRaises(ValueError):self.call(data)
  data=self.fixture();key=next(iter(data[5]));data[5][key]+=b'\n'
  with self.assertRaises(ValueError):self.call(data)
 def test_batch_tail_other_failure_and_scope(self):
  for mutate in (lambda d:d[1]['batches'].pop(),lambda d:d[1]['batches'][15][5].update(sha256='0'*64),lambda d:d[0]['spent_counters'].update(telemetry=1),lambda d:d[1].update(provenance_mode='legacy-recovered-prefix-v1')):
   data=self.fixture();mutate(data)
   with self.assertRaises(ValueError):self.call(data)
 def test_default_authority_body_unchanged(self):
  old=ast.parse((P/'BASELINE_batched_continuation.py').read_text());new=ast.parse((P/'batched_continuation.py').read_text())
  f=lambda t:next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_authority')
  a=f(old);b=f(new);b.body=[n for n in b.body if not (isinstance(n,ast.If) and ast.unparse(n.test)=="'parent_accounting_mode' in m")]
  self.assertEqual(ast.dump(a),ast.dump(b))
 def test_fixed_contract_fresh_no_mutable_global(self):
  d=ns['_original39_contract']();d['costs']['advance_calls']=0;self.assertEqual(ns['_original39_contract']()['costs']['advance_calls'],128653)
if __name__=='__main__':unittest.main(verbosity=2)
