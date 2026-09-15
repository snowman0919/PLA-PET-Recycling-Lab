"""Fail before publishing commits whose isolated light suite is not passing."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OID = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')


def revisions(text):
    found = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 4 or not OID.fullmatch(fields[1]) or not OID.fullmatch(fields[3]):
            raise ValueError('invalid pre-push ref input')
        if set(fields[1]) == {'0'}:
            continue
        if fields[1] not in found:
            found.append(fields[1])
    return found


def check_push(text, execute=subprocess.run):
    for revision in revisions(text):
        command = ['nix', 'develop', '--command', 'python3',
                   'validation/verify_git_snapshot.py', '--revision', revision, '--suite', 'light']
        result = execute(command, cwd=ROOT, check=False)
        if result.returncode:
            raise RuntimeError('Push withheld: committed snapshot failed: '+revision)


if __name__ == '__main__':
    try:
        check_push(sys.stdin.read())
    except (ValueError, RuntimeError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
