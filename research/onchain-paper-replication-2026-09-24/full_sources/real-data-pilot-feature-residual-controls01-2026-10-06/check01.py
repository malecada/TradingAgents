"""Offline integer fixtures only; no selected empirical grants."""
import copy,unittest
import residuals01 as r

def fixture():
    return {'stage':{'pair':{'max_checkpoint_bytes':1048576},'schedule':{'max_total_checkpoints':3},'restart_retention':{'schema_version':1,'format':'archived-restart-retention-v1','max_stores':20,'max_generations':3,'max_control_bytes':4194304,'max_cumulative_bytes':33554432,'max_live_bytes':10485760,'max_replay_bytes':2097152,'max_input_bytes':2097152,'max_replays':2}},'native_file_bytes':8388608,'training_checkpoint_bytes':4194304,'runtime_reservation':{'logical_bytes':16777216,'regular_files':128,'directories':13,'max_file_bytes':1048576}}

class Residuals(unittest.TestCase):
    def test_source_counts_and_serial_overlap(self):
        x=r.resolve(**fixture());d=x['residual_domains'];k=d['checkpoint_retention']
        self.assertEqual(k['regular_files'],756)
        self.assertEqual(k['directories'],182)
        self.assertEqual(k['additional_scratch_bytes'],2097152)
        self.assertEqual(k['logical_bytes'],7*(8388608+32768))
        self.assertEqual(d['import_owner_stage_journal']['regular_files'],23)
        self.assertEqual(d['import_owner_stage_journal']['logical_bytes'],1507328)
        self.assertEqual(len(x['runtime_relative_paths']),12)
    def test_no_silent_zero_or_omitted_runtime(self):
        a=fixture();a['runtime_reservation']['logical_bytes']=0
        with self.assertRaises(ValueError):r.resolve(**a)
        a=fixture();a['runtime_reservation']['directories']=12
        with self.assertRaisesRegex(ValueError,'twelve actual'):r.resolve(**a)
    def test_underfunded_original_checkpoint(self):
        a=fixture();a['stage']['restart_retention']['max_live_bytes']-=1
        with self.assertRaisesRegex(ValueError,'live reservation'):r.resolve(**a)
        a=fixture();a['stage']['restart_retention']['max_generations']=2
        with self.assertRaisesRegex(ValueError,'generation'):r.resolve(**a)
    def test_finite_declarations_and_unchanged_native(self):
        a=fixture();b=copy.deepcopy(a);x=r.resolve(**a)
        self.assertEqual(a,b)
        for d in x['residual_domains'].values():
            self.assertLessEqual(d['logical_bytes'],d['regular_files']*d['max_file_bytes'])
            self.assertLessEqual(d['max_file_bytes'],a['native_file_bytes'])
        self.assertIn('runtime_temp_cache',x['prospective_ceilings'])

if __name__=='__main__':unittest.main()
