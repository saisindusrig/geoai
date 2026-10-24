"""Read-only local inventory and row-level preservation verification. Never reads secrets."""
from pathlib import Path
import ast
import hashlib
import json
import os
import sqlite3
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "project-cleanup"


def database_fingerprint(path):
    result = {}
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
        for (table,) in connection.execute("select name from sqlite_master where type='table' order by name"):
            rows = connection.execute('select * from "' + table.replace('"', '""') + '"').fetchall()
            hashes = sorted(hashlib.sha256(repr(row).encode()).hexdigest() for row in rows)
            result[table] = {"rows": len(rows), "sha256": hashlib.sha256("".join(hashes).encode()).hexdigest()}
    return result


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    inventory = defaultdict(lambda: {"files": 0, "bytes": 0})
    duplicates = defaultdict(list)
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in {".git", ".cleanup-backups"}]
        for name in names:
            path = Path(base) / name
            rel = path.relative_to(ROOT)
            group = "/".join(rel.parts[:2]) if len(rel.parts) > 1 else rel.as_posix()
            inventory[group]["files"] += 1
            inventory[group]["bytes"] += path.stat().st_size
            if rel.parts[:2] == ("backend", "app") and path.suffix == ".py":
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and len(node.body) >= 3:
                            signature = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
                            duplicates[hashlib.sha256(signature.encode()).hexdigest()].append({"path": rel.as_posix(), "line": node.lineno, "function": node.name})
                except (SyntaxError, UnicodeError):
                    pass
    for group, item in inventory.items():
        lower = group.lower()
        if any(x in lower for x in ("node_modules", ".venv", ".cad-proof-deps")):
            purpose = "Installed dependencies; retained; removal requires environment verification"
        elif any(x in lower for x in ("storage", "docs", ".test", ".cache", "live-results", "cad-proof-output")):
            purpose = "Data, fixtures or engineering evidence; retained; manual review required"
        elif ".next" in lower or "__pycache__" in lower or ".pytest_cache" in lower:
            purpose = "Generated cache; retain active builds; only verified bytecode eligible"
        else:
            purpose = "Source/configuration/assets; retained unless independently proven redundant"
        item["purpose"] = purpose
        item["safe_to_remove"] = False
    (OUTPUT / "inventory.json").write_text(json.dumps(dict(sorted(inventory.items())), indent=2))
    (OUTPUT / "duplicate-function-candidates.json").write_text(json.dumps([v for v in duplicates.values() if len(v) > 1], indent=2))
    backup = Path((ROOT / ".cleanup-backup-path").read_text())
    baseline = json.loads((backup / "database-baseline.json").read_text())
    verification = []
    for record in baseline:
        actual = database_fingerprint(ROOT / record["path"])
        schema_query = "select type,name,tbl_name,sql from sqlite_master order by type,name"
        with sqlite3.connect((ROOT / record["path"]).as_uri() + "?mode=ro", uri=True) as current, sqlite3.connect((backup / "databases" / record["path"]).as_uri() + "?mode=ro", uri=True) as saved:
            schema_unchanged = current.execute(schema_query).fetchall() == saved.execute(schema_query).fetchall()
        verification.append({"path": record["path"], "unchanged": actual == record["tables"] and schema_unchanged, "schema_unchanged": schema_unchanged, "tables": len(actual), "rows": sum(v["rows"] for v in actual.values())})
    (OUTPUT / "database-preservation.json").write_text(json.dumps(verification, indent=2))
    print(json.dumps({"groups": len(inventory), "files": sum(x["files"] for x in inventory.values()), "bytes": sum(x["bytes"] for x in inventory.values()), "databases": len(verification), "unchanged": sum(v["unchanged"] for v in verification)}))


if __name__ == "__main__":
    main()
