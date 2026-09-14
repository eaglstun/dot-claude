# HTTP services and networking

Sources:

- https://pkg.go.dev/net/http
- https://pkg.go.dev/net/http#Server.Shutdown
- https://pkg.go.dev/net#Dialer
- https://go.dev/blog/context

## Servers

Configure an explicit `http.Server`; package-level `ListenAndServe` defaults omit important operational knobs.
Set header/read/write/idle limits based on protocol and workload, cap request bodies where appropriate, and
propagate `r.Context()` into downstream calls. Handlers may run concurrently; shared fields need synchronization.

Middleware should preserve optional interfaces/semantics when wrapping response writers, and should recover only
at a boundary that can safely produce a response. Authenticate before expensive body processing. Keep health/readiness
semantics distinct.

Graceful shutdown stops new connections, waits for active handlers within a deadline, and then lets the process
force termination. Track separately owned background goroutines; server shutdown does not wait for arbitrary work.

## Clients

Reuse `http.Client` and especially `Transport`; they pool connections and are safe for concurrent use. Set an overall
client timeout or request context deadlines, plus transport dial/TLS/response-header limits appropriate to the call.
Always close response bodies. Decide retry policy based on idempotency, replayable bodies, status/error classes and
a total deadline; add backoff/jitter and bounds.

For streaming, an overall timeout may be inappropriate—use context and phase/idle controls. Validate redirects,
proxies and destination policy for SSRF-sensitive callers.

## Gotchas

- The default `http.Client` has no overall timeout.
- Creating a transport per request destroys connection reuse.
- A successful HTTP round trip may return a non-2xx response; transport errors and application status differ.
- `Shutdown` does not close hijacked connections or arbitrary goroutines automatically.
- Writing headers/body after another goroutine has returned from the handler is unsafe.

