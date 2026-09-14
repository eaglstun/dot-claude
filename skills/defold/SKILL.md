---
name: defold
description: Build, debug, and ship games with Defold, including Lua scripts, game objects and components, collections, factories and proxies, messages, input, rendering, resources, and mobile or HTML5 bundling. Use when working in a Defold project (game.project, .collection, .go, .script, .gui_script, or .render_script), evaluating Defold for a game, or porting a game to Defold.
---

# Defold

Treat Defold as its own component-and-message engine rather than mapping Unity scene or general ECS conventions onto it.

## Start with the project

1. Read `game.project`; it is the project root and the source of engine, bootstrap, display, platform, and resource settings.
2. Inspect the main collection and nearby `.collection`, `.go`, `.script`, `.gui_script`, `.render_script`, and input-binding files.
3. Check the project's Defold version before relying on newer lifecycle or API behavior.
4. Preserve established URL, message, factory, and collection conventions unless they cause the problem.

## Route the work

- Read [architecture-and-lifecycle.md](references/architecture-and-lifecycle.md) when designing gameplay structure, choosing a creation or loading mechanism, debugging messages or callbacks, handling input, or changing rendering.
- Read [mobile-and-builds.md](references/mobile-and-builds.md) when editing `game.project`, loading runtime assets, invoking Bob, reducing bundle size, signing, or packaging for iOS, Android, or HTML5.
- Use the [stable Lua API reference](https://defold.com/ref/stable/overview_defoldlua/) for exact signatures and availability. Use the versioned reference when the project is pinned to an older release.

## Working rules

- Keep per-instance script state on `self`; reserve module state for deliberately shared data.
- Prefer messages and explicit URLs across component boundaries. Cache URLs and hashes used in hot paths.
- Use a factory for repeated game objects in the current world, a collection factory for repeated hierarchies in the current world, and a collection proxy for independently loaded worlds or levels.
- Account for deferred creation, deletion, and message delivery. Do not assume a just-deleted object has disappeared during the current callback.
- Acquire input focus explicitly. Input is delivered down a focus stack and can be consumed.
- Prefer the default renderer for ordinary 2D work. Introduce a custom render script only when the pipeline genuinely needs to change.
- Respect resource reachability: unreferenced assets are omitted from bundles unless included as custom or bundled resources.
- Tune component maxima and preallocation from measurements. Do not add an application-level object pool merely to avoid Defold creation overhead; the engine already pools objects internally.
- Test mobile input, lifecycle, performance, and release bundles on real target devices.

## Source of truth

When behavior is version-sensitive or uncertain, verify it in the [official manuals](https://defold.com/manuals/), [API reference](https://defold.com/ref/stable/overview_defoldlua/), or the project editor's bundled documentation before changing code.
