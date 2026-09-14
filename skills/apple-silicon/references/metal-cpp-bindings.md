---
semantic_id: "pHM7wo84Jt9FhhOHy3FLJ5AhV4MdIAAJ"
related_ids:
  - "uEMz9ix-pFpEVhN_W3svIpADFdaYgAAH"
  - "5d-8s5m-ehRjzyKEy3F3q57tXImVMAAM"
---
# metal-cpp — Metal from C++ without Objective-C

The alternative to `objcpp-interop-for-mm-files.md`: instead of writing `.mm` files, drive Metal
from plain `.cpp`. **Both are manual retain/release** — the ownership discipline in that file is
the same discipline here, in different syntax.

Sources:

- <https://developer.apple.com/metal/cpp/> — the landing page
- <https://github.com/apple/metal-cpp> — **Apple's own GitHub org**; `README.md` there is Apple's word
- WWDC22 session 10160, "Program Metal in C++ with metal-cpp"
  <https://developer.apple.com/videos/play/wwdc2022/10160/>
- `LearnMetalCPP.zip` via <https://developer.apple.com/metal/sample-code/>

Everything below was **verified by compiling and running** on Apple M4 Max / macOS Darwin 25.5.0 /
Xcode 26.6 (Apple clang 21.0.0), against `apple/metal-cpp` `main` @ `27c4382`, tag
`release/metal-cpp_macOS27_iOS27`. Error messages are real transcript, not reconstructed.

Fetched: 2026-08-19

---

## 0. The ZIP downloads are gone

Apple's landing page no longer offers ZIPs — it says *"Access the headers from GitHub."*
Confirmed by request:

```
metal-cpp_macOS15.2_iOS18.2.zip   HTTP 200   (still hosted)
metal-cpp_macOS26_iOS26.zip       HTTP 404
metal-cpp_macOS27_iOS27.zip       HTTP 404
```

Distribution moved to git tags after macOS 15.2 / iOS 18.2. **Any instruction to "download the zip
from developer.apple.com/metal/cpp" now describes a page that doesn't say that.** Clone the repo
and check out a release tag:

```
release/metal-cpp_macOS12_iOS15      … through …
release/metal-cpp_macOS26_iOS26
release/metal-cpp_macOS26.4_iOS26.4
release/metal-cpp_macOS27_iOS27
```

Apache-2.0, tags signed by an Apple engineer. Unambiguously official.

`Metal/MTLVersion.hpp` carries `METALCPP_VERSION_MAJOR/MINOR/PATCH`, but it tracks the **Metal
framework build**, not a semver of the bindings (macOS 15.2 → 367.4.2, macOS 26 → 370.63.1,
macOS 26.4 → *unchanged* 370.63.1, macOS 27 → 381.0.0). It doesn't exist at all in the macOS
12/13 releases, so don't use it for old-version detection.

---

## 1. The deal

**Header-only.** No `.a`, no `.dylib`, no build step. One include directory and one `.cpp`.

**C++17 minimum**, because `NS::Object` uses `constexpr`. Apple states it on both the landing page
and the README. The actual first hard error under `-std=c++14` is *not* the `constexpr if` (that's
only a warning) — it's:

```
NSSharedPtr.hpp:56:83: error: no template named 'is_convertible_v' in namespace 'std'
```

C++20 and C++23 both build clean.

**Overhead — Apple's exact words:** *"No measurable overhead compared to calling Metal Objective-C
headers, due to inlining of C++ function calls."*

That holds. Every method is an `inline __attribute__((always_inline))` wrapper around
`objc_msgSend`. Measured, 20M iterations of `buf->length()` vs `[buf length]` at `-O2` in one
binary:

```
obj-c  [buf length]     : 1.438 ns/call
metal-cpp buf->length() : 1.448 ns/call     ratio 1.007
```

**Read that correctly: metal-cpp is not *faster* than Objective-C, it is *the same as* it.** You
still pay full dynamic dispatch on every call. It removes the language shim, not the message send.

**clang only.** The block types (`void (^)(...)`) rule out GCC, and `doesRequireMsgSendStret` has
an `#error "Unsupported architecture!"` for anything non-Apple.

---

## 2. Build integration — where everyone gets stuck

### The `*_PRIVATE_IMPLEMENTATION` macros

metal-cpp never links Metal's Objective-C classes directly. For every class and selector it wraps,
it holds a file-scope variable initialized at load time by `objc_lookUpClass()` /
`sel_registerName()`. The macros are the ODR switch deciding whether a header **declares** those
(`extern`) or **defines** them:

