"""Finite metadata-only dimension arithmetic. No array or scientific imports."""
import json
from pathlib import Path

def estimate(headers):
    assert len(headers["graphs"]) == 7
    rows = []
    for g in headers["graphs"]:
        n, e = g["N"], g["E"]
        assert type(n) is int and type(e) is int and n > 0 and e > n
        shapes = {"node_features": [n, 4], "edge_index": [2, e], "edge_features": [e, 2], "edge_aggregates": [e, 2]}
        for key, shape in shapes.items():
            h = g["headers"][key]
            assert h["header"]["shape"] == shape
            assert h["header"]["descr"] == ("<i8" if key == "edge_index" else "<f8")
        # S original self loops unknown; U=E-S+N. Duplicate-free graph: 0<=S<=N.
        u = [e, e+n]
        row = {"week": g["week"], "graph_hash": g["graph_hash"], "N": n, "E": e, "U_range": u,
               "mcm_float32_N32_mapped_bytes": n*32*4,
               "original_edge_index_int64_2E_bytes": 2*e*8,
               "raw_numeric_graph_arrays_bytes": 32*n+48*e,
               "mlp_N64_each_bytes": n*64*4,
               "mlp_N32_each_bytes": n*32*4,
               "layers": []}
        for heads, width, input_width in [(4,16,32),(1,32,64)]:
            row["layers"].append({"heads":heads,"head_width":width,"input_width":input_width,
               "clean_NF_bytes": n*input_width*4,
               "h_NHD_bytes":n*heads*width*4,"out_NHD_bytes":n*heads*width*4,
               "source_score_target_score_maximum_denom_each_NH_bytes":n*heads*4,
               "e_numer_attention_each_UH_bytes_range":[v*heads*4 for v in u],
               "source_target_each_int64_U_bytes_range":[v*8 for v in u],
               "one_full_block_message_BHD_bytes":65536*heads*width*4,
               "proven_h_out_one_block_coexist_bytes":2*n*heads*width*4+65536*heads*width*4})
        rows.append(row)
    n=sum(r["N"] for r in rows);e=sum(r["E"] for r in rows)
    assert (n,e)==(12999004,18683284)
    raw=sum(r["raw_numeric_graph_arrays_bytes"] for r in rows)
    bound=raw+max(l["proven_h_out_one_block_coexist_bytes"] for r in rows for l in r["layers"])
    return {"scope":"Conditional source-level storage requirements if neural stage is reached; not observed RSS, peak, capacity or financial fit", "graphs":rows,
      "totals":{"N":n,"E":e,"mcm_mapped_payload_bytes":128*n,"raw_numeric_retained_bytes":raw,"original_edge_index_bytes_included_in_raw":16*e},
      "conservative_proven_simultaneous_storage_bytes":bound,
      "bound_includes":"All retained resident numeric raw graph arrays plus largest layer h, out and one block messages. Excludes MCM page residency and all other overhead. This is a storage lower bound, not a measured cgroup resident-memory floor.",
      "bound_exceeds_6GiB":bound>6*1024**3,"bound_exceeds_nominal_16GB":bound>16_000_000_000,
      "limitations":["U uses unknown original self-loop count; original graph edges must pass duplicate-free runtime check", "Expanded index is a view, not U*H new int64 backing", "torch.from_numpy aliases MCM/edge backing", "Layer concat reshape may view or copy depending stride", "Never sum all named shapes as peak", "No measured allocator, checkpoint recomputation, unique/sort scratch, Python node-ID, mmap residency, gradient or optimizer peak"]}

if __name__ == "__main__":
    directory=Path(__file__).resolve().parent
    result=estimate(json.loads((directory/"GRAPH_HEADERS01.json").read_text()))
    (directory/"ARITHMETIC01.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result["totals"],sort_keys=True))
    print("conditional simultaneous storage bound:",result["conservative_proven_simultaneous_storage_bytes"])
