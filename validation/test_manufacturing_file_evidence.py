"""부품별 누락/변조/경로 이탈을 폴더 단위 PASS로 숨기지 못하게 한다."""
from pathlib import Path
from tempfile import TemporaryDirectory
from v08_full_compliance import manufacturing_files_current, sha, PRINT_BINDINGS


def main():
    with TemporaryDirectory() as folder:
        base = Path(folder)
        row = {}
        for field, digest in (("step_file", "sha256_step"), ("dxf_file", "sha256_dxf"), ("drawing_pdf", "sha256_pdf")):
            path = base / field
            path.write_text("known artifact")
            row[field], row[digest] = path.name, sha(path)
        assert manufacturing_files_current(base, row)
        step = {"file": row["step_file"], "sha256": row["sha256_step"]}
        assert manufacturing_files_current(base, step, (("file", "sha256"),))
        for value in ("", "missing", "../outside"):
            assert not manufacturing_files_current(base, {**step, "file": value}, (("file", "sha256"),))
        for field in ("step_file", "dxf_file", "drawing_pdf"):
            for value in ("", "missing", "../outside"):
                assert not manufacturing_files_current(base, {**row, field: value})
        (base / row["step_file"]).write_text("changed")
        assert not manufacturing_files_current(base, row)
        assert not manufacturing_files_current(base, step, (("file", "sha256"),))
        printed = {}
        for field, digest in PRINT_BINDINGS:
            path = base / field
            path.write_text("print artifact")
            printed[field], printed[digest] = path.name, sha(path)
        assert manufacturing_files_current(base, printed, PRINT_BINDINGS)
        for field, digest in PRINT_BINDINGS:
            assert not manufacturing_files_current(base, {**printed, field: "missing"}, PRINT_BINDINGS)
            assert not manufacturing_files_current(base, {**printed, digest: "wrong"}, PRINT_BINDINGS)
    print("MANUFACTURING_FILE_EVIDENCE_PASS missing/path/hash cases")


if __name__ == "__main__":
    main()
