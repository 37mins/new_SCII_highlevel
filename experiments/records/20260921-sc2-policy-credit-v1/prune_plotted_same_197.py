"""One-shot, exact allowlist pruning authorized 2026-09-24; stdin is the frozen plan.
Dry-run is default. --apply irreversibly unlinks only model/optimizer files.
No recursive deletion, checkpoint reads, process termination, or queue mutation.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

ROOTS = (
    "/var/jfsCache/sc2-qwen-l7same96-197-20260922-r1/runs/train96/checkpoints",
    "/var/jfsCache/sc2-l7-followup197-20260922-r4/spb-same/long/runs/train96/checkpoints",
)

def expected_paths():
    return {f"{root}/global_step_{step}/actor/{kind}_world_size_8_rank_{rank}.pt"
            for root in ROOTS for step in range(16, 89, 8)
            for kind in ("model", "optim") for rank in range(8)}

def validate_plan(plan):
    rows = plan["targets"]
    assert len(rows) == 320 and len({r["path"] for r in rows}) == 320
    assert {r["path"] for r in rows} == expected_paths(), "allowlist mismatch"
    assert all(r["nlink"] == 1 and r["bytes"] > 0 for r in rows)
    assert plan["expected_logical_bytes"] == sum(r["bytes"] for r in rows)
    assert plan["expected_allocated_bytes"] == sum(r["allocated_bytes"] for r in rows)
    assert not ({r["path"] for r in plan["retained_inventory"]} & expected_paths())

def unchanged(row):
    p = Path(row["path"])
    assert p.resolve(strict=True) == p, f"symlink path: {p}"
    s = p.lstat()
    assert stat.S_ISREG(s.st_mode), f"not regular: {p}"
    for key, actual in (("bytes", s.st_size), ("allocated_bytes", s.st_blocks * 512),
                        ("inode", s.st_ino), ("device", s.st_dev), ("nlink", s.st_nlink)):
        assert row[key] == actual, f"changed {key}: {p}"

def receipts_unchanged(plan):
    for name, expected in plan["preserved_receipts"].items():
        p = Path(name)
        assert p.resolve(strict=True) == p and p.stat().st_size == expected["bytes"]
        assert expected["bytes"] < 1024 * 1024
        assert hashlib.sha256(p.read_bytes()).hexdigest() == expected["sha256"], name

def references_clear():
    # Read selected fields only: never inspect environment variables or process arguments.
    ids = subprocess.check_output(["docker", "ps", "-q"], text=True, timeout=15).split()
    for cid in ids:
        raw = subprocess.check_output(["docker", "inspect", "--format", "{{json .Mounts}}", cid],
                                      text=True, timeout=15)
        for mount in json.loads(raw):
            source = mount["Source"].rstrip("/")
            assert not any(root == source or root.startswith(source + "/") or source.startswith(root + "/")
                           for root in ROOTS), f"running container references candidate root: {cid}"
    # Fail closed on permissions/unknown errors; exited processes/descriptors may disappear.
    open_refs = []
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            fds = list((proc / "fd").iterdir())
            maps = (proc / "maps").read_text()
        except (FileNotFoundError, ProcessLookupError):
            continue
        for fd in fds:
            try:
                target = os.readlink(fd)
            except (FileNotFoundError, ProcessLookupError):
                continue
            if target.removesuffix(" (deleted)") in expected_paths():
                open_refs.append({"pid": int(proc.name), "file": target})
        if any(path in maps for path in expected_paths()):
            open_refs.append({"pid": int(proc.name), "memory_mapping": True})
    assert not open_refs, f"candidate open references: {open_refs}"

def free_bytes():
    s = os.statvfs("/var/jfsCache")
    return s.f_bavail * s.f_frsize

def main():
    assert sys.argv[1:] in ([], ["--apply"]), "only --apply is accepted"
    raw = sys.stdin.buffer.read()
    plan = json.loads(raw)
    validate_plan(plan)
    receipts_unchanged(plan)
    for row in plan["targets"] + plan["retained_inventory"]:
        unchanged(row)
    references_clear()
    before = free_bytes()
    print(json.dumps({"event": "preflight_passed", "epoch": time.time(),
                      "apply": bool(sys.argv[1:]), "targets": 320, "open_references": 0,
                      "plan_sha256": hashlib.sha256(raw).hexdigest(), "free_bytes": before}), flush=True)
    if not sys.argv[1:]:
        return
    count = total = 0
    try:
        for row in plan["targets"]:
            unchanged(row)
            Path(row["path"]).unlink()
            count += 1
            total += row["bytes"]
            print(json.dumps({"event": "unlinked", "path": row["path"], "bytes": row["bytes"]}), flush=True)
        assert all(not Path(row["path"]).exists() for row in plan["targets"])
        receipts_unchanged(plan)
        for row in plan["retained_inventory"]:
            unchanged(row)
        print(json.dumps({"event": "completed", "epoch": time.time(), "deleted_files": count,
                          "deleted_logical_bytes": total, "free_before": before, "free_after": free_bytes(),
                          "retained_files_unchanged": len(plan["retained_inventory"]),
                          "preserved_receipts_unchanged": len(plan["preserved_receipts"]),
                          "queue_modified": False, "recovery": "No weight backup; intermediate CPs non-resumable."}), flush=True)
    except Exception:
        print(json.dumps({"event": "partial_failure", "deleted_files": count,
                          "deleted_logical_bytes": total, "epoch": time.time()}), flush=True)
        raise

if __name__ == "__main__":
    main()
