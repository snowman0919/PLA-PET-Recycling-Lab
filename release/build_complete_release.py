#!/usr/bin/env python3
"""Package committed source, fabrication assets and exact-head verification evidence."""
from __future__ import annotations
import argparse
import html
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile
from urllib.parse import quote
from publication_policy import validate_policy
from verify_complete_release import safe_name, sha, verify, validate_contents

ROOT = Path(__file__).resolve().parents[1]
NAME = 'PLA-PET-Recycling-Lab-v1.0.0-rc1-COMPLETE'


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def json_bytes(data) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode()


def info(name: str, executable: bool = False) -> zipfile.ZipInfo:
    obj = zipfile.ZipInfo(name, (2000, 1, 1, 0, 0, 0))
    obj.create_system = 3; obj.compress_type = zipfile.ZIP_DEFLATED
    obj.external_attr = (0o100755 if executable else 0o100644) << 16
    return obj

def overview(catalog: dict, files: dict, head: str) -> bytes:
    sections = []
    for group in catalog['groups']:
        links = []
        for source in group['files']:
            path = 'repository/' + safe_name(source)
            if path not in files:
                raise ValueError('catalog target missing: ' + source)
            links.append(f'<li><a href="{quote(path)}">{html.escape(source)}</a></li>')
        sections.append('<section><h2>' + html.escape(group['title']) + '</h2><ul>' + ''.join(links) + '</ul></section>')
    listing = json.dumps(sorted(files), ensure_ascii=False).replace('<', '\\u003c')
    image = quote('repository/' + catalog['primary_render'])
    page = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PPR 제작 인수인계</title>
