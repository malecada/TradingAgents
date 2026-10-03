"""Compose disjoint frozen source corrections without any admission or run."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];FULL=HERE.parent
META=FULL/'imported-source-metadata-correction02-2026-10-03'
CLEAN=FULL/'original-import-native-refusal-candidate03-2026-10-03'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def body(path,pin):
    raw=path.read_bytes();assert sha(raw)==pin;return raw
def main():
    base=body(META/'compact_mcm.py','9009112805eec33444030058d30bd7d741b59fdb0bcfb9ab031f9862923d7f53').decode()
    clean=body(CLEAN/'compact_mcm.py','05c7d5dfd53fd537cc2b2033427b4f496887c13ada9ff33310606dd2fa7c509d').decode()
    tree=ast.parse(base);other=ast.parse(clean)
    old_fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked')
    new_fn=next(n for n in other.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked')
    lines=base.splitlines(keepends=True);replacement=''.join(clean.splitlines(keepends=True)[new_fn.lineno-1:new_fn.end_lineno])
    composed=''.join(lines[:old_fn.lineno-1])+replacement+'\n'+''.join(lines[old_fn.end_lineno:])
    result=ast.parse(composed);result_fn=next(n for n in result.body if isinstance(n,ast.FunctionDef) and n.name=='_produce_locked')
    assert ast.dump(result_fn)==ast.dump(new_fn)
    old_other=ast.Module(body=[n for n in tree.body if n is not old_fn],type_ignores=[])
    result_other=ast.Module(body=[n for n in result.body if n is not result_fn],type_ignores=[])
    assert ast.dump(old_other)==ast.dump(result_other)
    baseline=ast.parse((HERE/'generate_inputs.baseline.py').read_bytes());generator=ast.parse((HERE/'generate_inputs01.py').read_bytes())
    # Restore the sole registered resource literal before AST parity.
    changed=[]
    for node in ast.walk(generator):
        if isinstance(node,ast.Dict):
            for key,value in zip(node.keys,node.values):
                if isinstance(key,ast.Constant) and key.value=='edge_chunk' and isinstance(value,ast.Constant) and value.value==4096:changed.append(value);value.value=65536
    assert len(changed)==1
    assert ast.dump(ast.Module(body=[n for n in baseline.body if not isinstance(n,ast.FunctionDef) or n.name!='registration'],type_ignores=[]))==ast.dump(ast.Module(body=[n for n in generator.body if not isinstance(n,ast.FunctionDef) or n.name!='registration'],type_ignores=[]))
    target=HERE/'compact_mcm.py'
    with target.open('x') as stream:stream.write(composed)
    predecessor=META/'source_inventory01.json';inventory=json.loads(predecessor.read_bytes());rows=inventory['source_inventory']
    for row in rows:
        assert sha((ROOT/row['origin']).read_bytes())==row['sha256']
        name={'tradingagents/research/onchain_replication/compact_mcm.py':'compact_mcm.py','fixture_tools/generate_inputs01.py':'generate_inputs01.py','tradingagents/research/onchain_replication/resource_fixture.py':'resource_fixture.py'}.get(row['target'])
        if name:
            path=HERE/name;raw=path.read_bytes();row.update(origin=str(path.relative_to(ROOT)),sha256=sha(raw),bytes=len(raw),git_commit=None,git_path=None)
    assert len(rows)==153 and sum(x['target'].startswith('tradingagents/') for x in rows)==142
    output={'schema_version':1,'status':'composed_source_only_not_released','source_inventory':rows,'composed_package_count':142,
        'source_logical_bytes':sum(x['bytes'] for x in rows),'predecessor':{'path':str(predecessor.relative_to(ROOT)),'sha256':sha(predecessor.read_bytes())},
        'replaced_targets':['tradingagents/research/onchain_replication/compact_mcm.py','fixture_tools/generate_inputs01.py','tradingagents/research/onchain_replication/resource_fixture.py'],
        'metadata_source_sha256':sha(base.encode()),'cleanup_source_sha256':sha(clean.encode()),'composed_mcm_sha256':sha(composed.encode()),
        'qualification':'Exact disjoint metadata02 and cleanup03 AST composition plus prospective finite successor gate generator. All numerical body and current required142package closure retained. Source only; independent composition/gate/runtime/capsule review still required. Refusal parser/modules and27suite are not admitted here.'}
    with (HERE/'source_inventory01.json').open('x') as stream:json.dump(output,stream,indent=2,sort_keys=True);stream.write('\n')
    print(json.dumps({'source_count':len(rows),'package_count':142,'composed_mcm_sha256':sha(composed.encode()),'source_inventory_sha256':sha((HERE/'source_inventory01.json').read_bytes()),'generator_sha256':sha((HERE/'generate_inputs01.py').read_bytes())}))
if __name__=='__main__':main()
