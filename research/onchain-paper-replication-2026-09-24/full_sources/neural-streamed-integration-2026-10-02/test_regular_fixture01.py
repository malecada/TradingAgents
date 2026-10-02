"""Stdlib fixture isolation regression; never imports pytest or numerical libraries."""
import argparse
import ast
from pathlib import Path
import stat
import unittest

parser=argparse.ArgumentParser(); parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--root',type=Path,required=True); args=parser.parse_args()
tree=ast.parse(args.source.read_bytes())
node=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='regular_fixture'),None)
names=['test_schema2_real_admission_source_and_original_model','test_schema2_refuses_checkpoint_block_and_source_body','test_actual_selected_tiny_resource_checkpoint_identity']
scope={'Path':Path,'stat':stat,'NAMES':['test_real_constructor_default_selected_initial_rng_and_detachment',*names]}
if node is not None:
    node.decorator_list=[]
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(args.source),'exec'),scope)
helper=scope.get('regular_fixture'); args.root.mkdir(mode=0o700)


class RegularFixture(unittest.TestCase):
    def require_helper(self):self.assertIsNotNone(helper,'owned regular-directory fixture missing')

    def test_three_fixtures_remain_regular_owned_distinct(self):
        self.require_helper(); root=args.root/'distinct'; root.mkdir()
        made=[helper(root,name) for name in names]
        self.assertEqual(len(set(made)),3)
        self.assertEqual(set(root.iterdir()),set(made))
        self.assertTrue(all(stat.S_ISDIR(p.lstat().st_mode) and p.resolve()==p and p.parent==root for p in made))

    def test_duplicate_and_unknown_request_refused(self):
        self.require_helper(); root=args.root/'refusals'; root.mkdir()
        helper(root,names[0])
        with self.assertRaises(FileExistsError):helper(root,names[0])
        for name in ('../escape','unknown'):
            with self.assertRaises(ValueError):helper(root,name)

    def test_symlink_parent_refused(self):
        self.require_helper(); actual=args.root/'actual'; actual.mkdir()
        link=args.root/'link'; link.symlink_to(actual,target_is_directory=True)
        with self.assertRaises(ValueError):helper(link,names[0])
        self.assertEqual(list(actual.iterdir()),[])


if __name__=='__main__':unittest.main(argv=['test_regular_fixture01'],verbosity=2)
