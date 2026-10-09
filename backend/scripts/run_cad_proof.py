"""Offline proof artifacts. Requires the opt-in OCP dependencies on PYTHONPATH."""
import argparse
import base64
import json
import math
from pathlib import Path
import struct
import shutil
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.experimental.bim_cad import build_candidate, regenerate
from app.experimental.cad_fixtures import support_frame, TRUSTED
from app.experimental import cad_geometry as cad


def gltf(outputs):
    """Portable per-component triangle meshes with IDs and inspection metadata."""
    binary = bytearray()
    views, accessors, meshes, nodes = [], [], [], []
    def accessor(values, format, component_type, type_, count, minimum=None, maximum=None):
        while len(binary) % 4:
            binary.append(0)
        offset = len(binary)
        binary.extend(struct.pack('<'+format*len(values), *values))
        views.append(dict(buffer=0,byteOffset=offset,byteLength=len(binary)-offset))
        item = dict(bufferView=len(views)-1,componentType=component_type,count=count,type=type_)
        if minimum is not None:
            item.update(min=minimum,max=maximum)
        accessors.append(item)
        return len(accessors)-1
    for id, output in outputs.items():
        source = output['mesh']
        # Flat face normals; exact CAD remains separate from this derived cache.
        positions, normals = [], []
        for a,b,c in source['triangles']:
            p,q,r = [source['positions'][i] for i in [a,b,c]]
            u,v = [[q[i]-p[i] for i in range(3)],[r[i]-p[i] for i in range(3)]]
            normal = [u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            length = math.sqrt(sum(n*n for n in normal))
            if length <= 1e-14:
                raise ValueError('DEGENERATE_MESH_TRIANGLE')
            normal = [n/length for n in normal]
            # Local ENU (z up) to glTF (y up), right-handed rotation.
            for point in [p,q,r]:
                positions.extend([point[0],point[2],-point[1]])
                normals.extend([normal[0],normal[2],-normal[1]])
        vertices = [positions[i:i+3] for i in range(0,len(positions),3)]
        pos = accessor(positions,'f',5126,'VEC3',len(vertices),[min(p[i] for p in vertices) for i in range(3)],[max(p[i] for p in vertices) for i in range(3)])
        norm = accessor(normals,'f',5126,'VEC3',len(vertices))
        meshes.append(dict(name=id,primitives=[dict(attributes=dict(POSITION=pos,NORMAL=norm),material=0 if output.get('materialId')=='concrete' else 1,mode=4)]))
        nodes.append(dict(name=id,mesh=len(meshes)-1,extras={k:output[k] for k in ['id','assetId','assemblyId','materialId','definitionHash','provenance','engineeringStatus'] if k in output}))
    return dict(asset=dict(version='2.0',generator='GeoAI isolated OCCT proof'),scene=0,
        scenes=[dict(nodes=list(range(len(nodes))))],nodes=nodes,meshes=meshes,
        materials=[dict(name='Concept concrete',pbrMetallicRoughness=dict(baseColorFactor=[.65,.68,.70,1],metallicFactor=0,roughnessFactor=.8)),
                   dict(name='Concept steel',pbrMetallicRoughness=dict(baseColorFactor=[.35,.48,.6,1],metallicFactor=.5,roughnessFactor=.5))],
        buffers=[dict(uri='data:application/octet-stream;base64,'+base64.b64encode(binary).decode(),byteLength=len(binary))],bufferViews=views,accessors=accessors,
        extras=dict(sourceFrame='LOCAL_ENU',sourceUnits='m',axisConversion='x,y,z -> x,z,-y',authority='BIM plus cad-proof/1 mapping; mesh is derived'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('.cad-proof-output'))
    args = parser.parse_args()
    start = time.perf_counter()
    bridge = build_candidate(*support_frame('BRIDGE'),trusted=TRUSTED)
    industry = build_candidate(*support_frame('INDUSTRIAL_PLATFORM'),trusted=TRUSTED)
    assert bridge.outputs == industry.outputs
    regenerated, dirty = regenerate(bridge,{('primary-0','length'):6},trusted=TRUSTED)
    examples = {
        'concrete-beam':cad.extrude(cad.rectangle(.3,.5),5),
        'steel-I-beam':cad.extrude(cad.i_profile(.3,.5,.02,.03),5),
        'circular-column':cad.circular_column(.2,3),
        'slab-opening':cad.box_with_opening(5,3,.2,hole_width=.8,hole_depth=.6),
        'plate-hole':cad.box_with_opening(.4,.4,.02,hole_radius=.04),
        'tapered-member':cad.tapered_rectangle(.4,.4,.2,.2,5)}
    concrete = {'concrete-beam','circular-column','slab-opening','tapered-member'}
    solids = {id:dict(id=id,materialId='concrete' if id in concrete else 'steel',metrics=cad.solid_metrics(shape),mesh=cad.tessellate(shape)) for id,shape in examples.items()}
    result = dict(schemaVersion='cad-proof-results/1',kernel='OCCT/OCP 8.0.1.1.0',units='m',engineeringStatus='UNVERIFIED',
        elapsedSeconds=time.perf_counter()-start,solids=solids,crossAssetIdentical=True,affectedComponentIds=dirty,
        before=dict(model=bridge.model.model_dump(mode='json',by_alias=True),mapping=bridge.mapping.model_dump(mode='json',by_alias=True),outputs=bridge.outputs),
        after=dict(model=regenerated.model.model_dump(mode='json',by_alias=True),outputs=regenerated.outputs,epoch=regenerated.epoch))
    args.output.mkdir(parents=True,exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    vendor = args.output/'vendor'
    vendor.mkdir(exist_ok=True)
    for source, name in [(root/'frontend/node_modules/three/build/three.module.js','three.module.js'),
                         (root/'frontend/node_modules/three/build/three.core.js','three.core.js'),
                         (root/'frontend/node_modules/three/examples/jsm/controls/OrbitControls.js','OrbitControls.js'),
                         (root/'frontend/node_modules/three/LICENSE','THREE-LICENSE.txt')]:
        shutil.copyfile(source,vendor/name)
    shutil.copyfile(root/'backend/app/experimental/cad_review.html',args.output/'review.html')
    from OCP.BRepTools import BRepTools
    for id, shape in examples.items():
        if not BRepTools.Write_s(shape,str(args.output/f'{id}.brep')):
            raise ValueError('BREP_EXPORT_FAILED')
    (args.output/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    for name, outputs in [('support-frame-5m',bridge.outputs),('support-frame-6m',regenerated.outputs)]:
        (args.output/f'{name}.gltf').write_text(json.dumps(gltf(outputs)),encoding='utf-8')
    summary = dict(elapsedSeconds=result['elapsedSeconds'],componentCount=len(bridge.outputs),affectedComponentIds=dirty,
                   vertices=sum(len(o['mesh']['positions']) for o in bridge.outputs.values()),triangles=sum(len(o['mesh']['triangles']) for o in bridge.outputs.values()),
                   solidMetrics={id:o['metrics'] for id,o in solids.items()})
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
