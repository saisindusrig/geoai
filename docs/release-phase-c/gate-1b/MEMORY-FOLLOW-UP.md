# Separate focused GPU memory follow-up — prepared, not started

Memory qualification remains open. Carry forward the hardware-verification findings: loaded heap approximately 112–121 MB; disposed heap approximately 31–38 MB; residual DOM/listener growth across repeated navigation. No confirmed unbounded Cesium retained-object leak. Entity/EntityCollection disposal reached zero in diagnostic samples, and selected destroyed-scene/detached-canvas targets disappeared after debugger groups were released and full collection occurred. Object enumeration materially affected early apparent growth. Native GPU memory/VRAM was not measured.

A future focused investigation should:

1. Use the qualified pinned Node24/default build, isolated synthetic API/files and a fixed viewport/quality. Keep Firebase/Nebius disabled. No original model or accounting mutations.
2. Begin with an uninstrumented control: no renderer wrappers, heap-object enumeration or strong scene references. Warm the same two synthetic projects and dashboard, then perform a recorded, bounded navigation soak (proposed 15 cycles, maximum 10 minutes). Record natural and controlled-collection heap separately, plus DOM nodes, listeners and active canvases. Dashboard has five intentionally live marketing preview canvases; a disposed editor should have no live Cesium canvas.
3. If a repeatable post-warm-up trend remains, trace multiple retained objects/classes and exact roots after releasing every debugger handle. Separate router/UI/gallery retention, delayed native disposal and Cesium resources/pick anchors. Never infer the whole trend from one collected target or one heap snapshot. Do not persist full heap dumps/device IDs; retain sanitized causal evidence.
4. Make a product change only after a specific missing cleanup/reference is reproduced and its owner is established. Add a meaningful lifecycle regression, rerun the same clean measurements and check selection/camera, conceptual preview, explicit Apply/Save, undo/redo and result identity. No speculative renderer rewrite, framework upgrade or cache purge.
5. Report whether warmed retention converges, remains bounded by a demonstrated cache lifecycle, or continues growing. Keep memory sign-off withheld if the cause or bounds remain unknown; a lower single snapshot is not a fix.

This document schedules nothing, starts no agent/chat, changes no memory behavior and authorizes no cloud, installation or deployment. Gate1B does not resolve this work.
