# OpenSees integration preflight

Date: 11 October 2026. Initial preflight status: **NO LOCAL SOLVER FOUND**. Resolved status: **AUTHORIZED WORKSPACE-LOCAL INSTALLATION / REAL SOLVER VERIFIED**.

No OpenSees, OpenSeesSP or OpenSeesMP executable was found on PATH. A recursive name search found no OpenSees files in the workspace, user Downloads, Desktop, Documents, Program Files, Program Files (x86), or existing C:\OpenSees / D:\OpenSees folders. No OpenSees/solver environment configuration was present. OpenSeesPy is absent from both backend/.venv and backend/.venv-civicspan. This is a search of the listed locations, not proof that no executable exists elsewhere on the computer. An executable supplied at another location still requires a version/capability smoke test.

The official Berkeley distribution page lists a Windows 64-bit OpenSees 3.8.0 executable package:
https://opensees.berkeley.edu/OpenSees/user/download.php

During the initial preflight, nothing was downloaded or installed and no solver was run. The user subsequently explicitly selected **Allow workspace-local OpenSees installation**. The official package was extracted into `.cache/opensees`, without a machine-wide installer or PATH change. The included Visual C++ installer was not run because the executable already worked with the existing runtime.

Runtime smoke test reported **OpenSees 3.8.0 64-bit**, build `6e55293513192aa05c7e1205e66a5a1a1ed088c4`. Package SHA-256: `5e37a5a95c645e31c7700ce6ec5b08c178baedc83241f7cbe10ef10cf6a4fb41`. Executable SHA-256: `5aa4e9c80c410c510ca62ac3b2f1d64a8e50679f0238e140b5bebcd6d5ddbe6d`.

The completed integration remains bounded to the previously defined elastic axial column and prescribed vertical spring. Solver and browser tests have now been executed; see `OPENSEES_MILESTONE_REPORT.md` and the saved numerical/browser/failure evidence. Design checks and engineering approval remain disabled.
