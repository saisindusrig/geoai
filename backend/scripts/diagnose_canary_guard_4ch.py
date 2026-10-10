"""Reproduce historical guard on a database copy; never invoke a transport."""
import ast
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FAILED = ROOT / ".cad-proof-output" / "4c-understand-canary-981cd96192534cfebc42a739366700b5"
OUT = ROOT / ".cad-proof-output" / "4ch-diagnosis"


def diagnose():
    OUT.mkdir(exist_ok=True)
    protected = {str(p.relative_to(FAILED)): hashlib.sha256(p.read_bytes()).hexdigest() for p in FAILED.rglob("*") if p.is_file()}
    (OUT / "protected-before.json").write_text(json.dumps(protected, indent=2))
    shutil.copyfile(FAILED / "acceptance.db", OUT / "read-copy.db")
    os.environ["DATABASE_URL"] = "sqlite:///" + (OUT / "read-copy.db").as_posix()
    os.environ["GEOAI_EXPERIMENTAL_CAD"] = "true"
    os.environ["GEOAI_CAD_TEST_USER_IDS"] = "490001"
    os.environ["GEOAI_CAD_TEST_PROJECT_IDS"] = "490001"
    from app.core.config import settings
    settings.LOCAL_STORAGE_DIR = str(FAILED / "public")
    from app.services import storage
    storage._s3_configured = lambda: False
    from app.services.ai import nebius
    async def blocked(*args, **kwargs):
        raise RuntimeError("LIVE_TRANSPORT_FORBIDDEN")
    nebius._request = blocked
    from app.db.session import SessionLocal
    from app.db.models import GeneratedFile
    from app.experimental.bim_orchestration import frozen
    from app.experimental.bim_authoring import stage_packet, stage_context
    from app.experimental.cad_contract import digest
    prepared = json.loads((FAILED / "understand-request.json").read_text())
    manifest = json.loads((FAILED / "prepared.json").read_text())
    with SessionLocal() as db:
        _, snapshot, _ = frozen(db, 490001, 490001, manifest["messageId"])
        assert digest(snapshot) == manifest["frozenContextHash"]
        packet = stage_packet("UNDERSTAND", request_text=snapshot["userRequest"])
        packet["trustedContext"] = stage_context("UNDERSTAND", snapshot, digest(snapshot))
        system = packet.pop("instruction")
        metadata=db.get(GeneratedFile,manifest["runId"]).metadata_json
        recorded_state={k:metadata.get(k) for k in ("status","calls","errorCode","attempts")}
    source_path = ROOT / "scripts" / "run_understand_canary.py"
    archived = OUT / "historical-runner.py.txt"
    source = archived.read_text() if archived.exists() else source_path.read_text()
    if not archived.exists():archived.write_text(source)
    tree = ast.parse(source, filename=str(source_path))
    guard = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == "guarded")
    prefix = []
    for node in guard.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "update":
            break
        prefix.append(node)
    guard.body = prefix
    module = ast.Module(body=[guard], type_ignores=[])
    namespace = dict(json=json, ledger={"requestCount":0}, MODEL="Qwen/Qwen3.5-397B-A17B",
        expected=dict(system=prepared["system"], payload=prepared["payload"]))
    exec(compile(module, str(source_path), "exec"), namespace)
    actual_messages = [dict(role="system", content=system), dict(role="user", content=json.dumps(packet, separators=(",", ":"), default=str))]
    expected_messages = [dict(role="system", content=prepared["system"]), dict(role="user", content=json.dumps(prepared["payload"], separators=(",", ":"), default=str))]
    result = dict(paidRequests=0, outboundInvocations=0, frozenHashVerified=True,
        recordedRunState=recorded_state,
        canonicalPacketHashMatches=digest(dict(system=system, payload=packet)) == prepared["packetHash"],
        parsedPayloadEqual=packet == prepared["payload"], systemEqual=system == prepared["system"],
        serializedMessagesEqual=actual_messages == expected_messages,
        actualMessageBytes=sum(len(m["content"].encode()) for m in actual_messages),
        expectedMessageBytes=sum(len(m["content"].encode()) for m in expected_messages))
    try:
        asyncio.run(namespace["guarded"]("POST", "chat/completions", model="Qwen/Qwen3.5-397B-A17B", timeout=45,
            payload=dict(model="Qwen/Qwen3.5-397B-A17B", max_tokens=3500, messages=actual_messages)))
        result["reproduced"] = False
    except AssertionError as exc:
        frames = traceback.extract_tb(exc.__traceback__)
        location = frames[-1]
        result.update(reproduced=True, exception="AssertionError", file=location.filename,
            line=location.lineno, assertion=source.splitlines()[location.lineno-1].strip(),
            stack=[dict(file=f.filename, line=f.lineno, function=f.name) for f in frames])
    # Demonstrate ordering difference without exposing project fields/values.
    def first_order_difference(a, b, path=()):
        if isinstance(a, dict) and isinstance(b, dict):
            if list(a) != list(b):
                safe_keys={"trustedContext","siteSummary","dimensions","relief","terrainSummary","outputSchema","properties","$defs"}
                return dict(depth=len(path), schemaPath=[k if k in safe_keys else "<field>" for k in path],
                    sameKeySet=set(a) == set(b), sameValues=a == b)
            for key in a:
                found = first_order_difference(a[key], b[key], (*path,key))
                if found:return found
        if isinstance(a, list) and isinstance(b, list):
            for x,y in zip(a,b):
                found=first_order_difference(x,y,path)
                if found:return found
    result["firstDictionaryOrderDifference"] = first_order_difference(packet, prepared["payload"])
    after = {str(p.relative_to(FAILED)): hashlib.sha256(p.read_bytes()).hexdigest() for p in FAILED.rglob("*") if p.is_file()}
    assert protected == after
    result["protectedFailedRunUnchanged"] = True
    (OUT / "reproduction.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":diagnose()
