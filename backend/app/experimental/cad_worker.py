"""Bounded opt-in subprocess supervisor. Not an OS security sandbox or API route."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import threading
import shutil
from contextlib import contextmanager
from app.experimental.cad_contract import Geometry, Result, digest, encode


class WorkerFailure(RuntimeError):
    pass


_slots = threading.BoundedSemaphore(2)


@contextmanager
def _scratch_directory():
    base = Path(tempfile.gettempdir()).resolve()
    root = Path(tempfile.mkdtemp(prefix="geoai-cad-")).resolve()
    try:
        yield str(root)
    finally:
        # Only this server-created immediate child may be recursively removed.
        if root.parent != base or not root.name.startswith("geoai-cad-"):
            raise WorkerFailure("INVALID_SCRATCH_ROOT")
        deadline = time.monotonic()+3
        while True:
            try:
                shutil.rmtree(root)
                break
            except FileNotFoundError:
                break
            except PermissionError as exc:
                # Windows can report zero active job processes just before
                # inherited file handles finish closing in the kernel.
                if time.monotonic() >= deadline:
                    raise WorkerFailure("SCRATCH_CLEANUP_FAILED") from exc
                time.sleep(.02)


def _windows_job(process, memory_mb, cpu_s):
    from ctypes import wintypes as w
    class Basic(ctypes.Structure):
        _fields_ = [("ProcessTime", ctypes.c_int64), ("JobTime", ctypes.c_int64), ("Flags", w.DWORD),
                    ("MinWorking", ctypes.c_size_t), ("MaxWorking", ctypes.c_size_t), ("Active", w.DWORD),
                    ("Affinity", ctypes.c_size_t), ("Priority", w.DWORD), ("Scheduling", w.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_uint64) for name in ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes", "OtherBytes")]
    class Extended(ctypes.Structure):
        _fields_ = [("Basic", Basic), ("IO", IO), ("ProcessMemory", ctypes.c_size_t), ("JobMemory", ctypes.c_size_t),
                    ("PeakProcess", ctypes.c_size_t), ("PeakJob", ctypes.c_size_t)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.restype = w.HANDLE
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
    kernel.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    kernel.TerminateJobObject.argtypes = [w.HANDLE,w.UINT]
    kernel.QueryInformationJobObject.argtypes = [w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.c_void_p]
    job = kernel.CreateJobObjectW(None, None)
    limits = Extended()
    limits.Basic.Flags = 0x100 | 0x2000 | 0x2  # memory, kill-on-close, process CPU time
    limits.Basic.ProcessTime = cpu_s * 10_000_000
    limits.ProcessMemory = memory_mb * 1024 * 1024
    if not job or not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)) or not kernel.AssignProcessToJobObject(job, int(process._handle)):
        if job:
            kernel.CloseHandle(job)
        raise WorkerFailure("MEMORY_ISOLATION_UNAVAILABLE")
    action = w.DWORD(0)  # JOB_OBJECT_TERMINATE_AT_END_OF_JOB
    if not kernel.SetInformationJobObject(job, 6, ctypes.byref(action), ctypes.sizeof(action)):
        kernel.CloseHandle(job)
        raise WorkerFailure("CPU_ISOLATION_UNAVAILABLE")
    class Accounting(ctypes.Structure):
        _fields_ = [(name,ctypes.c_int64) for name in ("UserTime","KernelTime","PeriodUser","PeriodKernel")] + [(name,w.DWORD) for name in ("Faults","Processes","Active","Terminated")]
    def stop():
        # Job close kills asynchronously. Wait for descendant teardown before
        # removing scratch files inherited through stdout/stderr handles.
        kernel.TerminateJobObject(job,1)
        deadline = time.monotonic()+3
        accounting = Accounting()
        while time.monotonic()<deadline:
            if kernel.QueryInformationJobObject(job,1,ctypes.byref(accounting),ctypes.sizeof(accounting),None) and accounting.Active == 0:
                break
            time.sleep(.01)
        kernel.CloseHandle(job)
    return stop


def _command(root):
    return [sys.executable, "-m", "app.experimental.cad_worker_entry", str(root)]


def compile_batch(geometry, *, timeout_s=30, memory_mb=1024, cpu_s=20, cancelled=lambda: False):
    if not _slots.acquire(blocking=False):
        raise WorkerFailure("CONCURRENCY_LIMIT")
    try:
        return _compile_batch(geometry, timeout_s=timeout_s, memory_mb=memory_mb, cpu_s=cpu_s, cancelled=cancelled)
    finally:
        _slots.release()


def _compile_batch(geometry, *, timeout_s, memory_mb, cpu_s, cancelled):
    request = Geometry.model_validate(geometry)
    if not .05 <= timeout_s <= 120 or not 64 <= memory_mb <= 2048 or type(cpu_s) is not int or not 1 <= cpu_s <= 60:
        raise ValueError("WORKER_LIMIT_RANGE")
    payload = encode(request)
    if len(payload) > 2_000_000:
        raise WorkerFailure("INPUT_LIMIT")
    with _scratch_directory() as directory:
        root = Path(directory)
        # Native worker logs go to bounded-on-read private scratch, never API output.
        with (root / "stdout").open("wb") as output, (root / "stderr").open("wb") as errors:
            kwargs = {"start_new_session": True} if os.name != "nt" else {}
            allowed = {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PYTHONPATH", "PYTHONIOENCODING", "LANG", "LC_ALL"}
            env = {k:v for k,v in os.environ.items() if k.upper() in allowed}
            env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONNOUSERSITE="1")
            command = _command(root)
            if os.name != "nt":
                command = [sys.executable, "-m", "app.experimental.cad_worker_bootstrap", str(memory_mb), str(cpu_s), *command]
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=output, stderr=errors, env=env, **kwargs)
            close_job = None
            try:
                if os.name == "nt":
                    close_job = _windows_job(process, memory_mb, cpu_s)
                if cancelled():
                    raise WorkerFailure("CANCELLED")
                process.stdin.write(payload)
                process.stdin.close()
                deadline = time.monotonic() + timeout_s
                while process.poll() is None:
                    if cancelled():
                        raise WorkerFailure("CANCELLED")
                    if time.monotonic() >= deadline:
                        raise WorkerFailure("TIMEOUT")
                    if any(p.stat().st_size > 32_000_000 for p in root.iterdir() if p.is_file()):
                        raise WorkerFailure("OUTPUT_LIMIT")
                    time.sleep(.02)
                if process.returncode != 0:
                    raise WorkerFailure("WORKER_CRASH")
                if cancelled():
                    raise WorkerFailure("CANCELLED")
            except (BrokenPipeError, OSError) as exc:
                raise WorkerFailure("WORKER_IO_FAILURE") from exc
            finally:
                if process.stdin and not process.stdin.closed:
                    process.stdin.close()
                if close_job:
                    close_job()
                elif os.name != "nt":
                    # Kill the group even when the leader crashed or exited first.
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if process.poll() is None:
                    process.kill()
                process.wait()
        if (root / "stdout").stat().st_size > 2_000_000:
            raise WorkerFailure("MANIFEST_LIMIT")
        try:
            results = [Result.model_validate(r) for r in json.loads((root / "stdout").read_bytes())]
            expected = {d.component_id: digest(d) for d in request.definitions}
            if len(results) != len(expected) or {r.component_id: r.definition_hash for r in results} != expected:
                raise ValueError("RESULT_BINDING_MISMATCH")
            blobs = {}
            for r in results:
                for a in (r.brep, r.mesh):
                    path = root / a.sha256
                    if path.stat().st_size != a.byte_length:
                        raise ValueError("ARTIFACT_SIZE_MISMATCH")
                    data = path.read_bytes()
                    if hashlib.sha256(data).hexdigest() != a.sha256:
                        raise ValueError("ARTIFACT_HASH_MISMATCH")
                    blobs[a.sha256] = data
                    if a.kind == "MESH":
                        mesh = json.loads(data)
                        positions, triangles = mesh["positions"], mesh["triangles"]
                        if mesh["units"] != "m" or not positions or not triangles or len(positions) > 250000 or len(triangles) > 500000:
                            raise ValueError("INVALID_MESH")
                        import math
                        if any(len(p) != 3 or any(not math.isfinite(v) for v in p) for p in positions) or any(len(t) != 3 or any(type(i) is not int or not 0 <= i < len(positions) for i in t) for t in triangles):
                            raise ValueError("INVALID_MESH")
            if sum(len(b) for b in blobs.values()) > 32_000_000:
                raise ValueError("BATCH_BYTE_LIMIT")
        except (ValueError, KeyError, OSError, TypeError) as exc:
            raise WorkerFailure("INVALID_WORKER_OUTPUT") from exc
        return results, blobs
