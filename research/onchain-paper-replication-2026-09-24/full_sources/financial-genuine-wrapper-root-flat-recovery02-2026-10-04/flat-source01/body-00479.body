"""Bounded monotonic observation of actual same-run registered output publication.

This helper is not admission by itself. The terminal sealer supplies the exact
baseline only after completing its original strictly checked transition.
"""
import importlib.util
from pathlib import Path
import stat
from tradingagents.research import lifecycle

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('terminal_outputs_reader',HERE.parent/'pair-component-reader-2026-10-01/reader.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
require=reader.require

class Outputs:
    def __init__(self,run,baseline,*,max_bytes):
        require(type(run) is lifecycle.ResearchRun,'actual output run required')
        require(type(max_bytes) is int and 0<max_bytes<=reader.MANIFEST_LIMIT,'bounded output metadata cap required')
        require(type(baseline) is dict and bool(baseline),'exact output baseline required')
        self._run=run;self._root=run.admission.root;self._directory=run.directory/'outputs'
        self._allowed=frozenset(run.admission.experiment['outputs']);self._cap=max_bytes
        self._hashes=dict(baseline);self._signatures={};self._directory_identity=None
        with lifecycle._lock(self._root):
            require(run._published_outputs==baseline,'output baseline differs from actual publication')
            self._check_locked()
    def check(self):
        with lifecycle._lock(self._root):self._check_locked()
    def _check_locked(self):
        run=self._run;run._active()
        require(run.admission.root==self._root and run.directory/'outputs'==self._directory
            and frozenset(run.admission.experiment['outputs'])==self._allowed,'output owner or registration changed')
        path=self._directory;value=path.lstat();identity=(value.st_dev,value.st_ino)
        require(path.resolve()==path and path.is_relative_to(self._root) and stat.S_ISDIR(value.st_mode)
            and value.st_dev==self._root.stat().st_dev
            and (self._directory_identity is None or self._directory_identity==identity),'output directory changed')
        require(type(run._published_outputs) is dict and len(run._published_outputs)<=len(self._allowed),'output publication registry differs')
        current=dict(run._published_outputs)
        require(all(type(n) is str and Path(n).name==n and n in self._allowed
            and type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h) for n,h in current.items()),'unregistered output or invalid published hash')
        require(all(current.get(n)==h for n,h in self._hashes.items()),'observed output deleted or rebound')
        reader.inventory(path,{path/n for n in current})
        signatures={}
        for name,sha in current.items():
            with reader.opened(path/name,self._root,self._signatures.get(name)) as (stream,sig):
                require(0<sig[2]<=self._cap,'output metadata byte cap exceeded')
                require(reader.digest_stream(stream,sig[2])==sha,'published output bytes differ')
                signatures[name]=sig
        reader.inventory(path,{path/n for n in current})
        require(run._published_outputs==current,'output registry changed during observation')
        # Admit all new observations together, only after every file passed.
        self._hashes=current;self._signatures=signatures;self._directory_identity=identity
