from pathlib import Path
exec(compile((Path(__file__).parent/'verify.py').read_text().split('for name,a,b in fixtures:')[0],__file__,'exec'))
for name,a,b in fixtures[:4]:
    seed=B.create(a,b,config,max_state_bytes=1000000,max_chunk_entries=32)
    B.advance(seed,a,b,config,max_operations=len(a.node_ids)*len(b.node_ids)+1)
    for budget in range(1,a.edge_index.shape[1]*b.edge_index.shape[1]+8):
        x=copy.deepcopy(seed);y=copy.deepcopy(seed)
        assert B._advance_checked(x,a,b,config,max_operations=budget)==C._advance_checked(y,a,b,config,max_operations=budget);equal(x,y)
    for mod in [B,C]:
        x=copy.deepcopy(seed)
        with np.errstate(all='raise'):
            mod.advance(x,a,b,config,max_operations=100000)
        res=mod.result(x,a,b,config);ref=match_reference(a,b,config)
        assert res.assignment.tobytes()==ref.assignment.tobytes() and res.score.hex()==ref.score.hex() and res.soft_assignment.tobytes()==ref.soft_assignment.tobytes()
# Actual inverse baseline->candidate->baseline checkpoint interoperability.
a,b=fixtures[0][1:];x=B.create(a,b,config,max_state_bytes=1000000,max_chunk_entries=32)
B.advance(x,a,b,config,max_operations=18)
h=B.save(x,P/'checkpoint-baseline-to-candidate',a,b,config,max_checkpoint_bytes=1000000)
y=C.load(P/'checkpoint-baseline-to-candidate',a,b,config,expected_sha256=h,max_state_bytes=1000000,max_chunk_entries=32);equal(x,y)
print(json.dumps({'status':'PASS','extra_boundary_checks':checks,'scalar_reference_final_results':8,'raise_mode_fallback':True,'baseline_to_candidate_checkpoint':True}))
