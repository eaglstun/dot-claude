---
topic_id: "v2:NCGC"
topic_path: "apple-accelerate/vector-math"
semantic_id: "tk7RAPZ_0drq5HO2TqSR8X5bnxZEcAAD"
related_ids:
  - "2m9Jg7YZA5rQauuEzrQdN34HGhXEgAAF"
  - "_-bsBuV9l9rySMOYA7aN4ChjXm7U8AAI"
---
# Quadrature — numerical definite integration

Source:

- <https://developer.apple.com/documentation/accelerate/quadrature>
- <https://developer.apple.com/documentation/accelerate/working_with_the_quadrature_functions>

Quadrature numerically integrates a function `f(x)` over an interval `[a, b]` — the
`∫f dx` you can't (or won't) do symbolically. Small, self-contained corner of Accelerate;
one integrator, driven by a C callback.

## The shape of it

```c
quadrature_integrate_function fun;
fun.fun = my_integrand;      // void my_integrand(void *arg, size_t n, const double *x, double *y)
fun.fun_arg = &params;       // opaque context passed back to your callback

quadrature_integrate_options options = {0};
options.integrator   = QUADRATURE_INTEGRATE_QAGS;  // adaptive, general purpose
options.abs_tolerance = 1.0e-8;
options.rel_tolerance = 1.0e-8;
options.max_intervals = 200;

quadrature_status status;
double abs_error;
double result = quadrature_integrate(&fun, a, b, &options, &status, &abs_error, 0, NULL);
```

Key points:

- **Vectorized callback.** Your integrand is called with an **array** of sample points `x[0..n]`
  and must fill `y[0..n]` — so you can (and should) vectorize it with vDSP/vForce rather than
  compute one point per call. `n` is chosen by the integrator.
- **`fun_arg`** carries your parameters (opaque `void*`) into the callback — the standard
  C-closure workaround; no capturing closures in the C API.
- **Integrators** (`options.integrator`): `QUADRATURE_INTEGRATE_QNG` (fast, non-adaptive,
  smooth functions), `QUADRATURE_INTEGRATE_QAGS` (adaptive with singularity handling — the
  general default), `QUADRATURE_INTEGRATE_QAG` (adaptive, no singularity handling). These
  mirror the classic QUADPACK routines.
- **Tolerances & status:** you set `abs_tolerance`/`rel_tolerance`; you get back the estimated
  `abs_error` and a `quadrature_status` (check it — `QUADRATURE_SUCCESS` vs error/warning codes).

## Gotchas

- **The callback is batched — fill the whole `y` array.** It's `y[i] = f(x[i])` for all `i in
0..<n`, not a single point. Filling only `y[0]` returns nonsense. This is the #1 mistake.
- **Check `quadrature_status`.** A returned `result` on a non-success status (didn't converge,
  hit `max_intervals`, roundoff-limited) is not trustworthy. Don't just read the return value.
- **Match the integrator to the integrand.** `QNG` on a function with a singularity or sharp
  peak silently under-resolves; use `QAGS`. `QAGS` on a smooth polynomial wastes work vs `QNG`.
- **Pass parameters via `fun_arg`, not globals.** The C callback can't capture; stuff state in
  `fun_arg` and cast it back. Globals break reentrancy/threading.
- **Improper integrals need care.** Infinite limits or strong singularities may need variable
  substitution before handing to the integrator; there's no magic `∞` limit here.

### See also

- [[vforce-and-veclib]] / [[vdsp-signal-processing]] — vectorize the integrand callback with
  these so the batched `x → y` step is fast.
