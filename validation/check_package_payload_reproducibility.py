"""발행 게이트를 우회하지 않고 payload만 메모리에서 두 환경으로 비교한다."""
import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release"))
from build_fabrication_release import collect, zi


def payload():
    files = collect()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as package:
        for name, (source, _) in sorted(files.items()):
            package.writestr(zi(name), source.read_bytes())
    data = buffer.getvalue()
    return {"file_count": len(files), "serialized_bytes": len(data),
            "payload_zip_sha256": hashlib.sha256(data).hexdigest()}


def main():
    if sys.argv[1:] == ["--digest"]:
        print(json.dumps({"payload": payload(), "python": sys.version}))
        return
    output = ROOT / "validation/results/package_payload_reproducibility.json"
    result = {"status": "INCOMPLETE", "fabrication_readiness": "HOLD",
              "physical_validation_state": "NOT_RUN", "final_release_reproducibility": "NOT_PROVEN",
              "scope": "Current collect() payload only; no generated release metadata or fabrication ZIP written"}
    output.write_text(json.dumps(result, indent=2) + "\n")
    runs = [json.loads(subprocess.check_output(
        [exe, "-I", str(Path(__file__).resolve()), "--digest"], cwd=ROOT, text=True, timeout=120))
        for exe in (sys.executable, "/usr/bin/python3")]
    assert runs[0]["payload"] == runs[1]["payload"], "runtime payload mismatch or changing input snapshot"
    result.update(status="PASS", **runs[0]["payload"], python_versions=[r["python"] for r in runs],
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("PACKAGE_PAYLOAD_REPRODUCIBILITY_PASS files=" + str(result["file_count"]) + " release=HOLD")


if __name__ == "__main__":
    main()