<style>body{font:16px/1.65 system-ui,sans-serif;background:#f5f7fa;color:#182b38;margin:0}main{max-width:1140px;margin:auto;padding:38px 28px}header{border-bottom:3px solid #276276;padding-bottom:20px}h1{font-size:34px;line-height:1.3}h2{font-size:20px}a{color:#15597a;overflow-wrap:anywhere}code{overflow-wrap:anywhere}.notice{background:#fff1db;border-left:5px solid #ad6816;padding:18px;margin:22px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:20px}section{background:white;border:1px solid #d8e0e7;border-radius:8px;padding:22px}li{margin:9px 0}img{max-width:100%;height:auto;display:block;margin:auto}input{box-sizing:border-box;width:100%;font-size:18px;padding:12px;margin:15px 0}small{color:#485b68}</style><main>
<header><small>DESIGN PRERELEASE / v1.0.0-rc1</small><h1>PPR 전체 제작 인수인계</h1><p>코드 · 상세 설계 · STEP/FreeCAD · 제조도면 · BOM · 전기 · 펌웨어 · 조립 · 물리시험 양식</p><p>Source commit: <code>HEAD_TOKEN</code></p></header>
<div class="notice"><strong>FABRICATION_CANDIDATE / 물리시험 NOT_RUN / 안전인증 NOT_CERTIFIED</strong><br>MVP와 최종 제품은 같은 실물입니다. 공개 배포는 구매·가공·통전·양산 승인이 아닙니다. 수령품·열처리·교정·물리검증의 HOLD는 유지합니다.</div>
<p>먼저 <code>python3 verify_package.py .</code>로 파일 무결성을 검사하세요. 검증은 실행 전에 실시하며, 작업용 복사본에서 재생성하세요. 패키지 자체의 해시는 GitHub Release의 SHA256SUMS와 대조합니다.</p>
<section><h2>최신 전체 모델: GGM-FULL-ASM</h2><p>통합 외형 470 × 729 × 930 mm. 기본 프레임 470 × 700 mm와 구분합니다. Hard envelope 안이지만 선호 Y720 mm보다 9 mm 큽니다. 구매품 내부·물리성능을 보증하는 CAD가 아닙니다.</p><img src="IMAGE_TOKEN" alt="실제 GGM native CAD에서 렌더한 전체 형상"><p><small>도면 치수·재료·공차와 GGM R2 변경이 우선합니다. 구형 기본 조립 모델은 별도 참조이며 최신 배치로 사용하지 않습니다.</small></p></section>
<div class="grid">SECTIONS_TOKEN</div><h2>전체 파일 검색</h2><input id="search" placeholder="예: EX-SCR, assembly, firmware, P9"><p id="count"></p><div id="files"></div>
<script>const all=FILES_TOKEN;function update(){const q=document.getElementById('search').value.toLowerCase();const found=all.filter(x=>x.toLowerCase().includes(q));document.getElementById('count').textContent=found.length+' files / 최대 120개 표시';const box=document.getElementById('files');box.replaceChildren();for(const name of found.slice(0,120)){const p=document.createElement('p'),a=document.createElement('a');a.textContent=name;a.href=name.split('/').map(encodeURIComponent).join('/');p.append(a);box.append(p)}}document.getElementById('search').addEventListener('input',update);update();</script></main></html>'''
    return page.replace('HEAD_TOKEN', head).replace('IMAGE_TOKEN', image).replace('SECTIONS_TOKEN', ''.join(sections)).replace('FILES_TOKEN', listing).encode()

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    head = git('rev-parse', 'HEAD').decode().strip()
    evidence = args.evidence.resolve()
    if not evidence.is_relative_to(ROOT):
        raise ValueError('evidence must stay inside the repository')
    files = {}; executable = set()
    stream = io.BytesIO(git('archive', '--format=tar', head))
    with tarfile.open(fileobj=stream) as archive:
        for member in archive:
            if member.isdir():
                continue
            name = safe_name(member.name)
            if not member.isfile() or '.env' in Path(name).parts or name.endswith(('.pem', '.key', '.p12')):
                raise ValueError('nonregular or sensitive tracked source: ' + name)
            content = archive.extractfile(member).read()
            if re.search(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{70,}', content):
                raise ValueError('potential secret in committed source: ' + name)
            files['repository/' + name] = content
            if member.mode & 0o111:
                executable.add('repository/' + name)
    policy = json.loads(files['repository/release/publication_policy.json'])
    validate_policy(policy)
    files['repository/SOURCE_SNAPSHOT.json'] = json_bytes({
        'schema_version': 1, 'source_commit': head, 'git_tree': git('rev-parse', 'HEAD^{tree}').decode().strip(),
        'physical_validation_state': 'NOT_RUN', 'energization_authorized': False})
    for suite in ('light', 'cad'):
        result_path = evidence/suite/'result.json'
        result = json.loads(result_path.read_text())
        for name in ['result.json', 'SUMMARY.md', *[r['log'] for r in result['records']]]:
            files[f'verification/{suite}/' + safe_name(name)] = (evidence/suite/name).read_bytes()
    for name in ('firmware/rebuild.log', 'github_runs.json', 'regeneration.json'):
        source = evidence/name
        if not source.is_file():
            raise ValueError('missing execution evidence: ' + name)
        files['verification/' + name] = source.read_bytes()
    runs = json.loads(files['verification/github_runs.json'])
    for workflow in ('CI-LIGHT', 'CI-FULL'):
        if not any(r.get('workflowName') == workflow and r.get('headSha') == head and
                   r.get('conclusion') == 'success' and r.get('status') == 'completed' for r in runs):
            raise ValueError('missing exact-head GitHub success: ' + workflow)
    for prefix in ('PLA-PET-Recycling-Lab-v1.0.0-rc1-FABRICATION', 'PPR-v08-PHYSICAL-VALIDATION-LAUNCH-' + head[:8]):
        path = ROOT/'dist'/f'{prefix}.zip'
        with zipfile.ZipFile(path) as archive:
            if prefix.startswith('PLA-'):
                bound = json.loads(archive.read('00_START_HERE/release_manifest.json'))['source_commit']
            else:
                bound = json.loads(archive.read('00_READ_FIRST/STATUS.json'))['head']
        if bound != head:
            raise ValueError('stale child package: ' + path.name)
        files['packages/' + path.name] = path.read_bytes()
    files['verify_package.py'] = files['repository/release/verify_complete_release.py']
    catalog = json.loads(files['repository/release/handoff_catalog.json'])
    files['START_HERE.html'] = overview(catalog, files, head)
    executable.add('verify_package.py')
    import sys
    subprocess.run([sys.executable, 'release/verify_fabrication_release.py'], cwd=ROOT, check=True)
    launch = ROOT/'dist'/('PPR-v08-PHYSICAL-VALIDATION-LAUNCH-' + head[:8] + '.zip')
    subprocess.run([sys.executable, 'validation/physical_v08/validate_physical_launch_package.py', str(launch)], cwd=ROOT, check=True)
    for name in ('v08_full_compliance', 'v08_release_inventory'):
        source = ROOT/'validation/results'/f'{name}.json'
        report = json.loads(source.read_text()); checks = report.get('checks', {})
        if not checks or not all(v is True or isinstance(v, dict) and v.get('status') == 'PASS' for v in checks.values()):
            raise ValueError('release gate unresolved: ' + name)
        files[f'verification/{name}.json'] = source.read_bytes()
    data = {'schema_version': 1, 'release_tag': 'v1.0.0-rc1', 'source_commit': head,
            'release_state': 'FABRICATION_CANDIDATE', 'physical_validation_state': 'NOT_RUN',
            'safety_certification_state': 'NOT_CERTIFIED', 'fabrication_authorized': False,
            'energization_authorized': False,
            'files': [{'path': n, 'size': len(c), 'sha256': sha(c)} for n, c in sorted(files.items())]}
    validate_contents(data, files.__getitem__)
    files['PACKAGE_MANIFEST.json'] = json_bytes(data)
    output = ROOT/'dist'/f'{NAME}.zip'; output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, content in sorted(files.items()):
            archive.writestr(info(name, name in executable), content, compresslevel=9)
    result = verify(output)
    result.update(path=str(output), sha256=sha(output.read_bytes()))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
