---
semantic_id: "wO5ibXM3vZ3E7ZukiCPf8l17AiOK0AAL"
related_ids:
  - "sOdjSW41uZ3G7ZqgsCHn4tV8GiZL0AAP"
  - "6O1LSWY3F52W4Zgiu6uP8kB7BidC4AAH"
---
# Shader Graph node catalog

Source (Apple JSON doc endpoints — the `ShaderGraph` framework reference, one page per
node category):

- <https://developer.apple.com/documentation/shadergraph>
- `…/shadergraph/{surface, realitykit, geometric, application, procedural, 2d-texture,`
  `3d-texture, 2d-procedural, 3d-procedural, math, adjustment, compositing, data, logic,`
  `material, organization}`

Fetched: 2026-08-19

Every entry links to its own page, which carries the exact input/output signature and type
overloads. This file is the index — reach for it when the question is *"which node does
X?"* rather than *"what are this node's ports?"*.

## How to read it

- Shader Graph implements **MaterialX 1.38**; most nodes here are standard MaterialX and
  behave the way they do in other MaterialX tools.
- Nodes suffixed **(RealityKit)** are Apple additions and have no MaterialX equivalent.
- Nodes named **`Geometry Modifier …`** connect *only* to the Geometry Modifier output pin
  (vertex-stage). Nodes named **`Surface …`** connect *only* to Custom Surface
  (fragment-stage). Everything else is generic.
- Most nodes are typed overloads of a shared operation — pick the version matching your
  data type, or let the context-sensitive node selector (drag off a connector into empty
  space) filter for you.

## The three you almost always start from

- **Preview Surface** — the MaterialX USD preview surface every new material opens with.
- **PBR Surface (RealityKit)** — the real RealityKit PBR surface node.
- **Geometry Modifier (RealityKit)** — the per-vertex entry point.

Two RealityKit nodes are worth knowing exist because nothing else provides them:
**Camera Index Switch (RealityKit)** renders a different result per eye in a stereoscopic
render, and **Hover State (RealityKit)** drives custom hover effects on visionOS.
**Blurred Background (RealityKit)** samples the blurred backdrop, and **Environment
Radiance (RealityKit)** returns real-environment diffuse/specular radiance from the IBL map.

---

## Surface

Generate a MaterialX preview surface.


### Overview

Every new material you create includes a preview surface that displays your material as you build it. Create additional surfaces to see alternate previews within the same graph.


