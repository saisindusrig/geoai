"""Portable isolated runtime/reliability checks; no provider or cloud resources."""
import ctypes
import hashlib
import os
from pathlib import Path
import sys
import threading
import time
import pytest
from app.experimental import cad_worker
from app.experimental.cad_worker import compile_batch, WorkerFailure
from app.experimental.cad_artifacts import PrivateStore, local_orphans, publish
from test_cad_integration import geometry, seed, fake_result


def test_concurrency_admission_and_recovery(monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    monkeypatch.setattr(cad_worker,"_slots",threading.BoundedSemaphore(1))
    def blocked(*args,**kwargs):
        entered.set()
        release.wait(3)
        return [],{}
    monkeypatch.setattr(cad_worker,"_compile_batch",blocked)
    thread = threading.Thread(target=lambda:compile_batch(geometry()))
    thread.start()
    assert entered.wait(2)
    try:
        with pytest.raises(WorkerFailure,match="CONCURRENCY_LIMIT"):
            compile_batch(geometry())
    finally:
        release.set()
        thread.join(3)
    assert compile_batch(geometry()) == ([],{})


def alive(pid):
    if os.name == "nt":
        from ctypes import wintypes as w
        kernel = ctypes.WinDLL("kernel32")
        kernel.OpenProcess.argtypes = [w.DWORD,w.BOOL,w.DWORD]
        kernel.OpenProcess.restype = w.HANDLE
        kernel.GetExitCodeProcess.argtypes = [w.HANDLE,ctypes.POINTER(w.DWORD)]
        kernel.CloseHandle.argtypes = [w.HANDLE]
        handle = kernel.OpenProcess(0x1000,False,pid)
        if not handle:
            return False
        code = w.DWORD()
        kernel.GetExitCodeProcess(handle,ctypes.byref(code))
        kernel.CloseHandle(handle)
        return code.value == 259
    try:
        status = Path(f"/proc/{pid}/stat").read_text().split()[2]
        return status != "Z"
    except FileNotFoundError:
        return False


@pytest.mark.parametrize("ending", ["timeout","leader_exit","cancel"])
def test_process_tree_termination(tmp_path,monkeypatch,ending):
    marker = tmp_path/"child.pid"
    code = "import sys,subprocess,time; sys.stdin.buffer.read(); p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); open(sys.argv[1],'w').write(str(p.pid)); "
    code += "sys.exit(7)" if ending == "leader_exit" else "time.sleep(60)"
    monkeypatch.setattr(cad_worker,"_command",lambda root:[sys.executable,"-c",code,str(marker)])
    with pytest.raises(WorkerFailure):
        compile_batch(geometry(),timeout_s=2,cancelled=lambda:ending=="cancel" and marker.exists())
    assert marker.exists()
    pid = int(marker.read_text())
    deadline = time.monotonic()+3
    while alive(pid) and time.monotonic()<deadline:
        time.sleep(.02)
    assert not alive(pid)


def test_cpu_limit(monkeypatch):
    code = "import sys; sys.stdin.buffer.read()\nwhile True: pass"
    monkeypatch.setattr(cad_worker,"_command",lambda root:[sys.executable,"-c",code])
    with pytest.raises(WorkerFailure,match="WORKER_CRASH"):
        # Windows periodically checks CPU accounting, rather than exact wall time.
        compile_batch(geometry(),cpu_s=1,timeout_s=20)


def test_cancel_after_launch(monkeypatch):
    monkeypatch.setattr(cad_worker,"_command",lambda root:[sys.executable,"-c","import sys,time; sys.stdin.buffer.read(); time.sleep(10)"])
    start = time.monotonic()
    with pytest.raises(WorkerFailure,match="CANCELLED"):
        compile_batch(geometry(),cancelled=lambda:time.monotonic()-start>.2)


def test_incomplete_write_cleanup(tmp_path,monkeypatch):
    from app.core.config import settings
    from app.services import storage
    from app.experimental import cad_artifacts
    monkeypatch.setattr(settings,"LOCAL_STORAGE_DIR",str(tmp_path/"public"))
    monkeypatch.setattr(storage,"_s3_configured",lambda:False)
    monkeypatch.setattr(cad_artifacts.os,"fsync",lambda fd:(_ for _ in ()).throw(OSError("disk failure")))
    data = b"brep"
    store = PrivateStore()
    sha = hashlib.sha256(data).hexdigest()
    with pytest.raises(OSError):
        store.put(101,sha,data)
    assert not list(store._target(101,sha)[1].parent.iterdir())


def test_local_orphans_authorized_dry_run(db_session,tmp_path,monkeypatch):
    from app.core.config import settings
    from app.services import storage
    from fastapi import HTTPException
    monkeypatch.setattr(settings,"LOCAL_STORAGE_DIR",str(tmp_path/"public"))
    monkeypatch.setattr(storage,"_s3_configured",lambda:False)
    seed(db_session)
    g = geometry()
    results,blobs = fake_result(g)
    store = PrivateStore()
    publish(db_session,user_id=1,geometry=g,results=results,blobs=blobs,trusted_source=g.source,enabled=True,store=store)
    db_session.commit()
    orphan = hashlib.sha256(b"abandoned").hexdigest()
    store.put(101,orphan,b"abandoned")
    assert local_orphans(db_session,user_id=1,project_id=101,store=store)["orphanHashes"] == [orphan]
    assert store.get(101,orphan) == b"abandoned"
    with pytest.raises(HTTPException):
        local_orphans(db_session,user_id=2,project_id=101,store=store)
