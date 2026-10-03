"""Real source serializer and retained start reconstruction; no authority claim."""
import ast,hashlib,json,unittest
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
F=HERE.parent
CAP=F/'original-import-native-release-2026-10-03/capsule01'
def namespace():
    tree=ast.parse((HERE/'compact_mcm.py').read_text())
    helpers=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='_source_evidence']
    if not helpers:raise AssertionError('selected source evidence helper missing')
    p=F/'original-import-native-release-2026-10-03/capsule01/tradingagents/research/onchain_replication/provenance.py'
    provenance=ast.parse(p.read_text());functions=[node for node in provenance.body if isinstance(node,ast.FunctionDef) and node.name in {'canonical_bytes','digest','thaw'}]
    cache=ast.parse((p.parent/'cache.py').read_text());fn=next(node for node in cache.body if isinstance(node,ast.FunctionDef) and node.name=='cache_key')
    def require(v,m):
        if not v:raise ValueError(m)
    ns={'_imported':lambda x:x is True,'require':require,'json':json,'hashlib':hashlib}
    exec(compile(ast.Module(body=[*functions,fn,*helpers],type_ignores=[]),'actual-metadata-helper','exec'),ns)
    score=ast.parse((p.parent/'score_batches.py').read_text());nodes=[node for node in score.body if isinstance(node,ast.FunctionDef) and node.name in {'_json','_require'}]
    serializer={'json':json,'META_LIMIT':8192};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-score-serializer','exec'),serializer)
    ns.update(serializer);return ns