```cpp
#if defined(NS_PRIVATE_IMPLEMENTATION)
#define _NS_PRIVATE_DEF_CLS(symbol) void* s_k##symbol _NS_PRIVATE_VISIBILITY = _NS_PRIVATE_OBJC_LOOKUP_CLASS(symbol)
#define _NS_PRIVATE_DEF_SEL(accessor, symbol) SEL s_k##accessor _NS_PRIVATE_VISIBILITY = sel_registerName(symbol)
#else
#define _NS_PRIVATE_DEF_CLS(symbol) extern void* s_k##symbol
#define _NS_PRIVATE_DEF_SEL(accessor, symbol) extern SEL s_k##accessor
#endif
```

Non-`inline` namespace-scope variables with external linkage — **exactly one definition per
program.** Plain ODR, no magic.

> Apple, verbatim: *"Don't define the NS, MTL, or CA `_PRIVATE_IMPLEMENTATION` macros more than
> once."*

### The canonical implementation TU

```cpp
// metal_cpp_impl.cpp — the ONLY file that may define these. Nothing else in it.
#define NS_PRIVATE_IMPLEMENTATION
#define CA_PRIVATE_IMPLEMENTATION
#define MTL_PRIVATE_IMPLEMENTATION
#define MTLFX_PRIVATE_IMPLEMENTATION      // needed if you use MetalFX; absent from Apple's snippet
#include <Foundation/Foundation.hpp>
#include <Metal/Metal.hpp>
#include <QuartzCore/QuartzCore.hpp>
#include <MetalFX/MetalFX.hpp>
```

Never `#include` this file from another, and **watch unity/jumbo builds** — merging it with a
second copy is how you get duplicate symbols in a project that was fine yesterday.

### Reading the three link errors

Each failure mode has a distinct signature. This table is the fastest debugging tool here:

| Error | Symbols look like | Cause |
| --- | --- | --- |
| **undefined symbols** | `NS::Private::Class::s_kNSString`, `MTL::Private::Selector::s_k…` | **Zero** TUs define the macros |
| **duplicate symbols** | the same `…::Private::…` names, in two `.o` files | **Two** TUs define them |
| **undefined symbols** | `_MTLBinaryArchiveDomain`, `_MTLCommandBufferEncoderInfoErrorKey`, referenced from `__cxx_global_var_init` | Missing `-framework Metal` |

`Private::` in an *undefined* error = you forgot the implementation TU. The same names in a
*duplicate* error = you have two. `_MTL*` C constants referenced from `__cxx_global_var_init` =
a framework isn't linked.

### The build command that works

```bash
clang++ -std=c++17 -I metal-cpp \
  -framework Foundation -framework Metal -framework QuartzCore -framework MetalFX \
  metal_cpp_impl.cpp main.cpp -o demo
```

Verified end to end: creates the device, allocates a 1024-float shared buffer, compiles an MSL
kernel from a runtime source string, `dispatchThreads`, waits, reads back. No Objective-C anywhere.

### Single-header option

```bash
./SingleHeader/MakeSingleHeader.py Foundation/Foundation.hpp QuartzCore/QuartzCore.hpp \
    Metal/Metal.hpp MetalFX/MetalFX.hpp
```

Produces a **1.3 MB** `SingleHeader/Metal.hpp`. Works; compiled and ran. On Python 3.12+ it emits a
harmless `SyntaxWarning: "\s" is an invalid escape sequence`.

`METALCPP_SYMBOL_VISIBILITY_HIDDEN` hides metal-cpp's symbols — worth defining if you ship
metal-cpp inside a plugin or dylib whose host might also use it.

---

## 3. Mixing with Objective-C++

A `.mm` file can include `<Metal/Metal.h>` and `<Metal/Metal.hpp>` **simultaneously** — verified,
with and without ARC. The headers branch on `__OBJC__` internally.

**A `MTL::Device*` and an `id<MTLDevice>` are the same pointer value.** Confirmed:
`(__bridge void*)objc == (void*)pCpp` → `1`.

```objc
id<MTLDevice> toObjC(MTL::Device* p) { return (__bridge id<MTLDevice>)p; }
MTL::Device*  toCpp(id<MTLDevice> d) { return (__bridge MTL::Device*)d; }
```

