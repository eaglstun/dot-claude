# Data, encoding, and databases

Sources:

- https://pkg.go.dev/encoding/json
- https://pkg.go.dev/io
- https://pkg.go.dev/time
- https://pkg.go.dev/database/sql
- https://go.dev/doc/database/manage-connections
- https://go.dev/doc/database/execute-transactions

## Encoding boundaries

JSON exported fields and tags form an API. Decide unknown-field policy, absent vs null vs zero semantics, number
precision, and time format explicitly. For strict request decoding, consider `DisallowUnknownFields`, reject trailing
values, cap input, and return field-safe errors. `omitempty` is not “omit every semantic zero” for all types/versions;
test the wire shape.

Stream large data with `io.Reader`/`Writer`, decoder/encoder or buffered iteration rather than `ReadAll`. Respect short
writes and propagate flush/close errors. Treat time zones and monotonic components deliberately; serialize explicit
instants/formats and inject clocks where behavior depends on now.

## database/sql

`*sql.DB` is a concurrent connection pool, not one connection. Open once, configure pool limits/lifetimes from
database and workload capacity, and `PingContext` when startup readiness requires it. Always pass context.

Transactions use `BeginTx`, operations on the returned `Tx`, then commit or rollback. Never mix `DB` operations into
logic that must be atomic. A deferred rollback is safe after a successful commit. Check commit errors.

Iterate rows, scan, close, then check `rows.Err`. Use nullable types/pointers according to domain semantics. Parameterize
values; identifiers/order clauses require allowlisting rather than placeholders.

## Gotchas

- `sql.DB` can be non-nil before any connection succeeds.
- Forgetting to close rows or response bodies starves pools.
- JSON numbers decoded into `any` become `float64` unless configured otherwise.
- `time.Time` equality can include location/monotonic details; compare with intended semantics.
- Retrying a transaction requires rerunning the whole transaction function, not only commit.

