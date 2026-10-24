"""Remove only explicitly verified generated Next output; never touches data/backups."""
from pathlib import Path
import hashlib
import json
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/disk-optimization"
TARGETS = {
    "inactive": [
        "backend/.cad-proof-output/workspace-frontend/.next",
        "backend/.cad-proof-output/workspace-production/.next",
        "frontend/.next",
    ],
    "stopped-frontend-cache": ["frontend/.next-phase1/dev/cache"],
}


def main():
    phase = sys.argv[1]
    assert phase in TARGETS
    OUT.mkdir(exist_ok=True)
    manifest = OUT / ("removed-" + phase + ".jsonl")
    assert not manifest.exists() or manifest.stat().st_size == 0, "Do not overwrite an earlier removal manifest"
    removed = 0
    size = 0
    with manifest.open("w", encoding="utf-8") as evidence:
        for relative in TARGETS[phase]:
            target = (ROOT / relative).resolve(strict=True)
            assert target.is_relative_to(ROOT) and target != ROOT
            assert not target.is_symlink() and not target.is_junction()
            build = target if target.name == ".next" else target.parent
            assert json.loads((build / "package.json").read_text())["type"] == "commonjs"
            assert (build / "server").is_dir() or (build / "dev/server").is_dir()
            paths = []
            for base, dirs, names in os.walk(target, followlinks=False):
                for name in dirs + names:
                    path = Path(base) / name
                    assert not path.is_symlink() and not path.is_junction(), str(path)
                    assert path.resolve().is_relative_to(target)
                for name in names:
                    path = Path(base) / name
                    assert path.suffix.lower() not in {".db", ".sqlite", ".sqlite3", ".dxf", ".brep", ".step", ".tcl", ".pdf"}, "Unexpected data in build tree"
                    paths.append(path)
            # Manifest is flushed before deletion; all targets were resolved and checked.
            for path in paths:
                data = path.read_bytes()
                evidence.write(json.dumps({"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "reason": "Verified regenerable Next.js build/cache; source and dependencies retained", "phase": phase}) + "\n")
                evidence.flush()
                path.unlink()
                removed += 1
                size += len(data)
            for base, dirs, names in os.walk(target, topdown=False):
                Path(base).rmdir()
    print(json.dumps({"phase": phase, "removed_files": removed, "removed_bytes": size, "GB": size / 1e9, "finished": time.strftime("%Y-%m-%d %H:%M:%S")}))


if __name__ == "__main__":
    main()