### Nodes
- [Preview Surface](https://developer.apple.com/documentation/shadergraph/surface/preview-surface) — A MaterialX version of USD Preview Surface.

## RealityKit

Add RealityKit surfaces or textures to your material and access and manipulate scene geometry.


### Overview

Incorporate RealityKit-specific content into your graph and modify that content visually. You can use geometry modifiers to change the vertices of your models. You can also create and configure RealityKit surfaces and textures and use them in your graph.


### Nodes
- [Unlit Surface (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/unlit-surface-(realitykit)) — A surface shader that defines properties for a RealityKit Unlit material.
- [PBR Surface (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/pbr-surface-(realitykit)) — A surface shader that defines properties for a RealityKit Physically Based Rendering material.
- [Hair Surface (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/hair-surface-(realitykit)) — A surface shader that defines properties for a RealityKit Hair material.
- [Occlusion Surface (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/occlusion-surface-(realitykit)) — A surface shader that defines properties for a RealityKit Occlusion material that does not receive dynamic lighting.
- [Shadow Receiving Occlusion Surface (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/shadow-receiving-occlusion-surface-(realitykit)) — A surface shader that defines properties for a RealityKit Occlusion material that receives dynamic lighting.
- [View Direction (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/view-direction-(realitykit)) — A vector from a position in the scene to the view reference point.
- [Camera Position (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/camera-position-(realitykit)) — The position of the camera in the scene.
- [Geometry Modifier Model To World (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/geometry-modifier-model-to-world-(realitykit)) — The model-to-world transformation Matrix4x4 (Float).
- [Geometry Modifier World To Model (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/geometry-modifier-world-to-model-(realitykit)) — The world-to-model transformation Matrix4x4 (Float).
- [Geometry Modifier Normal To World (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/geometry-modifier-normal-to-world-(realitykit)) — The normal-to-world transformation Matrix3x3 (Float).
- [Geometry Modifier Model To View (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/geometry-modifier-model-to-view-(realitykit)) — The model-to-view transformation Matrix4x4 (Float).
- [Geometry Modifier View To Projection (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/geometry-modifier-view-to-projection-(realitykit)) — The view-to-projection transformation Matrix4x4 (Float).
- [Geometry Modifier Projection To View (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/geometry-modifier-projection-to-view-(realitykit)) — The projection-to-view transformation Matrix4x4 (Float).
- [Geometry Modifier Vertex ID (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/geometry-modifier-vertex-id-(realitykit)) — The integer index of the vertex.
- [Surface Model To World (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/surface-model-to-world-(realitykit)) — The model-to-world transformation Matrix4x4 (Float).
- [Surface Model To View (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/surface-model-to-view-(realitykit)) — The model-to-view transformation Matrix4x4 (Float).
- [Surface World To View (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/surface-world-to-view-(realitykit)) — The world-to-view transformation Matrix4x4 (Float).
- [Surface View To Projection (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/surface-view-to-projection-(realitykit)) — The view-to-projection transformation Matrix4x4 (Float).
- [Surface Projection To View (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/surface-projection-to-view-(realitykit)) — The projection-to-view transformation Matrix4x4 (Float).
- [Surface Screen Position (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/surface-screen-position-(realitykit)) — The coordinates of the currently-processed data in screen space.
- [Surface View Direction (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/surface-view-direction-(realitykit)) — A vector from a position in the scene to the view reference point.
- [Environment Radiance (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/environment-radiance-(realitykit)) — Returns an environment’s diffuse and specular radiance value based on real-world environment, and an IBL map that is either a developer-provided map or a default map.
- [Hover State (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/hover-state-(realitykit)) — Hover State to define custom hover effects.
- [Blurred Background (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/blurred-background-(realitykit)) — Returns a sample of the blurred background.
- [Geometry Modifier (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/geometry-modifier-(realitykit)) — A function that manipulates the location of a model’s vertices, run once per vertex.
- [Camera Index Switch (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/camera-index-switch-(realitykit)) — Render different results for each eye in a stereoscopic render.
- [Image 2D (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-(realitykit)) — A texture with RealityKit properties.
- [Image 2D LOD (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-lod-(realitykit)) — A texture with RealityKit properties and a explicit level of detail.
- [Image 2D Gradient (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-gradient-(realitykit)) — A texture with RealityKit properties and a specified LOD gradient.
- [Image 2D Pixel (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-pixel-(realitykit)) — A texture with RealityKit properties and pixel texture coordinates.
- [Image 2D LOD Pixel (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-lod-pixel-(realitykit)) — A texture with RealityKit properties, a explicit level of detail, and pixel texture coordinates.
- [Image 2D Gradient Pixel (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-gradient-pixel-(realitykit)) — A texture with RealityKit properties, a specified LOD gradient, and pixel texture coordinates.
- [Cube Image (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/cube-image-(realitykit)) — A texturecube with RealityKit properties.
- [Cube Image LOD (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/cube-image-lod-(realitykit)) — A texturecube with RealityKit properties and a explicit level of detail.
- [Cube Image Gradient (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/cube-image-gradient-(realitykit)) — A texturecube with RealityKit properties and a specified LOD gradient.
- [Image 2D Read (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-read-(realitykit)) — Direct texture read.
- [Image 3D (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-3d-(realitykit)) — A texture with RealityKit properties.
- [Image 3D LOD (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-3d-lod-(realitykit)) — A texture with RealityKit properties.
- [Image 3D Gradient (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-3d-gradient-(realitykit)) — A texture with RealityKit properties.
- [Image 3D Pixel (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-3d-pixel-(realitykit)) — A texture with RealityKit properties.
- [Image 3D LOD Pixel (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-3d-lod-pixel-(realitykit)) — A texture with RealityKit properties.
- [Image 3D Gradient Pixel (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-3d-gradient-pixel-(realitykit)) — A texture with RealityKit properties.
- [Image 2D Array (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-array-(realitykit)) — A texture with RealityKit properties.
- [Image 2D Array LOD (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-array-lod-(realitykit)) — A texture with RealityKit properties.
- [Image 2D Array Gradient (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-array-gradient-(realitykit)) — A texture with RealityKit properties.
- [Image 2D Array Pixel (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-array-pixel-(realitykit)) — A texture with RealityKit properties.
- [Image 2D Array LOD Pixel (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-array-lod-pixel-(realitykit)) — A texture with RealityKit properties.
- [Image 2D Array Gradient Pixel (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-array-gradient-pixel-(realitykit)) — A texture with RealityKit properties.
- [Image 2D Array Read (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-2d-array-read-(realitykit)) — Direct texture read.
- [Image 3D Read (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/image-3d-read-(realitykit)) — Direct texture read.
- [Screen-Space X Partial Derivative (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/screen-space-x-partial-derivative-(realitykit)) — Returns a high-precision partial derivative of the specified value with respect to the screen space X coordinate.
- [Screen-Space Y Partial Derivative (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/screen-space-y-partial-derivative-(realitykit)) — Returns a high-precision partial derivative of the specified value with respect to the screen space Y coordinate.
- [Absolute Derivatives Sum (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/absolute-derivatives-sum-(realitykit)) — Returns the sum of the absolute derivatives in X and Y using local differencing for p; that is, fabs(dfdx(p)) + fabs(dfdy(p)).
- [Power Positive (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/power-positive-(realitykit)) — Computes X to the power of Y, where X is >= 0.
- [Round Integral (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/round-integral-(realitykit)) — Rounds X to integral value using round ties to even rounding mode in floating-point format.
- [Reflection Diffuse (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/reflection-diffuse-(realitykit)) — Diffuse component of reflection.
- [Reflection Specular (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/reflection-specular-(realitykit)) — Specular component of reflection.
- [Fortran Difference and Minimum (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/fortran-difference-and-minimum-(realitykit)) — Returns X – Y if X > Y, or +0 if X <= Y.
- [Is Finite (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/is-finite-(realitykit)) — Returns true if the incoming value is finite.
- [Is Infinite (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/is-infinite-(realitykit)) — Returns true if the incoming value is infinite.
- [Is Not a Number (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/is-not-a-number-(realitykit)) — Returns true if the incoming value is a not a number (NaN).
- [Is Normal (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/is-normal-(realitykit)) — Test if the incoming value is a normalized floating-point value.
- [Is Ordered (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/is-ordered-(realitykit)) — Test if arguments are ordered.
- [Is Unordered (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/is-unordered-(realitykit)) — Test if arguments are unordered.
- [Sign Bit (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/sign-bit-(realitykit)) — Tests for sign bit.

### Subscripts
- [Multiply 24 (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/multiply-24-(realitykit)) — Multiplies two 24-bit integer values X and Y and returns the 32-bit integer result.
- [Multiply Add 24 (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/multiply-add-24-(realitykit)) — Multiplies two 24-bit integer values X and Y and returns the 32-bit integer result with 32-bit Z value added.

## Geometric

Access scene geometry while your graph runs.


### Overview

When the GPU applies your graph to a scene, geometric nodes reflect the data value the system is currently processing. Use these nodes to get details about that data value, such as its coordinates, normal, or tangent information. Alternatively, use the Reflect and Refract nodes to modify vectors relative to the current data value.


### Nodes
- [Position](https://developer.apple.com/documentation/shadergraph/geometric/position) — The coordinates of the currently-processed data in a given coordinate space.
- [Normal](https://developer.apple.com/documentation/shadergraph/geometric/normal) — The geometric normal of the currently-processed data in a given coordinate space.
- [Tangent](https://developer.apple.com/documentation/shadergraph/geometric/tangent) — The geometric tangent of the currently-processed data in a given coordinate space.
- [Bitangent](https://developer.apple.com/documentation/shadergraph/geometric/bitangent) — The geometric bitangent vector of the currently-processed data in a given coordinate space.
- [Texture Coordinates](https://developer.apple.com/documentation/shadergraph/geometric/texture-coordinates) — The 2D or 3D texture coordinates of the currently-processed data.
- [Geometry Color](https://developer.apple.com/documentation/shadergraph/geometric/geometry-color) — The color associated with the geometry at the currently-processed geometric position, typically defined by vertex color.
- [Geometric Property](https://developer.apple.com/documentation/shadergraph/geometric/geometric-property) — The value of the specified geometric property (defined using ) of the currently-bound geometry.
- [Reflect (RealityKit)](https://developer.apple.com/documentation/shadergraph/geometric/reflect-(realitykit)) — Reflects a vector about another vector.
- [Refract (RealityKit)](https://developer.apple.com/documentation/shadergraph/geometric/refract-(realitykit)) — Refracts a vector using a given normal and index of refraction (eta).

## Application

Get system values such as the current time or the direction of the up vector.


### Overview

Use Application nodes as input to other parts of your material. For example, you might use the current time as a unique input value to another node.


### Nodes
- [Time (float)](https://developer.apple.com/documentation/shadergraph/application/time-(float)) — The current time in seconds.
- [Up Direction](https://developer.apple.com/documentation/shadergraph/application/up-direction) — The direction of the up vector.

## Procedural

Add a constant number, vector, matrix, color, string, or other value to your graph.


### Overview

Use Procedural nodes to manage constant values within your graph. Configure a Procedural node with a constant value in the Reality Composer Pro inspector, and use it as an input to other nodes. You can also use the input side of the node to store values from other parts of your graph.


### Nodes
- [Float](https://developer.apple.com/documentation/shadergraph/procedural/float) — A constant floating-point numeric value.
- [Color3 (Float)](https://developer.apple.com/documentation/shadergraph/procedural/color3-(float)) — A constant Color3 (Float) value.
- [Color4 (Float)](https://developer.apple.com/documentation/shadergraph/procedural/color4-(float)) — A constant Color4 (Float) value.
- [Vector2 (Float)](https://developer.apple.com/documentation/shadergraph/procedural/vector2-(float)) — A constant Vector2 (Float) value.
- [Vector3 (Float)](https://developer.apple.com/documentation/shadergraph/procedural/vector3-(float)) — A constant Vector3 (Float) value.
- [Vector4 (Float)](https://developer.apple.com/documentation/shadergraph/procedural/vector4-(float)) — A constant Vector4 (Float) value.
- [Boolean](https://developer.apple.com/documentation/shadergraph/procedural/boolean) — A constant boolean (true/false) value.
- [Integer](https://developer.apple.com/documentation/shadergraph/procedural/integer) — A constant integer numeric value.
- [Matrix3x3 (Float)](https://developer.apple.com/documentation/shadergraph/procedural/matrix3x3-(float)) — A constant Matrix3x3 (Float) value.
- [Matrix4x4 (Float)](https://developer.apple.com/documentation/shadergraph/procedural/matrix4x4-(float)) — A constant Matrix4x4 (Float) value.
- [String](https://developer.apple.com/documentation/shadergraph/procedural/string) — A constant string (text) value.
- [Image File](https://developer.apple.com/documentation/shadergraph/procedural/image-file) — A constant path refering to an arbitrary image file on disk.
- [Half](https://developer.apple.com/documentation/shadergraph/procedural/half) — A constant half-precision floating-point numeric value.
- [Vector2 (Half)](https://developer.apple.com/documentation/shadergraph/procedural/vector2-(half)) — A constant half-precision floating-point Vector2 numeric value.
- [Vector3 (Half)](https://developer.apple.com/documentation/shadergraph/procedural/vector3-(half)) — A constant half-precision floating-point Vector3 numeric value.
- [Vector4 (Half)](https://developer.apple.com/documentation/shadergraph/procedural/vector4-(half)) — A constant half-precision floating-point Vector4 numeric value.
- [Matrix2x2 (Float)](https://developer.apple.com/documentation/shadergraph/procedural/matrix2x2-(float)) — A constant Matrix2x2 (Float) value.
- [Integer2](https://developer.apple.com/documentation/shadergraph/procedural/integer2) — A constant Integer2 value.
- [Integer3](https://developer.apple.com/documentation/shadergraph/procedural/integer3) — A constant Integer3 value.
- [Integer4](https://developer.apple.com/documentation/shadergraph/procedural/integer4) — A constant Integer4 value.

## 2D-Texture

Load and configure 2D texture files.


### Overview

Use these nodes to incorporate file-based textures into your material. In addition to loading textures from disk, you can use each node to customize the rendering behavior of the texture.

For example, a Tiled Image node repeats the original image to fill the surface with content. In addition to loading textures, you can use the Transform 2D node to apply an affine transform to a 2D vector.


### Nodes
- [Image](https://developer.apple.com/documentation/shadergraph/2d-texture/image) — A texture referencing a 2D image file.
- [Tiled Image](https://developer.apple.com/documentation/shadergraph/2d-texture/tiled-image) — Samples data from an image with provisions for offsetting and tiling in UV space.
- [UV Texture](https://developer.apple.com/documentation/shadergraph/2d-texture/uv-texture) — A MaterialX version of USD UV Texture reader.
- [Transform 2D](https://developer.apple.com/documentation/shadergraph/2d-texture/transform-2d) — A node that applies an affine transformation to a 2d input.

## 3D-Texture

Project multiple 2D images onto a surface to create a 3D texture.


### Nodes
- [Triplanar Projection](https://developer.apple.com/documentation/shadergraph/3d-texture/triplanar-projection) — Samples data from three images and projects each along its respective coordinate axis and blends them by geometric normal.

## 2D-Procedural

Generate 2D gradients, noise, and other patterns programmatically for your material.


### Overview

Use these nodes to generate gradients, noise, and other types of patterns and apply them to textures or other 2D surfaces. For example, you might use a horizontal or vertical ramp node to create a color gradient on a surface.


### Nodes
- [Ramp Horizontal](https://developer.apple.com/documentation/shadergraph/2d-procedural/ramp-horizontal) — A left-to-right linear value ramp (gradient) generator.
- [Ramp Vertical](https://developer.apple.com/documentation/shadergraph/2d-procedural/ramp-vertical) — A top-to-bottom linear value ramp (gradient) generator.
- [Ramp 4 Corners](https://developer.apple.com/documentation/shadergraph/2d-procedural/ramp-4-corners) — A four-point linear value ramp (gradient) generator.
- [Split Horizontal](https://developer.apple.com/documentation/shadergraph/2d-procedural/split-horizontal) — A left-to-right split matte, split at a specified U value.
- [Split Vertical](https://developer.apple.com/documentation/shadergraph/2d-procedural/split-vertical) — A top-to-bottom split matte, split at a specified V value.
- [Noise 2D](https://developer.apple.com/documentation/shadergraph/2d-procedural/noise-2d) — A 2D Perlin noise generator.
- [Cellular Noise 2D](https://developer.apple.com/documentation/shadergraph/2d-procedural/cellular-noise-2d) — A 2D cellular noise generator.
- [Worley Noise 2D](https://developer.apple.com/documentation/shadergraph/2d-procedural/worley-noise-2d) — A 2D Worley noise generator.

## 3D-Procedural

Generate 3D noise patterns programmatically for your material.


### Overview

3D Procedural nodes generate noise patterns that don’t repeat along the z-axis of your model. Use the nodes to add random variations to parts of your material, such as its surface roughness. Each node produces a different type of noise pattern based on a specific algorithm.


### Nodes
- [Noise 3D](https://developer.apple.com/documentation/shadergraph/3d-procedural/noise-3d) — A 3D Perlin noise generator.
- [Fractal Noise 3D](https://developer.apple.com/documentation/shadergraph/3d-procedural/fractal-noise-3d) — Zero-centered 3D fractal noise created by summing several octaves of 3D Perlin noise.
- [Cellular Noise 3D](https://developer.apple.com/documentation/shadergraph/3d-procedural/cellular-noise-3d) — A 3D cellular noise generator.
- [Worley Noise 3D](https://developer.apple.com/documentation/shadergraph/3d-procedural/worley-noise-3d) — A 3D Worley noise generator.

## Math

Perform a wide variety of mathematical and transformative operations on data values.


### Overview

Include `Math` nodes in your graph to perform typical mathematical operations on data values. A wide range of nodes are available, supporting basic arithmetic, trigonometry, logs, exponents, dot and cross products, and more. Some nodes operate on specific data types of values, but most operate on a wide range of data types, including numbers, colors, and vectors.


### Nodes
- [Add](https://developer.apple.com/documentation/shadergraph/math/add) — Adds two values.
- [Subtract](https://developer.apple.com/documentation/shadergraph/math/subtract) — Subtracts two values.
- [Multiply](https://developer.apple.com/documentation/shadergraph/math/multiply) — Multiplies two values.
- [Divide](https://developer.apple.com/documentation/shadergraph/math/divide) — Divides two values.
- [Modulo](https://developer.apple.com/documentation/shadergraph/math/modulo) — Outputs the remaining fraction after dividing the input by a value and subtracting the integer portion.
- [Abs](https://developer.apple.com/documentation/shadergraph/math/abs) — Outputs the per-channel absolute value of the input.
- [Floor](https://developer.apple.com/documentation/shadergraph/math/floor) — Outputs the nearest integer value, per-channel, less than or equal to the incoming values.
- [Ceiling](https://developer.apple.com/documentation/shadergraph/math/ceiling) — Outputs the nearest integer value, per-channel, greater than or equal to the incoming values.
- [Power](https://developer.apple.com/documentation/shadergraph/math/power) — Raises the incoming value to an exponent.
- [Sin](https://developer.apple.com/documentation/shadergraph/math/sin) — The sine of the incoming value in radians.
- [Cos](https://developer.apple.com/documentation/shadergraph/math/cos) — The cosine of the incoming value in radians.
- [Tan](https://developer.apple.com/documentation/shadergraph/math/tan) — The tangent of the incoming value in radians.
- [Asin](https://developer.apple.com/documentation/shadergraph/math/asin) — The arcsine of the incoming value in radians.
- [Acos](https://developer.apple.com/documentation/shadergraph/math/acos) — The arccosine of the incoming value in radians.
- [Atan2](https://developer.apple.com/documentation/shadergraph/math/atan2) — The arctangent of the expression (iny/inx) in radians.
- [Square Root](https://developer.apple.com/documentation/shadergraph/math/square-root) — The square root of the incoming value.
- [Natural Log](https://developer.apple.com/documentation/shadergraph/math/natural-log) — The natural log of the input.
- [Exp](https://developer.apple.com/documentation/shadergraph/math/exp) — Outputs ‘e’ to the power of the input.
- [Sign](https://developer.apple.com/documentation/shadergraph/math/sign) — The per-channel sign of the input value: -1 for negative, +1 for positive, 0 for zero.
- [Clamp](https://developer.apple.com/documentation/shadergraph/math/clamp) — Clamps the input per-channel to a specified range.
- [Min](https://developer.apple.com/documentation/shadergraph/math/min) — Outputs the minimum of two incoming values.
- [Max](https://developer.apple.com/documentation/shadergraph/math/max) — Outputs the maximum of two incoming values.
- [Normalize](https://developer.apple.com/documentation/shadergraph/math/normalize) — Outputs a normalized vector.
- [Magnitude](https://developer.apple.com/documentation/shadergraph/math/magnitude) — Outputs the float magnitude of a vector.
- [Dot Product](https://developer.apple.com/documentation/shadergraph/math/dot-product) — Outputs the dot product of two vectors.
- [Cross Product](https://developer.apple.com/documentation/shadergraph/math/cross-product) — Calculates the cross product vector of 2 input vectors.
- [Transform Point](https://developer.apple.com/documentation/shadergraph/math/transform-point) — Transforms a coordinate from one space to another.
- [Transform Vector](https://developer.apple.com/documentation/shadergraph/math/transform-vector) — Transforms a vector3 from one space to another.
- [Transform Normal](https://developer.apple.com/documentation/shadergraph/math/transform-normal) — Transforms a normal from one space to another.
- [Transform Matrix](https://developer.apple.com/documentation/shadergraph/math/transform-matrix) — Transforms a vector by a matrix.
- [Transpose](https://developer.apple.com/documentation/shadergraph/math/transpose) — Outputs the tranpose of a matrix.
- [Determinant](https://developer.apple.com/documentation/shadergraph/math/determinant) — Outputs the float determinant of a matrix.
- [Invert Matrix](https://developer.apple.com/documentation/shadergraph/math/invert-matrix) — Outputs the inverse of a matrix.
- [Rotate 2D](https://developer.apple.com/documentation/shadergraph/math/rotate-2d) — Rotates a Vector2 (Float) about the origin in 2D.
- [Rotate 3D](https://developer.apple.com/documentation/shadergraph/math/rotate-3d) — Rotates a Vector3 (Float) about a specified unit axis vector.
- [Place 2D](https://developer.apple.com/documentation/shadergraph/math/place-2d) — Transforms UV texture coordinates for 2D texture placement.
- [Round](https://developer.apple.com/documentation/shadergraph/math/round) — Rounds to the nearest integer value, per-channel.
- [Safe Power](https://developer.apple.com/documentation/shadergraph/math/safe-power) — Raises the incoming value to an exponent and assigns the sign of the base to the output.
- [Normal Map](https://developer.apple.com/documentation/shadergraph/math/normal-map) — Transforms a normal vector from object or tangent space into world space.
- [Fractional (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/fractional-(realitykit)) — Returns the fractional part of a floating point number.
- [One Minus (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/one-minus-(realitykit)) — Outputs one minus the input.
- [Normal Map Decode](https://developer.apple.com/documentation/shadergraph/math/normal-map-decode) — Remaps a normal’s value from [0,1] to [-1,1] by applying 2x-1.
- [Max3 (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/max3-(realitykit)) — Outputs the maximum of three incoming values.
- [Min3 (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/min3-(realitykit)) — Outputs the minimum of three incoming values.
- [Fractional (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/fractional-(realitykit)) — Returns the fractional part of a floating point number.
- [Inverse Hyperbolic Cos](https://developer.apple.com/documentation/shadergraph/math/inverse-hyperbolic-cos) — The inverse hyperbolic cosine of the incoming value in radians.
- [Inverse Hyperbolic Sin](https://developer.apple.com/documentation/shadergraph/math/inverse-hyperbolic-sin) — The inverse hyperbolic sine of the incoming value in radians.
- [Atan](https://developer.apple.com/documentation/shadergraph/math/atan) — The arctangent of the incoming value in radians.
- [Inverse Hyperbolic Tan](https://developer.apple.com/documentation/shadergraph/math/inverse-hyperbolic-tan) — The hyperbolic arc tangent of the incoming value in radians.
- [Copy Sign (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/copy-sign-(realitykit)) — Return x with its sign changed to match the sign of y.
- [Hyperbolic Cos](https://developer.apple.com/documentation/shadergraph/math/hyperbolic-cos) — The hyperbolic cosine of the incoming value in radians.
- [Cos Pi (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/cos-pi-(realitykit)) — Compute cos(πX).
- [Exponential 2 (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/exponential-2-(realitykit)) — Exponential Base 2 of X.
- [Exponential 10 (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/exponential-10-(realitykit)) — Exponential Base 10 of X.

### Subscripts
- [Distance (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/distance-(realitykit)) — Returns the distance between X and Y.
- [Distance Square (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/distance-square-(realitykit)) — Returns the square of the distance between X and Y.
- [Fused Multiply-Add (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/fused-multiply-add-(realitykit)) — Returns (A * B) + C.
- [Hyperbolic Sin](https://developer.apple.com/documentation/shadergraph/math/hyperbolic-sin) — The hyperbolic sine of the incoming value in radians.
- [Hyperbolic Tan](https://developer.apple.com/documentation/shadergraph/math/hyperbolic-tan) — The hyperbolic tangent of the incoming value in radians.
- [Log 10](https://developer.apple.com/documentation/shadergraph/math/log-10) — The log base 10 of the input.
- [Log 2](https://developer.apple.com/documentation/shadergraph/math/log-2) — The log base 2 of the input.
- [Magnitude Square (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/magnitude-square-(realitykit)) — Outputs the float magnitude of a vector, squared.
- [Median3 (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/median3-(realitykit)) — Returns the middle value of three incoming values.
- [Modulo (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/modulo-(realitykit)) — Outputs the remaining fraction after dividing the input by a value and subtracting the integer portion.
- [Reciprocal Square Root (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/reciprocal-square-root-(realitykit)) — Computes inverse square root of X.
- [Sin Pi (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/sin-pi-(realitykit)) — Compute sin(πX).
- [Tan Pi (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/tan-pi-(realitykit)) — Compute tan(πX).
- [Truncate (RealityKit)](https://developer.apple.com/documentation/shadergraph/math/truncate-(realitykit)) — Rounds X to integral value using the round-toward-zero rounding mode.

## Adjustment

Modify or convert values, or ranges of values, from one form to another.


### Overview

Use Adjustment nodes to adjust color values, convert between different color formats, or map input values to a different set of outputs based on rules you specify. For example, you might use these nodes to adapt the output from one node to match the expected input for another node.


### Nodes
- [Remap](https://developer.apple.com/documentation/shadergraph/adjustment/remap) — Linearly remaps incoming values from one range to another.
- [Smooth Step](https://developer.apple.com/documentation/shadergraph/adjustment/smooth-step) — Outputs a smooth remapping from low-high to 0-1.
- [Luminance](https://developer.apple.com/documentation/shadergraph/adjustment/luminance) — Outputs a grayscale value containing the luminance of the incoming RGB color in all color channels.
- [RGB to HSV](https://developer.apple.com/documentation/shadergraph/adjustment/rgb-to-hsv) — Converts a color from RGB to HSV space.
- [HSV to RGB](https://developer.apple.com/documentation/shadergraph/adjustment/hsv-to-rgb) — Converts a color from HSV to RGB space.
- [Contrast](https://developer.apple.com/documentation/shadergraph/adjustment/contrast) — Increases or decreases contrast of values using a linear slope multiplier.
- [Range](https://developer.apple.com/documentation/shadergraph/adjustment/range) — Remaps incoming values from one range to another.
- [HSV Adjust](https://developer.apple.com/documentation/shadergraph/adjustment/hsv-adjust) — Adjusts the hue, saturation and value of an RGB color by a vector .
- [Saturate](https://developer.apple.com/documentation/shadergraph/adjustment/saturate) — Adjusts the saturation of a color.
- [Step (RealityKit)](https://developer.apple.com/documentation/shadergraph/adjustment/step-(realitykit)) — Outputs a 1 or a 0 depending on whether the input is greater than or less than the edge value.

## Compositing

Generate a single output from the combination of multiple data values.


### Overview

The compositing process takes multiple input values and combines them in varying proportions to create a single output. You can use Compositing nodes to combine textures and achieve a specific appearance. For example, you might show a background texture only in places where the foreground texture is transparent. Compositing nodes support the combination of colors, but also other data types, such as vectors and floating-point numbers.


### Nodes
- [Premultiply](https://developer.apple.com/documentation/shadergraph/compositing/premultiply) — Multiplies the RGB channels of the input by the alpha channel.
- [Unpremultiply](https://developer.apple.com/documentation/shadergraph/compositing/unpremultiply) — Divides the RGB channels of the input by the alpha channel.
- [Additive Mix](https://developer.apple.com/documentation/shadergraph/compositing/additive-mix) — Adds foreground and background values.
- [Subtractive Mix](https://developer.apple.com/documentation/shadergraph/compositing/subtractive-mix) — Subtracts foreground from background values.
- [Difference](https://developer.apple.com/documentation/shadergraph/compositing/difference) — Outputs the distance between foreground and background values.
- [Burn](https://developer.apple.com/documentation/shadergraph/compositing/burn) — A blend operation that darkens the foreground layer using the background.
- [Dodge](https://developer.apple.com/documentation/shadergraph/compositing/dodge) — A blend operation that lightens the background layer depending on the foreground.
- [Screen](https://developer.apple.com/documentation/shadergraph/compositing/screen) — A blend operation that lightens areas that are darker than white.
- [Overlay](https://developer.apple.com/documentation/shadergraph/compositing/overlay) — A blend operation that multiplies dark areas and screens light areas.
- [Disjoint Over](https://developer.apple.com/documentation/shadergraph/compositing/disjoint-over) — A merge operation that layers foreground over background color, but assumes no overlap in partially transparent areas covered by both.
- [In](https://developer.apple.com/documentation/shadergraph/compositing/in) — Outputs areas of foreground that overlap with the alpha of background.
- [Mask](https://developer.apple.com/documentation/shadergraph/compositing/mask) — Outputs areas of background that overlap with the alpha of foreground.
- [Matte](https://developer.apple.com/documentation/shadergraph/compositing/matte) — A merge operation that layers premultiplied foreground over background.
- [Out](https://developer.apple.com/documentation/shadergraph/compositing/out) — Outputs areas of foreground that do not overlap with background.
- [Over](https://developer.apple.com/documentation/shadergraph/compositing/over) — A merge operation that layers foreground over background, using the alpha of the foreground.
- [Inside](https://developer.apple.com/documentation/shadergraph/compositing/inside) — Multiplies a mask to all channels of the input.
- [Outside](https://developer.apple.com/documentation/shadergraph/compositing/outside) — Multiplies (1 - mask) to all channels of the input.
- [Mix](https://developer.apple.com/documentation/shadergraph/compositing/mix) — Mixes foreground and background inputs, weighting based on mix value.

## Data

Convert data values to different formats, or manipulate individual elements within a data structure.


### Overview

Use data nodes to take one type of data and manipulate it to get a different type of value. Data manipulations can take several forms:

- Convert one data type to a different format.
- Combine individual elements to create a single data type.
- Separate a single data type into its component elements.
- Extract or manipulate individual values from a data structure and use them as input to other nodes.


### Nodes
- [Convert](https://developer.apple.com/documentation/shadergraph/data/convert) — Converts a stream from one data type to another.
- [Swizzle](https://developer.apple.com/documentation/shadergraph/data/swizzle) — Performs an arbitrary permutation of the channels of the input stream, returning a new stream of the specified type.
- [Combine 2](https://developer.apple.com/documentation/shadergraph/data/combine-2) — Combines the channels from two streams into two channels of a single output stream of a compatible type.
- [Combine 3](https://developer.apple.com/documentation/shadergraph/data/combine-3) — Combines the channels from three streams into three channels of a single output stream of a compatible type.
- [Combine 4](https://developer.apple.com/documentation/shadergraph/data/combine-4) — Combines the channels from four streams into four channels of a single output stream of a compatible type.
- [Extract](https://developer.apple.com/documentation/shadergraph/data/extract) — Generates a float stream from one channel of a color​N o​r vector​N ​stream.
- [Separate 2](https://developer.apple.com/documentation/shadergraph/data/separate-2) — Outputs each of the channels of a vector2 or integer2 as individual float or integer outputs.
- [Separate 3](https://developer.apple.com/documentation/shadergraph/data/separate-3) — Outputs each of the channels of a color3, vector3, or integer3 as individual float or integer outputs.
- [Separate 4](https://developer.apple.com/documentation/shadergraph/data/separate-4) — Outputs each of the channels of a color4, vector4, or integer4 as individual float or integer outputs.
- [Primvar Reader](https://developer.apple.com/documentation/shadergraph/data/primvar-reader) — A node that provides the ability for shading networks to consume data defined on geometry.

## Logic

Perform Boolean operations and other logical comparisons on data values.


### Overview

Use Logic nodes to facilitate decision trees and other logic-based choices within your graph. You can perform comparisons for equality or to determine if one value is larger than another. You can also perform logic operations on Boolean values.


### Nodes
- [If Greater](https://developer.apple.com/documentation/shadergraph/logic/if-greater) — Outputs True Result or False Result depending on whether value1 > value2.
- [If Greater Or Equal](https://developer.apple.com/documentation/shadergraph/logic/if-greater-or-equal) — Outputs True Result or False Result depending on whether value1 >= value2.
- [If Equal](https://developer.apple.com/documentation/shadergraph/logic/if-equal) — Outputs True Result or False Result depending on whether value1 == value2.
- [Switch](https://developer.apple.com/documentation/shadergraph/logic/switch) — Outputs the value from one of ten input streams, according to a selector .
- [And (RealityKit)](https://developer.apple.com/documentation/shadergraph/logic/and-(realitykit)) — Boolean operation in1 && in2.
- [Or (RealityKit)](https://developer.apple.com/documentation/shadergraph/logic/or-(realitykit)) — Boolean operation in1 || in2.
- [XOR (RealityKit)](https://developer.apple.com/documentation/shadergraph/logic/xor-(realitykit)) — Returns true if only one of the inputs is true.
- [Not (RealityKit)](https://developer.apple.com/documentation/shadergraph/logic/not-(realitykit)) — Returns !input.
- [Select (RealityKit)](https://developer.apple.com/documentation/shadergraph/logic/select-(realitykit)) — Selects B if conditional is true, A if false.
- [Multiply Add 24 (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/multiply-add-24-(realitykit)) — Multiplies two 24-bit integer values X and Y and returns the 32-bit integer result with 32-bit Z value added.
- [Multiply 24 (RealityKit)](https://developer.apple.com/documentation/shadergraph/realitykit/multiply-24-(realitykit)) — Multiplies two 24-bit integer values X and Y and returns the 32-bit integer result.

## Material

Encapsulate a set of shader graph nodes into a single module.


### Overview

`Material` nodes help you divide your graph into subsets of nodes, each with distinct inputs and outputs. A [Node Graph](https://developer.apple.com/documentation/shadergraph/material/node-graph) appears as a single node within your main graph. Editing that node hides the main graph and gives you an empty space that you fill with additional nodes. Use that space to build a specific portion of your main graph, and use the [Node Graph](https://developer.apple.com/documentation/shadergraph/material/node-graph) to define the inputs and outputs to that separate space.


### Nodes
- [Node Graph](https://developer.apple.com/documentation/shadergraph/material/node-graph) — A node that can contain shading nodes and other node graphs.

## Organization

Modify the visual flow of data within your graph without changing any values.


### Overview

Use organization nodes to manage the visual complexity of your graph. Place a [Dot](https://developer.apple.com/documentation/shadergraph/organization/dot) node between two other nodes, and use the node to reroute connection lines around other nodes and elements. Dot nodes pass the data on their input side directly to the output side without modification.


### Nodes
- [Dot](https://developer.apple.com/documentation/shadergraph/organization/dot) — A pass-through node used for visually routing edges in the graph.
