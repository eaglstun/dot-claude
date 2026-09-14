# Mobile, resources, and builds

## Project settings and resources

`game.project` is an INI-style project file and the root of the resource graph. Resource settings use compiled extensions such as `.collectionc` where required. Runtime code can inspect configuration with `sys.get_config()`. Keep secrets out of the project and bundle. See the [project settings manual](https://defold.com/manuals/project-settings/).

The bundler follows resource references and omits unreachable assets. This is desirable until code constructs a resource path dynamically. For runtime-loaded raw files, include the directory in `custom_resources` and load it with `sys.load_resource()`. Use bundle resources when native extensions or platform packaging need files copied into the final application. Verify the final graph with a build report.

## Editor and Bob

Use the editor for ordinary iterative builds. Use Bob, Defold's command-line build tool, for reproducible local and CI builds. Match the Bob version to the project and engine version and satisfy the Java version documented for that release; the current Bob manual specifies OpenJDK 25.

A typical clean release flow is conceptually:

```sh
java -jar bob.jar --archive --variant release resolve distclean build bundle
```

Add the correct `--platform`, output, signing, and bundle-format options for the target. Do not blindly copy command lines across engine versions; verify flags in the current [Bob manual](https://defold.com/manuals/bob/).

Release builds remove or disable development facilities such as profiling and may strip logging and reverse-hash data depending on settings. Test the release artifact itself, not only editor or debug builds. Native extensions require dependency resolution and network access during suitable build stages.

## iOS

- Create iOS bundles from the macOS editor or Bob on a suitable build host.
- Device builds require an Apple signing identity and provisioning profile; simulator builds can be unsigned.
- Use a development app for rapid iteration and hot reload where appropriate, but validate a signed release bundle on hardware.
- Keep bundle identifier, version, orientations, capabilities, icons, launch assets, and privacy declarations consistent with the Apple project configuration.
- If supplying a custom `Info.plist`, preserve Defold's required entries and confirm the file remains included in resource discovery.

Follow the current [iOS manual](https://defold.com/manuals/ios/) for signing, simulator architectures, installation, and App Store packaging.

## Android

- Produce an APK for direct installation and testing or an AAB for Google Play distribution.
- Release artifacts require a keystore and stable signing configuration. Protect credentials outside source control.
- Validate package name, SDK levels, manifest merging, permissions, icons, orientations, and native architectures.
- Use `adb` and device logs for install and runtime failures, then test the actual release variant on representative hardware.

Follow the current [Android manual](https://defold.com/manuals/android/) for toolchain, signing, installation, and bundle formats.

## HTML5 and cross-platform checks

HTML5 is useful for quick sharing, but browser audio startup, storage, input, viewport scaling, memory, and asset download behavior differ from native mobile. Keep platform services behind small modules, use feature or config checks, and test every target rather than assuming identical behavior.

For all targets:

1. Generate a build report and inspect large resources.
2. Exercise pause and resume, focus loss, backgrounding, audio interruption, and orientation changes.
3. Test touch ergonomics and safe areas on physical devices.
4. Profile CPU, GPU, memory, draw calls, and live instance counts under worst-case gameplay.
5. Consider an [application manifest](https://defold.com/manuals/app-manifest/) only after measuring; removing engine features can shrink the binary but creates a maintenance obligation.