**The gotcha:** under `-fobjc-arc` a plain `(void*)objc` cast is a hard **error**, not a warning:

```
error: cast of Objective-C pointer type 'id<MTLDevice>' to C pointer type 'void *' requires a bridged cast
```

Under `-fno-objc-arc` the identical line compiles silently. The same interop file behaves
differently depending on that one flag.

| Cast | Purpose | Ownership |
| --- | --- | --- |
| `__bridge` | plain type change | none |
| `__bridge_retained` | ObjC → C++, out of ARC | ARC → MRR |
| `__bridge_transfer` | C++ → ObjC, into ARC | MRR → ARC |

**metal-cpp is MRR; your Objective-C is probably ARC.** `__bridge` moves no ownership — pick the
retained/transfer forms when the owner changes side.

---

## 4. Naming translation

Six namespaces, not the three most write-ups mention: `NS::` (a *subset* of Foundation), `MTL::`,
**`MTL4::`** (Metal 4 lives in its own namespace), `CA::` (only `CAMetalLayer`/`CAMetalDrawable`),
`MTLFX::`, `MTL4FX::`.

Rules (Apple states the principle — *"the only differences are the name conventions"* — but
publishes no algorithm; these are read off real declarations):

1. **Class:** strip the framework prefix. `MTLDevice` → `MTL::Device`.
2. **Method:** take the selector's first keyword, **drop the `With…:`/`For…:` clause and every
   later keyword**; arguments become positional in selector order.
3. `[obj foo]` → `obj->foo()`; `[obj setFoo:x]` → `obj->setFoo(x)`.
4. **Overloads replace selector families** — which is why literals sometimes need explicit casts,
   e.g. `pEnc->drawPrimitives(MTL::PrimitiveTypeTriangle, NS::UInteger(0), NS::UInteger(3))`.

| Objective-C | metal-cpp |
| --- | --- |
| `MTLCreateSystemDefaultDevice()` | `MTL::CreateSystemDefaultDevice()` |
| `[device newBufferWithLength:l options:o]` | `device->newBuffer(l, o)` |
| `[device newBufferWithBytes:p length:l options:o]` | `device->newBuffer(p, l, o)` |
| `[device newLibraryWithSource:s options:o error:&e]` | `device->newLibrary(s, o, &e)` |
| `[device newComputePipelineStateWithFunction:f error:&e]` | `device->newComputePipelineState(f, &e)` |
| `[device supportsFamily:MTLGPUFamilyApple7]` | `device->supportsFamily(MTL::GPUFamilyApple7)` |
| `[enc setBuffer:b offset:0 atIndex:0]` | `enc->setBuffer(b, 0, 0)` |
| `[enc dispatchThreads:g threadsPerThreadgroup:t]` | `enc->dispatchThreads(g, t)` |
| `[[MTLSamplerDescriptor alloc] init]` | `MTL::SamplerDescriptor::alloc()->init()` |
| `[NSString stringWithCString:s encoding:e]` | `NS::String::string(s, e)` |

**Enums are `enum`, not `enum class`, and the cases are NOT re-scoped into the type:**

```cpp
_MTL_ENUM(NS::UInteger, StorageMode) {
    StorageModeShared = 0, StorageModeManaged = 1, StorageModePrivate = 2, StorageModeMemoryless = 3,
};
```

So `MTLStorageModeShared` → **`MTL::StorageModeShared`**, *not* `MTL::StorageMode::Shared`. Values
are identical to the Obj-C ones and safe to cast between.

### Blocks and completion handlers

Every handler has **two overloads** — the raw block and an `std::function` wrapper:

```cpp
using NewLibraryCompletionHandler         = void (^)(MTL::Library*, NS::Error*);
using NewLibraryCompletionHandlerFunction = std::function<void(MTL::Library*, NS::Error*)>;
```

A C++ lambda binds to the `std::function` overload. Verified working in plain `.cpp`:

```cpp
pCmd->addCompletedHandler([](MTL::CommandBuffer* c){
    printf("status=%d\n", (int)c->status());
});
```

---

## 5. Memory — no ARC, and the compiler won't save you

### Apple's four rules

> 1. *You own any object returned by methods whose name begins with* `alloc`, `new`, `copy`,
>    `mutableCopy`, *or* `Create`. Returned with `retainCount == 1`.
> 2. *You can take ownership of an object by calling its* `retain()` *method.*
> 3. *When you no longer need it, you must relinquish ownership* — `release()` or `autorelease()`.
> 4. *You must not relinquish ownership of an object you do not own.*

