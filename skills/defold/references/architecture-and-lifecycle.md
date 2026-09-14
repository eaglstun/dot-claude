# Architecture and lifecycle

## Mental model

| Defold resource | Role | Use it for |
|---|---|---|
| `game.project` | Project root and settings | Bootstrap collection, display, engine limits, dependencies, platform settings |
| Collection | A hierarchy of game objects and nested collections | A world, screen, level, or reusable hierarchy |
| Game object | Addressable container with an id and transform | A gameplay entity composed from components |
| Component | Behavior or presentation attached to a game object | Scripts, sprites, models, collision objects, sounds, cameras, factories |
| Factory | Spawns one game-object prototype into the current collection world | Bullets, pickups, enemies, effects |
| Collection factory | Spawns a collection hierarchy into the current world | Repeated composite entities or room chunks |
| Collection proxy | Loads a collection as a separate world/socket | Level switching, independently managed worlds, separate physics worlds |

A collection used as a prototype is not automatically a separate runtime world. Factory-created objects and collection-factory hierarchies belong to the world containing the factory. A proxy owns a separate collection world with an explicit load, initialize, enable, disable, finalize, and unload lifecycle. See the official [building blocks](https://defold.com/manuals/building-blocks/), [factory](https://defold.com/manuals/factory/), [collection factory](https://defold.com/manuals/collection-factory/), and [collection proxy](https://defold.com/manuals/collection-proxy/) manuals.

## Scripts and state

Defold has three component script contexts:

- `.script` controls game-object gameplay components.
- `.gui_script` controls nodes within one GUI scene.
- `.render_script` controls the renderer and draw pipeline.

Their available APIs differ. Put reusable, context-independent code in Lua modules and require it from scripts. Keep instance state on `self`; top-level locals and required modules are shared within their Lua context. Review the [script manual](https://defold.com/manuals/script/) before moving code between script types.

## Addresses and messages

An address is a URL with socket, path, and fragment: `socket:/game_object#component`. Common relative forms include `.` for the current game object and `#component` for a sibling component. Prefer explicit URLs when ownership crosses a game-object or collection boundary.

Messages are delivered through the engine rather than as immediate function calls. Treat `msg.post()` as asynchronous and do not depend on the recipient running before the sender callback returns. Hash recurring message ids once rather than rebuilding them in hot loops. The [message passing manual](https://defold.com/manuals/message-passing/) documents URL resolution and delivery.

## Lifecycle

The callbacks commonly involved in gameplay are:

1. `init(self)` initializes a component.
2. `update(self, dt)` performs frame-rate-dependent work.
3. `fixed_update(self, dt)` performs fixed-step work when enabled in project settings.
4. `late_update(self, dt)` performs work after ordinary updates on supported engine versions.
5. `on_message(self, message_id, message, sender)` receives posted messages.
6. `on_input(self, action_id, action)` receives focused input.
7. `final(self)` releases script-owned resources before destruction.

Creation, deletion, and message delivery have defined sequencing but may be deferred within a frame. After calling `go.delete()`, stop treating the target as immediately absent; arrange local state so repeated contacts or messages cannot act on it again. Consult the current [application lifecycle manual](https://defold.com/manuals/application-lifecycle/) when ordering matters.

Components and game objects can be enabled or disabled with messages. Disabling can suspend update, rendering, and collision participation without destroying the object, but verify the behavior of the specific component type in the [components manual](https://defold.com/manuals/components/).

## Dynamic content

Choose the smallest mechanism matching lifetime and isolation:

- Factory: one game object, current world, fast repeated spawning.
- Collection factory: a reusable hierarchy, current world.
- Collection proxy: a separately loaded world with explicit lifecycle and memory control.

Set `max_instances` high enough for the worst live count and use build reports and profiling to tune it. Delete transient objects when done. Defold already pools game objects internally, so a second pooling layer usually adds stale-state and lifecycle bugs without helping performance.

For proxies, normally send `load`, wait for `proxy_loaded`, then send `init` and `enable`. If the loaded world needs input, acquire input focus from an object inside that world. Async loading can reduce stalls, but code must handle completion and cancellation states.

## Input across desktop and mobile

Input reaches scripts that have sent `acquire_input_focus`. Focused objects form a stack; returning `true` from `on_input` consumes the action before lower recipients receive it. Release focus when a screen or world stops owning input. See the [input manual](https://defold.com/manuals/input/).

For pointer gameplay:

- A mouse-button binding also provides single-touch input on mobile.
- Multi-touch uses a touch trigger and reports a collection of touch points.
- Do not bind mouse and multi-touch to the same action unless the code deliberately handles both reports.
- Convert screen coordinates to world coordinates through the active camera and render mapping; do not assume display pixels equal world units.

The [mouse and touch manual](https://defold.com/manuals/input-mouse-and-touch/) covers platform mapping details.

## Rendering

The render script selects tagged components with predicates, configures render state and matrices, and issues draw calls. The stock renderer is the right baseline for most sprite-oriented games. If a custom pipeline is necessary, begin from the current default script, keep the bootstrap render resource configured in `game.project`, and make camera and projection ownership explicit. See the [render manual](https://defold.com/manuals/render/).
