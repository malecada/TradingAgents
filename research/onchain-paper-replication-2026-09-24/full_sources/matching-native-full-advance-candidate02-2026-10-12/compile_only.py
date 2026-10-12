"""Root-only finite compiler hook; never loads or executes the extension."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sysconfig


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root-reviewed-compile-only',action='store_true',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cc',default='/usr/bin/cc')
    args=parser.parse_args()
    source=Path(__file__).resolve().with_name('native_full.c')
    source_sha=hashlib.sha256(source.read_bytes()).hexdigest()
    if source_sha!='c76737a37682dbd932896ba1d836a54a6fce1dec1db5ec95dcd7ea8af151432d':
        raise ValueError('frozen native02 source differs')
    args.output.mkdir(exist_ok=False)
    library=args.output/('_native_full'+sysconfig.get_config_var('EXT_SUFFIX'))
    command=[args.cc,'-shared','-fPIC','-O3','-std=c11','-fno-fast-math',
             '-ffp-contract=off','-fno-associative-math','-fno-unsafe-math-optimizations',
             '-frounding-math','-I'+sysconfig.get_paths()['include'],str(source),'-o',str(library),'-lm']
    result=subprocess.run(command,capture_output=True,text=True,timeout=30,
                          env={k:os.environ[k] for k in ('PATH','TMPDIR') if k in os.environ})
    record=dict(scope='Root compile-only; no extension load or numerical imports',
        command=command,exit=result.returncode,stdout=result.stdout,stderr=result.stderr,
        source_sha256=source_sha,library_path=str(library),
        library_sha256=hashlib.sha256(library.read_bytes()).hexdigest() if result.returncode==0 else None)
    (args.output/'COMPILE01.json').write_text(json.dumps(record,indent=2)+'\n')
    if result.returncode:raise SystemExit(result.returncode)


if __name__=='__main__':main()