class Metadata(unittest.TestCase):
    def test_actual_retained_start_is_too_large_and_selected_reference_fits(self):
        ns=namespace();records=json.loads((F/'original-import-metadata-bound-investigation-2026-10-03/RECONSTRUCTION01.json').read_text())['records']
        for row in records:
            start=row['start'];self.assertEqual(len((json.dumps(start,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()),19902)
            with self.assertRaisesRegex(ValueError,'compact metadata bound'):ns['_json'](start)
            reference=ns['_source_evidence'](True,start['sources']);fixed=start|{'sources':reference}
            self.assertEqual(reference['source_count'],144);self.assertEqual(reference['source_sha256'],ns['cache_key'](start['sources']))
            self.assertLess(len(ns['_json'](fixed)),8192)
    def test_legacy_returns_exact_same_map(self):
        ns=namespace();value={'unchanged':'a'*64};self.assertIs(ns['_source_evidence'](False,value),value)
    def test_source_changes_do_not_preserve_the_reference(self):
        ns=namespace();a={'path':'a'*64};expected=ns['_source_evidence'](True,a)
        self.assertNotEqual(expected,ns['_source_evidence'](True,{'path':'b'*64}))
        self.assertNotEqual(expected,ns['_source_evidence'](True,a|{'more':'b'*64}))
    def test_actual_check_join_rejects_changed_or_malformed_receipt_references(self):
        ns=namespace();tree=ast.parse((HERE/'compact_mcm.py').read_text());produced=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Produced');check=next(n for n in produced.body if isinstance(n,ast.FunctionDef) and n.name=='_check')
        clauses=[n for n in check.body if isinstance(n,ast.If) and isinstance(n.test,ast.Call) and isinstance(n.test.func,ast.Name) and n.test.func.id=='_imported']
        self.assertEqual(len(clauses),2);self.assertEqual(ast.dump(clauses[0]),ast.dump(clauses[1]))
        selected=compile(ast.Module(body=[clauses[0]],type_ignores=[]),'actual-check-reference-join','exec')
        sources={'path':'a'*64};expected=ns['_source_evidence'](True,sources)
        ns['_sources']=lambda dictionary:sources
        ns['self']=SimpleNamespace(_dictionary=True,_start={'sources':expected})
        exec(selected,ns)
        for altered in [sources,expected|{'source_count':2},expected|{'source_sha256':'b'*64},expected|{'kind':'other'},expected|{'extra':True}]:
            ns['self']._start={'sources':altered}
            with self.assertRaisesRegex(ValueError,'imported source receipt reference differs'):exec(selected,ns)
    def test_invalid_selected_map_is_refused_and_legacy_untouched(self):
        ns=namespace()
        for value in [{},{'path':'bad'},{'path':'A'*64},{'path':1},{1:'a'*64},[]]:
            with self.assertRaisesRegex(ValueError,'imported source evidence differs'):ns['_source_evidence'](True,value)
            self.assertIs(ns['_source_evidence'](False,value),value)
    def test_complete_record_prospective_extent_and_unchanged_read_limits(self):
        ns=namespace();tree=ast.parse((HERE/'compact_mcm.py').read_text())
        producer=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked')
        record_assignment=next(n for n in ast.walk(producer) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='record' for x in n.targets))
        owner=json.loads(next((CAP/'research_artifacts/onchain_representations').glob('*/original-import-native-success-20261003-01/compact/owner.json')).read_text())
        gate=json.loads((CAP/'fixture-registration.json').read_text());experiment=gate['experiments']['original-import-native-success-20261003-01']
        policy=json.loads((CAP/experiment['inputs']['compact_policy']['path']).read_text())['stage_policy']
        records=json.loads((F/'original-import-metadata-bound-investigation-2026-10-03/RECONSTRUCTION01.json').read_text())['records']
        for row in records:
            start=row['start']|{'sources':ns['_source_evidence'](True,row['start']['sources'])};zero='0'*64
            name='mcm-'+start['graph_hash'];root=Path(owner['binding']['journal_directory'])/'compact'/name
            contract={'owner':owner['binding']['claim_sha256'],'scope':{name:zero for name in ['workflow','config','context','policy','numerical_source']},'policy':policy,'kind':'mcm','pairs':start['cells'],'log_terminal_sha256':zero,'stream_terminal_sha256':zero}
            output=CAP/'research_artifacts/onchain_compact_outputs'/owner['binding']['workflow_identity']/owner['binding']['experiment']/name
            args={'stage_root':root,'stage_sha256':zero,'contract':contract,'expected_scope':start['scope'],'max_output_bytes':1048576}
            proof={'schema_version':1,'kind':'owned-compact-mcm-output','owner':owner['binding']['claim_sha256'],'binding_sha256':zero,'claim_sha256':owner['binding']['claim_sha256'],'stage':name,'stage_sha256':zero,'policy_input':start['output_input'],'policy_sha256':start['output_policy_sha256'],'workflow_reserved_output_bytes':start['reserved_workflow_output_bytes'],'representation_admitted':False}
            prospect=ns|{'start':start,'start_sha':zero,'stage_ref':zero,'stage_inode':[2**63-1,2**63-1],'pin':zero,'ticket':{'directory':str(output),'receipt_sha256':zero,'artifact_sha256':zero},'args':args,'output_proof':proof}
            exec(compile(ast.Module(body=[record_assignment],type_ignores=[]),'actual-complete-record-expression','exec'),prospect)
            self.assertLess(len(ns['_json'](prospect['record'])),8192)
        # Exact original method still reads both start/complete at META_LIMIT;
        # _json and the metadata reservation expression are not widened.
        produced=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Produced');evidence=next(n for n in produced.body if isinstance(n,ast.FunctionDef) and n.name=='_evidence')
        reads=[n for n in ast.walk(evidence) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='_read']
        self.assertEqual(len(reads),2)
        self.assertTrue(all(ast.dump(n.args[-1])==ast.dump(ast.Attribute(value=ast.Name(id='io',ctx=ast.Load()),attr='META_LIMIT',ctx=ast.Load())) for n in reads))
    def test_actual_start_and_check_call_the_selected_evidence_join(self):
        tree=ast.parse((HERE/'compact_mcm.py').read_text());prepare=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_prepare')
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_source_evidence' for n in ast.walk(prepare)))
        produced=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Produced');check=next(n for n in produced.body if isinstance(n,ast.FunctionDef) and n.name=='_check')
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_source_evidence' for n in ast.walk(check)))
    def test_every_numerical_and_production_function_is_unchanged(self):
        old=ast.parse((HERE/'compact_mcm.baseline.py').read_text());new=ast.parse((HERE/'compact_mcm.py').read_text());mapping={n.name:n for n in new.body if isinstance(n,ast.FunctionDef)}
        for node in old.body:
            if isinstance(node,ast.FunctionDef) and node.name!='_prepare':self.assertEqual(ast.dump(node),ast.dump(mapping[node.name]),node.name)
        oldclass=next(n for n in old.body if isinstance(n,ast.ClassDef) and n.name=='Produced');newclass=next(n for n in new.body if isinstance(n,ast.ClassDef) and n.name=='Produced');methods={n.name:n for n in newclass.body if isinstance(n,ast.FunctionDef)}
        for node in oldclass.body:
            if isinstance(node,ast.FunctionDef) and node.name!='_check':self.assertEqual(ast.dump(node),ast.dump(methods[node.name]),node.name)
        oldcheck=next(n for n in oldclass.body if isinstance(n,ast.FunctionDef) and n.name=='_check')
        newcheck=methods['_check']
        newcheck.body=[n for n in newcheck.body if not (isinstance(n,ast.If) and isinstance(n.test,ast.Call) and isinstance(n.test.func,ast.Name) and n.test.func.id=='_imported')]
        self.assertEqual(ast.dump(oldcheck),ast.dump(newcheck))
        oldprepare=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='_prepare')
        newprepare=mapping['_prepare']
        class StripSourceReference(ast.NodeTransformer):
            def visit_Call(self,node):
                if isinstance(node.func,ast.Name) and node.func.id=='_source_evidence':return ast.Name(id='sources',ctx=ast.Load())
                return self.generic_visit(node)
        self.assertEqual(ast.dump(oldprepare),ast.dump(StripSourceReference().visit(newprepare)))
if __name__=='__main__':unittest.main(verbosity=2)
