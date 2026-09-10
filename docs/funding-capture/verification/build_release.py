"""Build and inspect a local allowlisted source archive; never deploy it."""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[3]
ALLOW = ['tradingagents', 'cli', 'pyproject.toml', 'README.md', 'LICENSE', 'uv.lock',
         'scripts/predlab_s1_paper.py', 'scripts/predlab_s1_live.py',
         'scripts/predlab_journal_backup.sh', 'scripts/predlab_journal_backup.py',
         'scripts/predlab_capture_funding.py']


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    commit = git('rev-parse', '--verify', args.commit + '^{commit}').decode().strip()
    prefix = 'ta-source-' + commit + '/'
    expected = set(git('ls-tree', '-r', '--name-only', commit, '--', *ALLOW).decode().splitlines())
    assert expected and all('.env' != Path(name).name and 'node_modules' not in Path(name).parts for name in expected)
    raw = git('archive', '--format=tar', '--prefix=' + prefix, commit, '--', *ALLOW)
    memory = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as original, tarfile.open(fileobj=memory, mode='w:') as output:
        for member in original.getmembers():
            assert member.name.startswith(prefix.rstrip('/')) and not member.issym() and not member.islnk()
            output.addfile(member, original.extractfile(member) if member.isfile() else None)
        marker = (commit + '\n').encode()
        member = tarfile.TarInfo(prefix + 'SOURCE_COMMIT')
        member.size, member.mode, member.mtime = len(marker), 0o644, 0
        output.addfile(member, io.BytesIO(marker))
    compressed = gzip.compress(memory.getvalue(), mtime=0)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    archive = args.output_dir / (prefix.rstrip('/') + '.tar.gz')
    with archive.open('xb') as stream:
        stream.write(compressed)
    digest = hashlib.sha256(compressed).hexdigest()
    (args.output_dir / 'SHA256SUMS').write_text(f'{digest}  {archive.name}\n')
    inventory = []
    with tarfile.open(archive, 'r:gz') as package:
        files = [member for member in package.getmembers() if member.isfile()]
        assert {member.name.removeprefix(prefix) for member in files} == expected | {'SOURCE_COMMIT'}
        for member in files:
            name = member.name.removeprefix(prefix)
            contents = package.extractfile(member).read()
            original = (commit + '\n').encode() if name == 'SOURCE_COMMIT' else git('show', commit + ':' + name)
            assert contents == original
            inventory.append({'path':name, 'bytes':len(contents), 'sha256':hashlib.sha256(contents).hexdigest()})
        with tempfile.TemporaryDirectory(prefix='funding-release-check-') as directory:
            package.extractall(directory, filter='data')
            module_path = Path(directory) / prefix / 'tradingagents/predlab/funding_capture.py'
            spec = importlib.util.spec_from_file_location('release_capture_check', module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            identity = module.source_identity()
            assert identity == {'git_commit':commit, 'source_identity_method':'release_marker'}
    report = dict(source_commit=commit, archive=str(archive.resolve()), sha256=digest,
        compressed_bytes=len(compressed), files=len(inventory), source_allowlist=ALLOW,
        gitless_source_identity=identity, archive_files_match_commit=True,
        uploaded=False, deployed=False, package_inventory=inventory)
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'package_inventory'}))


if __name__ == '__main__':
    main()
