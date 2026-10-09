"""Emit installed CAD package/native/license inventory; never load native code."""
import hashlib
from importlib.metadata import distribution, PackageNotFoundError
from packaging.requirements import Requirement
import json
from pathlib import Path
import platform
import sys
import argparse
import subprocess


def inventory():
    packages = []
    pending = ["cadquery-ocp", "cadquery-ocp-proxy", "vtk", "pydantic", "shapely", "pyproj"]
    seen, missing = set(), []
    while pending:
        name = pending.pop(0).lower().replace("_", "-")
        if name in seen:
            continue
        seen.add(name)
        try:
            dist = distribution(name)
        except PackageNotFoundError:
            missing.append(name)
            continue
        for raw in dist.requires or []:
            requirement = Requirement(raw)
            if requirement.marker is None or requirement.marker.evaluate({"extra":""}):
                pending.append(requirement.name)
        files = []
        for item in dist.files or []:
            if str(item).lower().endswith((".dll", ".pyd", ".so")) or ".so." in str(item).lower() or any(token in str(item).lower() for token in ("license", "copyright", "notice")):
                path = Path(dist.locate_file(item))
                if path.is_file():
                    files.append({"path":str(item), "sha256":hashlib.sha256(path.read_bytes()).hexdigest(), "bytes":path.stat().st_size})
        packages.append({"name":name, "version":dist.version, "requires":dist.requires or [],
            "licenseExpression":dist.metadata.get("License-Expression"), "license":dist.metadata.get("License"),
            "licenseClassifiers":[c for c in dist.metadata.get_all("Classifier",[]) if c.startswith("License")],
            "projectUrls":dist.metadata.get_all("Project-URL",[]), "nativeAndNoticeFiles":files})
    return {"schemaVersion":"cad-runtime-inventory/1", "platform":platform.platform(), "python":platform.python_version(),
            "libc":platform.libc_ver(), "packages":packages, "missingDependencies":missing, "redistributionAccepted":False,
            "pending":["OCCT LGPL/exception and corresponding-source bundle", "bundled FreeImage/codec and VTK transitive notice review", "Linux build and image digest"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-linkage",action="store_true")
    args = parser.parse_args()
    result = inventory()
    if args.check_linkage:
        if platform.system() != "Linux":
            raise RuntimeError("LINUX_LINKAGE_CHECK_ONLY")
        linkage = []
        for package in result["packages"]:
            dist = distribution(package["name"])
            for item in package["nativeAndNoticeFiles"]:
                name = item["path"]
                if not (name.endswith(".so") or ".so." in name):
                    continue
                check = subprocess.run(["ldd",str(dist.locate_file(name))],capture_output=True,text=True,timeout=10)
                linkage.append({"package":package["name"],"path":name,"returnCode":check.returncode,"output":check.stdout+check.stderr})
        result["linkage"] = linkage
        print(json.dumps(result,indent=2))
        if not linkage or any("not found" in item["output"] or item["returnCode"] != 0 for item in linkage):
            raise SystemExit("NATIVE_LINKAGE_FAILED")
    else:
        print(json.dumps(result,indent=2))
