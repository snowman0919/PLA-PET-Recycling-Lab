#!/usr/bin/env python3
"""Offline byte-integrity check for a complete design prerelease, never a safety approval."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

MANIFEST = 'PACKAGE_MANIFEST.json'
REQUIRED = {'START_HERE.html', 'verify_package.py', 'repository/README.md',
            'repository/SOURCE_SNAPSHOT.json', 'verification/light/result.json',
            'verification/cad/result.json', 'verification/firmware/rebuild.log'}


def safe_name(name: str) -> str:
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('unsafe path: ' + repr(name))
    p = PurePosixPath(name)
    if p.is_absolute() or any(x in ('', '.', '..') for x in name.split('/')):
        raise ValueError('unsafe path: ' + repr(name))
    if any(ord(c) < 32 for c in name) or str(p) != name:
        raise ValueError('noncanonical path: ' + repr(name))
    return name


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def validate_metadata(data: dict) -> dict[str, dict]:
    expected = {'schema_version': 1, 'release_tag': 'v1.0.0-rc1',
                'release_state': 'FABRICATION_CANDIDATE',
                'physical_validation_state': 'NOT_RUN',
                'safety_certification_state': 'NOT_CERTIFIED',
                'fabrication_authorized': False, 'energization_authorized': False}
    for key, value in expected.items():
        if type(data.get(key)) is not type(value) or data[key] != value:
            raise ValueError('package policy mismatch: ' + key)
    if not re.fullmatch(r'[0-9a-f]{40}', str(data.get('source_commit', ''))):
        raise ValueError('invalid source commit')
    rows = data.get('files')
    if not isinstance(rows, list) or not rows or len(rows) > 20000:
        raise ValueError('invalid file manifest')
    result = {}
    for row in rows:
        name = safe_name(row['path'])
        if name == MANIFEST or name in result:
            raise ValueError('duplicate/self-referential manifest entry')
        if type(row.get('size')) is not int or not 0 <= row['size'] <= 2**30:
            raise ValueError('invalid file size')
        if not re.fullmatch(r'[0-9a-f]{64}', str(row.get('sha256', ''))):
            raise ValueError('invalid file hash')
        result[name] = row
    if len({n.casefold() for n in result}) != len(result):
        raise ValueError('case-insensitive path collision')
    if not REQUIRED <= set(result):
        raise ValueError('missing mandatory files')
    return result

def validate_contents(data: dict, read) -> None:
    head = data['source_commit']
    snapshot = json.loads(read('repository/SOURCE_SNAPSHOT.json'))
    if snapshot.get('source_commit') != head or snapshot.get('energization_authorized') is not False:
        raise ValueError('snapshot identity or authorization mismatch')
    for suite in ('light', 'cad'):
        result = json.loads(read(f'verification/{suite}/result.json'))
        records = result.get('records', [])
        if result.get('head') != head or result.get('status') != 'PASS' or not records:
            raise ValueError('stale or failing CI evidence: ' + suite)
        if result.get('commands') != len(records):
            raise ValueError('CI command coverage mismatch')
        for record in records:
            if record.get('returncode') != 0:
                raise ValueError('nonzero test exit code')
            src = safe_name('repository/' + record['script'])
            log = safe_name(f'verification/{suite}/' + record['log'])
            if sha(read(src)) != record['source_sha256'] or sha(read(log)) != record['log_sha256']:
                raise ValueError('CI source/log digest mismatch')
    fw = json.loads(read('repository/exports/final/firmware/build_manifest.json'))
    digest = fw['binary_sha256']
    binary = read('repository/exports/final/firmware/binaries/filament_recycler_atmega2560.hex')
    if sha(binary) != digest or f'RELEASED_HEX_REPRODUCIBLE_OK sha256={digest}' not in read('verification/firmware/rebuild.log').decode():
        raise ValueError('firmware replay mismatch')
    catalog = json.loads(read('repository/release/handoff_catalog.json'))
    for group in catalog['groups']:
        for name in group['files']:
            read(safe_name('repository/' + name))

def verify(path: Path) -> dict:
    archive = None
    try:
        if path.is_dir():
            base = path.resolve()
            if any(p.is_symlink() for p in base.rglob('*')):
                raise ValueError('symlink in extracted package')
            names = {p.relative_to(base).as_posix() for p in base.rglob('*') if p.is_file()}
            def read(name):
                return (base / safe_name(name)).read_bytes()
        else:
            archive = zipfile.ZipFile(path)
            entries = archive.infolist()
            names = {i.filename for i in entries}
            if len(names) != len(entries) or sum(i.file_size for i in entries) > 4 * 2**30:
                raise ValueError('duplicate or oversized ZIP')
            for item in entries:
                safe_name(item.filename)
                if item.is_dir() or stat.S_ISLNK(item.external_attr >> 16) or item.flag_bits & 1:
                    raise ValueError('nonregular/encrypted ZIP member')
            read = archive.read
        data = json.loads(read(MANIFEST)); rows = validate_metadata(data)
        if names != set(rows) | {MANIFEST}:
            raise ValueError('manifest file coverage mismatch')
        for name, row in rows.items():
            content = read(name)
            if len(content) != row['size'] or sha(content) != row['sha256']:
                raise ValueError('file integrity mismatch: ' + name)
        validate_contents(data, read)
        return {'status': 'COMPLETE_PACKAGE_VERIFY_PASS', 'source_commit': data['source_commit'],
                'files': len(rows), 'physical_validation_state': 'NOT_RUN',
                'safety_certification_state': 'NOT_CERTIFIED'}
    finally:
        if archive is not None:
            archive.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', type=Path, default=Path('.'))
    parser.add_argument('--expected-sha256')
    args = parser.parse_args()
    if not __debug__:
        raise SystemExit('Python optimization is prohibited for release checks')
    if args.expected_sha256:
        if not args.path.is_file() or sha(args.path.read_bytes()) != args.expected_sha256:
            raise SystemExit('external archive SHA-256 mismatch')
    print(json.dumps(verify(args.path), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
