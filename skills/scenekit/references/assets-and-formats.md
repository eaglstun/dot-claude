# Assets and formats

## SceneKit cannot load glTF or GLB

There is no built-in glTF importer, no plugin, and no ModelIO path. This matters
more than it used to: **GLB is the output format of essentially every AI 3D
generation service** (Tripo, Meshy, etc.) and most modern web/3D tooling.

Formats SceneKit *does* read: `.scn`, `.usdz` / `.usd`, `.dae` (Collada), `.obj`,
`.abc`. Load with `SCNScene(url:options:)`.

**USDZ is the right target** — single file, carries PBR materials and textures,
native support, and Xcode previews it.

## Converting GLB → USDZ with Blender (headless)

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background --python convert.py
```

```python
bpy.ops.import_scene.gltf(filepath=src)
# ... decimate / transform ...
bpy.ops.wm.usd_export(filepath=dst, export_textures=True, export_materials=True)
```

### Trap 1: Blender's USD export writes Z-up

Blender is Z-up; USD and SceneKit are Y-up, and the exporter does **not** convert.
Models arrive lying on their back. Bake the rotation in before export so the
asset is correct for anything that loads it:

```python
obj.data.transform(mathutils.Matrix.Rotation(math.radians(-90), 4, "X"))
obj.data.update()
```

### Trap 2: `bpy.ops.object.transform_apply` silently does nothing

It operates on the *selected* objects. If selection isn't what you assumed it
reports success and changes nothing — a rotation that appears to apply but
doesn't. **Transform the mesh data directly** (as above) instead of setting
`rotation_euler` and calling the operator.

### Trap 3: decimation tears generated meshes

Generated meshes ship with many split vertices. Collapse decimation treats those
as separate surfaces and rips along the seams rather than simplifying across
them, producing visible holes. **Weld first:**

```python
bpy.ops.mesh.remove_doubles(threshold=1e-4)
bpy.ops.mesh.normals_make_consistent(inside=False)
```

With welding, ratios that previously tore become usable — so if a target
triangle count was rejected before welding was added, retest it.

## Bake scale and origin into the asset

Export with the model's base at y = 0, centred, at its intended world size.
Placing it is then a translation and nothing else, and there are no magic scale
factors scattered through the render code.

## Bundling

`.usdz` files in the app bundle load with:

```swift
Bundle.main.url(forResource: "name", withExtension: "usdz")
```

With xcodegen, files under a target's `sources` path are picked up as resources
automatically — but **regenerate the project after adding one**, or the build
fails with an unhelpful "cannot find in scope" for unrelated code.

Instantiate once and `clone()` per placement: clones share the underlying
geometry, so N copies cost N draw calls but one geometry upload.

Guard a missing asset rather than force-unwrapping. Absent decoration should not
take the app down.

## Verifying an imported asset

Load it offscreen and check before wiring it into a scene:

```swift
let scene = try SCNScene(url: url)
var tris = 0
scene.rootNode.enumerateHierarchy { node, _ in
    node.geometry?.elements.forEach { tris += $0.primitiveCount }
}
let (lo, hi) = scene.rootNode.boundingBox   // catches wrong up-axis instantly
```

If the bounding box's tall axis is Z rather than Y, the up-axis conversion did
not happen.

## Rendering offscreen

`SCNRenderer(device:options:)` with `.snapshot(atTime:with:antialiasingMode:)`
renders without a view — ideal for A/B-ing render settings, verifying an asset,
or reproducing a bug in isolation. Works on macOS from a plain `swift file.swift`
script, which makes it a fast way to test SceneKit behaviour without an app.
