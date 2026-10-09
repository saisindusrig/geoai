# Experimental CAD runtime notices

These license texts are included in the Docker runtime. Their presence does not
certify redistribution compliance or replace corresponding-source obligations.

- OCP-Apache-2.0.txt: copied from installed cadquery-ocp 8.0.1.1.0.
- VTK-Copyright.txt: copied from installed VTK 9.6.2 wheel.
- OCCT-LGPL-2.1.txt and OCCT-Exception.txt: upstream OCCT V8_0_1 texts.
  Sources: https://github.com/Open-Cascade-SAS/OCCT/tree/V8_0_1
- Proxy 8.0.1.1.0 metadata declares Apache-2.0. Its package-specific copyright
  attribution/source provenance remains to be packaged and reviewed.
  https://pypi.org/project/cadquery-ocp-proxy/8.0.1.1.0/

Release review must reconcile every native library in the generated inventory
against its exact corresponding source and build provenance. Include OCCT source,
modifications/build instructions and replacement/relinking rights where required.
The header exception does not waive library license conditions.

Review bundled FreeImage (FreeImage Public License/GPL options), its image codecs,
VTK third-party libraries, NumPy math libraries, Shapely/GEOS and pyproj/PROJ plus
their bundled dependencies. Inventory metadata labels are not a substitute for
their full notices. Upstream FreeImage license:
https://freeimage.sourceforge.io/license.html

The Windows isolated evaluation lacks VTK's declared matplotlib dependency. Linux
CI installs the full dependency closure and captures pip freeze, package/native
hashes, dpkg versions, linkage and notices. Audit that evidence before producing
a redistribution bundle. Missing or unknown items remain blockers for release.
