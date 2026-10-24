"""Recursive logical-byte inventory, including hidden/Git/backup files, without junction duplication."""
from pathlib import Path
from collections import defaultdict
import json
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/disk-optimization"


def main():
    label = sys.argv[1]
    assert label in {"after", "intermediate"}
    groups = defaultdict(lambda: {"files": 0, "bytes": 0})
    links = []
    count = total = 0
    for base, dirs, names in os.walk(ROOT, followlinks=False):
        for name in list(dirs):
            path = Path(base) / name
            if path.is_symlink() or path.is_junction():
                links.append(path.relative_to(ROOT).as_posix())
                dirs.remove(name)
        for name in names:
            path = Path(base) / name
            n = path.stat().st_size
            rel = path.relative_to(ROOT)
            total += n
            count += 1
            for depth in range(1, min(4, len(rel.parts)) + 1):
                group = groups["/".join(rel.parts[:depth])]
                group["files"] += 1
                group["bytes"] += n
    result = {"measured_at": time.strftime("%Y-%m-%d %H:%M:%S"), "total_bytes": total, "files": count, "junctions_not_double_counted": links, "groups": dict(groups)}
    (OUT / ("inventory-" + label + ".json")).write_text(json.dumps(result, indent=2))
    before = json.loads((OUT / "inventory-before.json").read_text())
    print(json.dumps({"before_bytes": before["total_bytes"], "after_bytes": total, "reclaimed_bytes": before["total_bytes"] - total, "after_GB": total / 1e9}))


if __name__ == "__main__":
    main()
