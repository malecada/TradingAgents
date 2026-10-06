"""Only two independent-review regressions and exact successor inverse."""
from pathlib import Path
import copy,hashlib,json,types,unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
fixture=types.ModuleType('fixture');fixture.__file__=str(HERE/'check01.py')
exec(compile((HERE/'check01.py').read_bytes(),fixture.__file__,'exec'),vars(fixture))
r,m=fixture.r,fixture.m

class Check(unittest.TestCase):
    def test_two_fixed_seams(self):
        c,docs=fixture.Check().gate_fixture()
        def invoke(records):
            with patch.object(m,'recovery'),patch.object(m,'current'),patch.object(m,'metadata',side_effect=lambda root,p,pin:json.dumps(records[p]).encode()),patch.object(r,'retained'),patch.object(r.os.path,'lexists',return_value=False):r.validate(m,c)
        invoke(docs)
        for role,key,value in [('retire_outer','cleanup_verified',True),('relocation_receipt','identity','unrelated-maintenance')]:
            bad=copy.deepcopy(docs);bad[c['relocation'][role]['path']][key]=value
            with self.subTest(role=role),self.assertRaises(ValueError):invoke(bad)

    def test_exact_inverse_and_parent_preserved(self):
        delta=json.loads((HERE/'SUCCESSOR_DELTA02.json').read_text());old=ROOT/delta['parent']
        restored=(HERE/'retire01.py').read_text()
        for change in reversed(delta['retire_ordered_replacements']):
            self.assertEqual(restored.count(change['after']),1);restored=restored.replace(change['after'],change['before'])
        self.assertEqual(restored,(old/'retire01.py').read_text())
        for name,expected in delta['all_parent_files'].items():self.assertEqual(hashlib.sha256((old/name).read_bytes()).hexdigest(),expected)
        for name in ['recovery01.py','SELECTION_TEMPLATE01.json','RELEASE_TEMPLATE01.json','RELOCATION_OUTCOME_REQUIRED01.json']:
            self.assertEqual((HERE/name).read_bytes(),(old/name).read_bytes())
        a=json.loads((HERE/'SOURCE_PINS01.json').read_text());b=json.loads((old/'SOURCE_PINS01.json').read_text())
        a['recovery']['path']=b['recovery']['path'];self.assertEqual(a,b)
        self.assertEqual(hashlib.sha256((HERE/'SOURCE_PINS01.json').read_bytes()).hexdigest(),r.PINS_SHA)


if __name__=='__main__':unittest.main(verbosity=2)
