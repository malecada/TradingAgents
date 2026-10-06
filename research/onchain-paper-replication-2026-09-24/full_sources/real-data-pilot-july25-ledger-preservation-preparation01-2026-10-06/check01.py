"""Focused stdlib source/template checks; never imports entry/helper runtime."""
import ast,hashlib,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def audit(event,args):
    if event.startswith(('socket.','subprocess.')):raise RuntimeError('offline source checks only')
    if event=='import' and args[0].split('.')[0] in {'numpy','torch','pandas','scipy','tradingagents'}:raise RuntimeError('scientific runtime imports forbidden')
sys.addaudithook(audit)
def read(name):return json.loads((HERE/name).read_text())
class Checks(unittest.TestCase):
    def test_exact_identity_only_literal_ast_inverse(self):
        proof=read('INVERSE01.json');old='real-pilot-sixth-graph-preservation-20261006-01';new='real-pilot-july25-ledger-preservation-20261006-01'
        for name,p in proof['files'].items():
            before=(ROOT/p['before']['path']).read_text();after=(HERE/name).read_text()
            self.assertEqual(hashlib.sha256(before.encode()).hexdigest(),p['before']['sha256']);self.assertEqual(hashlib.sha256(after.encode()).hexdigest(),p['candidate']['sha256'])
            self.assertEqual(after.count(new),1);self.assertEqual(after.replace(new,old),before);self.assertEqual(ast.dump(ast.parse(after.replace(new,old))),ast.dump(ast.parse(before)))
            compile(after,str(HERE/name),'exec')
    def test_one_ledger_no_invented_selection_release_or_connection(self):
        env=read('ENVELOPE_TEMPLATE01.json');selection=read('SELECTION_TEMPLATE01.json');pins=read('SOURCE_PINS01.json');old=json.loads((ROOT/pins['base_envelope']['path']).read_text())
        self.assertEqual(env['connection'],old['connection']);self.assertNotIn(env['connection']['path'],env['source_files']);self.assertEqual(env['local_only_evidence'],[env['connection']['path']])
        self.assertIsNone(env['selection']);self.assertEqual(env['evidence'],[None]);self.assertEqual(selection['count'],1);self.assertEqual(len(selection['files']),1)
        row=selection['files'][0];self.assertTrue(row['path'].endswith('/pilot-02/2022-07-25/decode_graph/weekly-g_35n27n/events.sqlite'))
        for field in ('bytes','sha256','stat_identity'):self.assertIsNone(row[field])
        for field in ('total_bytes','max_body_bytes','remote'):self.assertIsNone(selection[field])
        self.assertFalse((HERE/'RELEASE_REVIEW01.json').exists());self.assertFalse((HERE/'envelope01.json').exists());self.assertFalse(pins['prospective_entry_exists_claimed'])
    def test_frozen_guard_constants_and_current_source_pins(self):
        tree=ast.parse((HERE/'entry01.py').read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='guarded_run'];self.assertEqual(len(calls),1)
        kwargs={k.arg:k.value for k in calls[0].keywords};expected=read('BINDING_REQUIREMENTS01.json')['resources_unchanged']
        for key in ('memory_max_bytes','memory_high_bytes','memory_swap_max_bytes','reserve_bytes','start_reserve_bytes','wall_seconds','disk_floor_bytes'):
            actual=eval(compile(ast.Expression(kwargs[key]),'<constant>','eval'),{'__builtins__':{},'int':int,'GIB':1024**3});self.assertEqual(actual,expected[key])
        env=read('ENVELOPE_TEMPLATE01.json');self.assertEqual(env['source_files']['tradingagents/research/onchain_replication/resources.py'],'672ff3ed96c7d5ba1ccbdc2355558b10aa823cbda0c3b07d1d2f44923c8b0185');self.assertEqual(env['scanner_sha256'],'deff02766685c1e7fb8628766acf0e0c36dc324da4672f3adc094bfac3e24a74')
        self.assertIn('not 1<=len(rows)<=4096',(HERE/'keep.py').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