And the complement people forget:

> *"If you create an object with a method that does not begin with `alloc`, `new`, `copy`,
> `mutableCopy`, or `Create`, the creating method adds the object to an autorelease pool."*

**The name test is the whole game:**

| Yours (+1, must release) | The pool's (do not release) |
| --- | --- |
| `MTL::CreateSystemDefaultDevice()` | `queue->commandBuffer()` |
| `MTL::SamplerDescriptor::alloc()->init()` | `cmd->computeCommandEncoder()` |
| `device->newBuffer(...)`, `newCommandQueue()` | `layer->nextDrawable()` |
| `device->newLibrary/newFunction/newComputePipelineState` | `NS::String::string(...)`, `device->name()` |
| `NS::AutoreleasePool::alloc()->init()` | `CA::MetalLayer::layer()` |

`delete` is a **compile error** — `NS::Object`'s destructor is deleted. Good: the naive C++ mistake
is caught. It does **not** catch the leak.

### `NS::AutoreleasePool`

> *"When you create an autoreleased object and there is no enclosing `AutoreleasePool`, the object
> is leaked."*

A pure C++ program has no RunLoop draining anything, and `commandBuffer()`,
`computeCommandEncoder()`, `nextDrawable()`, `currentRenderPassDescriptor()` are *all*
autoreleased. So a render/compute loop **needs a per-iteration pool** or every frame accumulates
until the process dies:

```cpp
while (running) {
    NS::AutoreleasePool* pPool = NS::AutoreleasePool::alloc()->init();
    // ... one frame ...
    pPool->release();
}
```

Debugging levers Apple names: `OBJC_DEBUG_MISSING_POOLS=YES` (warns on an autoreleased object with
no pool), `leaks --autoreleasePools`, `NS::AutoreleasePool::showPools()`, and `NSZombieEnabled=YES`
for use-after-free.

### `NS::SharedPtr<T>` — and which factory

There is **no raw-pointer constructor**, deliberately: a bare pointer doesn't say whether to retain
or transfer.

```cpp
NS::SharedPtr<T> NS::TransferPtr(T*);   // takes your +1. Does NOT retain. Does not remove from a pool.
NS::SharedPtr<T> NS::RetainPtr(T*);     // adds +1. Removes the object from its AutoreleasePool.
```

- **`TransferPtr`** — wrap anything from `alloc` / `new*` / `Create*`. **The common case.**
- **`RetainPtr`** — wrap something you *don't* own (autoreleased, or someone else's) that must
  outlive the current pool.

Getting it backwards fails symmetrically and fatally: `RetainPtr` on a `new*` result → **leak**
(refcount 2, one release). `TransferPtr` on an autoreleased object → **over-release** (the pool
releases it too). Verified: `NS::RetainPtr(pBuf)` on a refcount-1 buffer → `retainCount() == 2`.

The destructor calls `release()` **unconditionally, with no null check** — safe only because
`objc_msgSend` nil-checks (§6).

> ⚠️ **Apple's own README ships an example that does not compile.** Verbatim from the README:
> ```cpp
> NS::SharedPtr< MTL::SamplerState > pSamplerState( pDevice->newSamplerState( pSamplerDescriptor ) );
> ```
> ```
> error: no matching constructor for initialization of 'NS::SharedPtr<MTL::SamplerState>'
> ```
> The correct line is `NS::TransferPtr( pDevice->newSamplerState( pSamplerDescriptor ) )`. The
> README's *other* examples use `TransferPtr` correctly, so it's a one-line slip — but copy-pasting
> the README is the first thing anyone does.

### The classic failures

**Leak — no pool at all.** Pure-C++ `main()` with no pool. Silent, unbounded.

**Leak — the forgotten descriptor.** Descriptors are `alloc()->init()` = +1 and are **not** consumed
by the method that takes them:

```cpp
MTL::SamplerDescriptor* pDesc = MTL::SamplerDescriptor::alloc()->init();  // +1
MTL::SamplerState* pState = pDevice->newSamplerState(pDesc);              // +1
// forgot pDesc->release();  ← leaks every time through
```

**Over-release — releasing an autoreleased object.** `queue->commandBuffer()` isn't `new`, so it's
the pool's. `pCmd->release()` zeroes it early; the pool then releases a dead object. **The crash
lands in a different frame than the bug.**

