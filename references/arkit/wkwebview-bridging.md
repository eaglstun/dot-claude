---
topic_id: "v2:OEEE"
topic_path: "rust-arkit/arkit-features"
semantic_id: "JLyDFXR566f7isIczYDU2emULCpuQAAM"
related_ids:
  - "JHgGF37YMwO43R-95YLLxWmXCqNGYAAC"
  - "JKkJs_hYJq9qmYu82YrsWsoNXmd8wAAN"
---
# WKWebView ↔ JavaScript bridging (WebKit)

Source:

- <https://developer.apple.com/documentation/webkit/wkwebview>
- <https://developer.apple.com/documentation/webkit/wkscriptmessagehandler>
- <https://developer.apple.com/documentation/webkit/wkusercontentcontroller>
- <https://developer.apple.com/documentation/webkit/wkscriptmessage>

Fetched: 2026-06-27

## What it's for

`WKWebView` hosts web content in a native app. For this project it is **the only channel**
between native iOS code (ARKit, Core Motion) and the WebGL experiments. Two directions:

- **Native → JS:** `WKWebView.evaluateJavaScript(...)` / `callAsyncJavaScript(...)` — push a
  pose, an event, or call a function inside the page.
- **JS → Native:** `WKScriptMessageHandler` registered on the web view's
  `WKUserContentController`; the page posts with
  `window.webkit.messageHandlers.<name>.postMessage(...)`.

> This is how any native sensor data would reach the experiments. The shell already uses a
> `WKWebView` (`ios/KaraokeVR/WebVRView.swift`) and grants motion permission via `WKUIDelegate`
> so the page's own `deviceorientation`/`DeviceOrientationControls` work with **no JS changes**
> (see `headset` skill `ios-webview-wrapper-notes.md`). The methods below are what a future
> ARKit/Core Motion bridge would use to inject a pose per frame — e.g. `evaluateJavaScript` a
> synthetic `DeviceOrientationEvent`, or `postMessage` poses up to native.

## WKWebView essentials

```swift
@MainActor init(frame: CGRect, configuration: WKWebViewConfiguration)   // iOS 8.0+
@NSCopying var configuration: WKWebViewConfiguration { get }            // iOS 8.0+
```

`WKWebViewConfiguration.userContentController` (a `WKUserContentController`) is where you
register message handlers and inject user scripts **before** the web view loads — wire it up
at init time, not after.

## Native → JS: executing JavaScript

```swift
// iOS 8.0+  — classic completion-handler form
@MainActor func evaluateJavaScript(_ javaScriptString: String,
    completionHandler: (@MainActor @Sendable (Any?, (any Error)?) -> Void)? = nil)

// iOS 8.0+  — Swift async form (same selector)
@MainActor func evaluateJavaScript(_ javaScriptString: String) async throws -> Any?

// iOS 14.0+ — evaluate in a specific frame + content world
@MainActor func evaluateJavaScript(_ javaScriptString: String,
    in frame: WKFrameInfo?, in contentWorld: WKContentWorld,
    completionHandler: ((Result<Any, any Error>) -> Void)? = nil)

// iOS 15.0+ — async variant of the above
@MainActor func evaluateJavaScript(_ javaScript: String,
    in frame: WKFrameInfo? = nil, contentWorld: WKContentWorld) async throws -> Any?

// iOS 14.0+ — call a function body with typed arguments (no string interpolation of values)
@MainActor func callAsyncJavaScript(_ functionBody: String,
    arguments: [String : Any] = [:], in frame: WKFrameInfo? = nil,
    in contentWorld: WKContentWorld,
    completionHandler: ((Result<Any, any Error>) -> Void)? = nil)

// iOS 15.0+ — async variant
@MainActor func callAsyncJavaScript(_ functionBody: String,
    arguments: [String : Any] = [:], in frame: WKFrameInfo? = nil,
    contentWorld: WKContentWorld) async throws -> Any?
```

Notes:

- All `@MainActor` — call from the main thread/actor.
- For a per-frame pose push, `callAsyncJavaScript(_:arguments:in:in:completionHandler:)`
  (iOS 14+) is cleaner than `evaluateJavaScript`: you pass numbers as typed `arguments`
  instead of building a JS string, avoiding interpolation/escaping bugs in a hot loop.
- `contentWorld` (`WKContentWorld.page` for the page's own world, `.defaultClient` for an
  isolated one) controls whether your script shares globals with the page. To dispatch a
  `DeviceOrientationEvent` the page's listeners can see, target the **page** world.
- iPhone 17 Pro / current iOS: every form above is available, including the iOS 15 async ones.

## JS → Native: message handlers

```swift
// WKScriptMessageHandler — iOS 8.0+
protocol WKScriptMessageHandler : NSObjectProtocol
func userContentController(_ userContentController: WKUserContentController,
                           didReceive message: WKScriptMessage)        // iOS 8.0+

// WKScriptMessage — iOS 8.0+  (@MainActor class)
//   .body: Any  (JS value marshalled to NSNumber/NSString/NSDate/NSArray/NSDictionary/NSNull)
//   .name: String  .frameInfo  .webView  .world
```

Register / unregister on `WKUserContentController`:

```swift
func add(_ scriptMessageHandler: any WKScriptMessageHandler, name: String)                       // iOS 8.0+
func add(_ scriptMessageHandler: any WKScriptMessageHandler,
         contentWorld: WKContentWorld, name: String)                                              // iOS 14.0+
func addScriptMessageHandler(_ handler: any WKScriptMessageHandlerWithReply,
         contentWorld: WKContentWorld, name: String)                                              // iOS 14.0+ (can return a value/promise to JS)
func removeScriptMessageHandler(forName name: String)                                             // iOS 8.0+
func removeScriptMessageHandler(forName name: String, contentWorld: WKContentWorld)               // iOS 14.0+
func removeAllScriptMessageHandlers(from contentWorld: WKContentWorld)                            // iOS 14.0+
func removeAllScriptMessageHandlers()                                                             // iOS 14.0+
```

After `add(_:name:"foo")`, the page calls `window.webkit.messageHandlers.foo.postMessage(...)`,
which lands in `userContentController(_:didReceive:)` with `message.name == "foo"`. Use
`WKScriptMessageHandlerWithReply` (iOS 14+) when JS needs a value back (it gets a Promise).

## Deprecation notes

No deprecations on the symbols above as of this fetch. All are available on iOS, iPadOS, and
visionOS. The only retired API in this area is the legacy `UIWebView` (not `WKWebView`), long
removed — don't use it.

## Direction-picking cheat sheet (for this project)

- **Push a native head pose into the page each frame:** `callAsyncJavaScript` (iOS 14+) into
  `WKContentWorld.page`, dispatching a `DeviceOrientationEvent` so `DeviceOrientationControls`
  consumes it unchanged — matches the documented Core Motion fallback bridge.
- **Let the page ask native for something / report clicker or state:** register a
  `WKScriptMessageHandler` and `postMessage` from JS.
