import unittest
from caller01 import move_rows,selected_rows
class Checks(unittest.TestCase):
    def test_verifier_before_every_transfer(self):
        events=[];rows=[{'path':'a'},{'path':'b'}]
        out=move_rows(rows,before=lambda r:events.append('verify:'+r['path']),move=lambda r,i:events.append('move:'+r['path']) or r,publish=lambda n,v:events.append(n))
        self.assertEqual(out,rows);self.assertEqual(events,['00-attempted.json','verify:a','move:a','01-attempted.json','verify:b','move:b'])
    def test_failure_preserves_attempt_skips_rest_no_retry(self):
        records={};events=[];rows=[{'path':'a'},{'path':'b'},{'path':'c'}]
        def check(row):
            events.append(row['path'])
            if row['path']=='b':raise ValueError('changed metadata')
        with self.assertRaises(ValueError):move_rows(rows,before=check,move=lambda r,i:r,publish=lambda n,v:records.update({n:v}))
        self.assertEqual(events,['a','b']);self.assertEqual(records['01-failed.json']['status'],'failed');self.assertEqual(records['02-skipped.json']['status'],'skipped');self.assertNotIn('02-attempted.json',records)
    def test_selection_cannot_expand_or_alias(self):
        with self.assertRaises(ValueError):selected_rows({'files':[]})
    def test_receipt_failure_does_not_hide_original(self):
        original=KeyboardInterrupt('original');seen=[]
        def fail(row):raise original
        def publish(name,value):
            seen.append(name)
            if 'failed' in name:raise OSError('receipt unavailable')
        with self.assertRaises(KeyboardInterrupt) as caught:move_rows([{'path':'a'},{'path':'b'}],before=fail,move=lambda r,i:None,publish=publish)
        self.assertIs(caught.exception,original);self.assertIn('01-skipped.json',seen)
if __name__=='__main__':unittest.main()
