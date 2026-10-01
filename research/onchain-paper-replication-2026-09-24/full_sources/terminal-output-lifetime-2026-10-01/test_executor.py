"""New-identity registered executor/replay check against successor output lease."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
base=load('output_lifetime_executor_fixture',HERE.parent/'native-batch-executor-2026-10-01/test_executor.py')

class Tests(base.Tests):
    def test_native_terminal_features_fit_checkpoint_predict_and_refuse_duplicate_batch(self):
        original=base.base.load
        def selected(name,path):
            if Path(path).name=='native_map.py':return load('output_lifetime_native_candidate',HERE/'native_map.py')
            return original(name,path)
        with patch.object(base.base,'load',side_effect=selected):
            super().test_native_terminal_features_fit_checkpoint_predict_and_refuse_duplicate_batch()

if __name__=='__main__':unittest.main(verbosity=2)
