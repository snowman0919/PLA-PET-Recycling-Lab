"""Verify a committed tree, never uncommitted repairs in the working folder."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def export_snapshot(root: Path, revision: str, destination: Path) -> dict:
    if revision.startswith('-') or not re.fullmatch(r'[A-Za-z0-9_./-]+', revision):
        raise ValueError('invalid revision')
    head = git(root, 'rev-parse', '--verify', revision+'^{commit}').decode().strip()
    tree = git(root, 'rev-parse', head+'^{tree}').decode().strip()
    algorithm = git(root, 'rev-parse', '--show-object-format').decode().strip()
    expected = {}
    for row in git(root, 'ls-tree', '-rz', '--full-tree', head).split(b'\0'):
        if not row:
            continue
        metadata, path = row.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        if kind != 'blob' or mode not in {'100644', '100755'}:
            raise ValueError('nonregular committed file: '+path.decode())
        expected[path.decode()] = oid
    destination.mkdir(parents=True, exist_ok=False)
    observed = set()
    with tarfile.open(fileobj=io.BytesIO(git(root, 'archive', '--format=tar', head))) as archive:
        for entry in archive:
            if entry.isdir():
                continue
            path = PurePosixPath(entry.name)
            if (not entry.isfile() or path.is_absolute() or '..' in path.parts
                    or '.git' in path.parts or entry.name not in expected):
                raise ValueError('unsafe or unexpected archive member: '+entry.name)
            data = archive.extractfile(entry).read()
            oid = hashlib.new(algorithm, b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            if oid != expected[entry.name] or entry.name in observed:
                raise ValueError('archive differs from committed blob: '+entry.name)
            target = destination/entry.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data); target.chmod(entry.mode & 0o777)
            observed.add(entry.name)
    if observed != set(expected):
        raise ValueError('archive omitted committed files')
    identity = {'schema_version': 1, 'source_commit': head, 'git_tree': tree,
                'physical_validation_state': 'NOT_RUN', 'energization_authorized': False}
    marker = destination/'SOURCE_SNAPSHOT.json'
    if marker.exists():
        raise ValueError('committed snapshot marker cannot be overwritten')
    marker.write_text(json.dumps(identity, indent=2)+'\n')
    return dict(identity, verified_git_blobs=len(observed))


def main():
    if not __debug__:
        raise SystemExit('optimized Python disables regression assertions')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', default='HEAD')
    parser.add_argument('--suite', choices=['light', 'cad'], default='light')
    args = parser.parse_args()
    output = ROOT/'.build/git-snapshot-checks'
    output.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='check-', dir=output))
    snapshot = work/'repository'
    result = export_snapshot(ROOT, args.revision, snapshot)
    tmp = work/'tmp'; tmp.mkdir()
    env = dict(os.environ, TMPDIR=str(tmp), PYTHONDONTWRITEBYTECODE='1',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', QT_QPA_PLATFORM='offscreen')
    env.pop('PYTHONOPTIMIZE', None)
    command = [sys.executable, 'validation/ci_v08.py', '--suite', args.suite]
    with (work/'execution.txt').open('w') as log:
        run = subprocess.run(command, cwd=snapshot, env=env, stdout=log, stderr=log, timeout=3600)
    report = snapshot/'.build/ci-v08'/args.suite/'result.json'
    ci = json.loads(report.read_text()) if report.is_file() else {}
    passed = (run.returncode == 0 and ci.get('status') == 'PASS'
              and ci.get('head') == result['source_commit'])
    result.update(status='PASS' if passed else 'FAIL', suite=args.suite,
                  returncode=run.returncode, commands=ci.get('commands'),
                  scope='Committed bytes in an isolated source export; no worktree overlay',
                  execution_log_sha256=hashlib.sha256((work/'execution.txt').read_bytes()).hexdigest())
    (work/'result.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(result, evidence=str(work.relative_to(ROOT))), indent=2), flush=True)
    if not passed:
        print((work/'execution.txt').read_text(errors='replace')[-5000:])
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
