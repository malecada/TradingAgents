"""Named offline synthetic integer checks. No genuine source/data authority."""
import copy,json,unittest
import controls01 as c


def fixture():
    calc=c.allocation();graphs={}
    for w in c.WEEKS:
        x=calc['graph'](1,65536,4194240,4194304,16800)
        graphs[w]={'rows':1,'tail_part_bytes':4194240,'output_part_bytes':4194304,
            'allowances':x['required_typed_allowances'],'count_evidence_sha256':'0'*64}
    residual={n:dict(logical_bytes=10**7,regular_files=100,directories=20,max_file_bytes=8*1024**2,
        additional_scratch_bytes=100,scratch_files=1,scratch_max_file_bytes=100,
        evidence_sha256='0'*64,bound_basis='SYNTHETIC integer fixture only, no evidence authority') for n in c.REQUIRED}
    root='/synthetic';exp=c.EXPERIMENT
    return dict(schema_version=1,graphs=graphs,chunk_cells=65536,typed_control_bytes=10**7,
        archive=dict(max_stage_verifications=2,max_writer_metadata_bytes=10**7,max_read_metadata_bytes=10**7,max_stage_bytes=11*10**6,max_workflow_metadata_bytes=10**9),
        stage=dict(max_events=1000,chunk_events=100,max_total_checkpoints=100),
        transport=dict(max_commands=1000,max_payload_bytes=10**12,max_diagnostic_bytes=10**12+c.DMETA*1000,max_control_bytes=c.DMETA*4008),
        residual_domains=residual,
        filesystem=dict(allocation_unit_bytes=4096,per_regular_inode_overhead_bytes=256,per_directory_allocated_bytes=4096,extra_allocated_bytes=4096,extra_entries=10,max_native_file_bytes=8*1024**2,evidence_sha256='0'*64),
        baseline=dict(logical_bytes=0,allocated_bytes=0,entries=0,evidence_sha256='0'*64),
        storage_budget=dict(schema_version=2,kind='real-pilot-writable-union',authority_root=root,experiment=exp,roots=[root+'/research_artifacts',root+'/research_runs/'+exp],shared_files=[root+'/research_runs/.lock'],limits=dict(max_logical_bytes=10**14,max_allocated_bytes=10**14,max_entries=10**8,max_depth=64,max_scan_seconds=5)))

class Controls(unittest.TestCase):
    def test_reconciled_tiny_counts(self):
        r=c.calculate(fixture());v=r['categories']
        self.assertEqual(v['stream_tail_batch_headers']['regular_files'],70)
        self.assertEqual(v['typed_attempts']['directories'],35) #7*(2 tail+2 batch+1 output)
        self.assertEqual(v['retained_original_matrices']['logical_bytes'],896)
        self.assertEqual(v['transport_diagnostics']['logical_bytes'],1000*131072+8388608)
        self.assertEqual(r['builder03_physical_fragment']['additional_scratch_bytes'],400)
    def test_cumulative_io_is_not_retained(self):
        a=fixture();b=copy.deepcopy(a)
        b['transport']['max_payload_bytes']+=10**13;b['transport']['max_diagnostic_bytes']+=10**13
        x,y=c.calculate(a),c.calculate(b)
        self.assertEqual(x['new_logical_bytes'],y['new_logical_bytes'])
        self.assertEqual(x['allocation_overhead_bytes'],y['allocation_overhead_bytes'])
    def test_missing_and_zero_domain_refused(self):
        a=fixture();del a['residual_domains']['runtime_temp_cache']
        with self.assertRaisesRegex(ValueError,'complete residual'):c.calculate(a)
        a=fixture();a['residual_domains']['runtime_temp_cache']['logical_bytes']=0
        with self.assertRaisesRegex(ValueError,'unknown/zero'):c.calculate(a)
    def test_tail_recovery_cannot_be_removed(self):
        a=fixture();a['graphs'][c.WEEKS[0]]['allowances']['score-tail-f64']['max_recovered_bytes']=0
        with self.assertRaisesRegex(ValueError,'mandatory original traversal'):c.calculate(a)
    def test_aggregate_and_file_cap_refusals(self):
        a=fixture();a['storage_budget']['limits']['max_entries']=1
        with self.assertRaisesRegex(ValueError,'underfunded: entries'):c.calculate(a)
        a=fixture();a['filesystem']['max_native_file_bytes']=4*1024**2
        with self.assertRaisesRegex(ValueError,'native file cap'):c.calculate(a)
    def test_multibatch_count_and_overhead(self):
        a=fixture();g=a['graphs'][c.WEEKS[0]];g['rows']=2049
        g['allowances']=c.allocation()['graph'](2049,65536,4194240,4194304,16800)['required_typed_allowances']
        r=c.calculate(a)
        self.assertEqual(r['by_week'][c.WEEKS[0]]['batch_count'],2)
        self.assertEqual(r['by_week'][c.WEEKS[0]]['tail_preserve_parts'],3)
        self.assertEqual(r['by_week'][c.WEEKS[0]]['required_typed_allowances']['score-tail-f64']['max_chunks'],6)
        self.assertEqual(r['categories']['stream_tail_batch_headers']['regular_files'],75)
        files=r['regular_file_slots'];dirs=r['directory_slots']
        self.assertEqual(r['allocation_overhead_bytes'],files*(4095+256)+dirs*4096+4096)

if __name__=='__main__':unittest.main()
