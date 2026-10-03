"""Read-only environment inventory. Torch import is opt-in, CUDA never required."""
from __future__ import annotations
import importlib.metadata
import os
import platform
from pathlib import Path
from .provenance import file_hash


def inventory(root: Path, include_torch: bool = False) -> dict:
    result = {'python': platform.python_version(), 'cpu_count': os.cpu_count(),
              'lock_sha256': file_hash(Path(root) / 'uv.lock'),
              'packages': {p: importlib.metadata.version(p) for p in
                           ('numpy', 'scipy', 'pyarrow', 'torch', 'scikit-learn')}}
    if include_torch:
        import torch
        result.update(cuda_available=torch.cuda.is_available(), torch_version=torch.__version__,
                      cuda_build=torch.version.cuda)
    return result
