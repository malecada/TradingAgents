from pathlib import Path
import ast,json,importlib.util,copy
D=Path(__file__).resolve().parent;P=D.parent/'financial-wrapper-continuation-proof-reuse01-2026-10-05';sp=importlib.util.spec_from_file_location('bounded_predicate_source',P/'preclaim_reuse01.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
tree=ast.parse((P/'preclaim_reuse01.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_reuse_contract');node=next(n for n in fn.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='completed100 recovered provenance differs' for a in n.value.args));predicate=compile(ast.Expression(node.value.args[0]),'exact-original-recovery-provenance-predicate','eval')
outcome=json.loads(Path(m.REUSE_ANCHORS['outcome']['path']).read_text());fields={'source':m.REUSE_SOURCE,'identity':m.REUSE_REFERENCE,'outcome_review_sha256':m.REUSE_ANCHORS['outcome']['sha256'],'claim_sha256':outcome['actual_claim_sha256'],'terminal_sha256':outcome['actual_terminal_sha256'],'checkpoint_sha256':outcome['actual_checkpoint_sha256']};env={'REUSE_SOURCE':m.REUSE_SOURCE,'REUSE_REFERENCE':m.REUSE_REFERENCE,'REUSE_ANCHORS':m.REUSE_ANCHORS,'outcome':outcome,'recovered':fields};assert eval(predicate,env)
refused=[]
for k in fields:
 changed=copy.deepcopy(fields);changed[k]='foreign';assert not eval(predicate,{**env,'recovered':changed});refused.append(k)
# This scalar map deliberately has no schema/decision/review and is never a proof.
(D/'PREDICATES01.json').write_text(json.dumps({'actual_original_provenance_scalar_match':True,'mutated_fields_refused':refused,'no_proof_constructed':True,'no_public_function_or_authority_called':True},indent=2)+'\n');print(len(refused))