**Over-release — double-wrapping.** Apple warns on `get()`: *"Avoid wrapping the returned value
again, as it may lead double frees unless this object becomes detached."*

---

## 6. Gotchas

1. **There are no availability annotations. None.** Grepping every header for `API_AVAILABLE` /
   `available(` returns **zero hits**. The macOS 27 header is textually identical in shape to the
   macOS 15 one. Calling a macOS 27 API on a macOS 15 machine gives **no compile warning and no
   link error** — just a runtime `unrecognized selector sent to instance`. In Swift or Obj-C the
   compiler would have stopped you. **Deployment-target gating is entirely your problem.**

2. **The one exception is the `supports…()` family**, which routes through `sendMessageSafe` and
   silently returns `_Ret(0)` — i.e. `false`/`0`/`nullptr` — when the selector is missing. So an
   unsupported *capability check* degrades quietly rather than crashing; nothing else does.

3. **Deprecations *are* expressed**, as real `[[deprecated(...)]]` attributes. So you get warnings
   for old APIs but nothing for new ones. Backwards from what you'd expect.

4. **Metal errors never become C++ exceptions.** Allocation failure returns `nullptr`, no throw.
   A Metal validation failure **`abort()`s and is uncatchable** — verified: double-committing a
   command buffer inside `try { } catch (...) { }` built with `-fexceptions` exits **134**
   (SIGABRT) and the catch never runs. Error handling is `NS::Error**` out-params and `nullptr`
   returns. Check both, always.

5. **Calling methods on `nullptr` is safe but formally UB.** Apple: *"it is legal to call any
   method, including `retain()` and `release()`, on `nullptr` objects."* It works because the call
   inlines to `objc_msgSend`, which nil-checks. Apple annotates `SharedPtr`'s destructor and
   assignments `__attribute__((no_sanitize("undefined")))` for exactly this — **so expect UBSan
   noise from null `NS::Object*` calls anywhere else.** And per Apple's own warning: not crashing
   is no evidence the object is valid.

6. **`MTLSTR(...)` only works on string literals** — it's `__builtin___CFStringMakeConstantString`,
   no allocation, immortal. Runtime strings need `NS::String::string(s, NS::UTF8StringEncoding)`,
   which is **autoreleased**. Encoding constants live in `NS::`, not on the type. A non-ASCII byte
   under `NS::ASCIIStringEncoding` yields `nullptr`, not an error.

7. **`retainCount()` on strings is useless** — measured `18446744073709551615` (`UINT64_MAX`) for
   both `MTLSTR` and `NS::String::string`. Immortal/tagged objects. Don't debug with it.

8. **`MTL::Size` / `MTL::Region` are packed structs passed by value** (`sizeof(Size)==24`,
   `Region==48`), layout-identical to their Obj-C twins. `Region` has three constructors
   distinguished **only by arity** — `Region(x, y, w, h)` is 2D, not 3D-with-defaults. Prefer
   `Make2D`/`Make3D`.

9. **`NS::Array` / `NS::Dictionary` have no C++ construction path** — Apple says to use
   `CFArrayCreate` etc. Note `Create` → +1 → you release it. Bites in ray-tracing and
   argument-buffer code specifically.

10. **What's not covered:** no AppKit, UIKit, MetalKit, ModelIO, AVFoundation, CoreGraphics.
    `QuartzCore/` is *only* `CAMetalLayer` + `CAMetalDrawable`. `Foundation/` is a subset.

11. **`metal-cpp-extensions` (MTK::View, NS::Application) ships only inside `LearnMetalCPP.zip`**,
    never standalone — eleven headers, just enough to open a window. Verified: the 2022-vintage
    extensions still compile against current macOS 27 metal-cpp, so "clone metal-cpp fresh + lift
    `metal-cpp-extensions/` out of the old zip" works. **Do not use the zip's bundled metal-cpp** —
    it's macOS 12 vintage with no `NS::SharedPtr`, no MetalFX, no MTL4.
    Trap: MetalKit uses `MTK_PRIVATE_IMPLEMENTATION`, but **AppKit piggybacks on
    `NS_PRIVATE_IMPLEMENTATION`** — so `AppKit.hpp` must be included in that same TU.

12. **Metal 4 is fully covered**, in `MTL4::`. Entry points hang off the same `MTL::Device`, with a
    naming collision Apple had to resolve: `newCommandQueue()` returns a classic
    `MTL::CommandQueue*`, while the Metal 4 one is `newMTL4CommandQueue()`.
