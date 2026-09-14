---
semantic_id: "bR3iBSDJo6iY44yOrpON1W5vz383EAAE"
related_ids:
  - "YZjGBCDZwwy4_Yiw5KGLU09_4l43UAAO"
  - "bYXMHKZFq6AaysiC7pER1W_P_L93wAAK"
---
# Parsing and streaming

Source:

- https://hackage.haskell.org/package/megaparsec
- https://hackage.haskell.org/package/attoparsec
- https://hackage.haskell.org/package/conduit
- https://hackage.haskell.org/package/streamly
- https://hackage.haskell.org/package/resourcet

## 1. Which parser

| Library        | Best for                                 | Errors        | Backtracking                      |
| -------------- | ---------------------------------------- | ------------- | --------------------------------- |
| `megaparsec`   | languages, config, anything human-facing | **excellent** | explicit `try`                    |
| `attoparsec`   | network protocols, fast binary/text      | minimal       | explicit `try`, incremental input |
| `parsec`       | legacy; megaparsec is the successor      | ok            | explicit `try`                    |
| `flatparse`    | maximum speed, ByteString                | manual        | manual                            |
| `alex`+`happy` | large grammars with a real lexer/LALR    | manual        | n/a                               |
| `earley`       | ambiguous grammars                       | ok            | full                              |

Default to **megaparsec** unless throughput is the requirement, in which case
**attoparsec** (which also supports incremental feeding, essential for sockets).

## 2. megaparsec shape

```haskell
import Text.Megaparsec
import Text.Megaparsec.Char
import qualified Text.Megaparsec.Char.Lexer as L
import Data.Void (Void)

type Parser = Parsec Void Text          -- error type, input type

sc :: Parser ()
sc = L.space space1 (L.skipLineComment "--") (L.skipBlockComment "{-" "-}")

lexeme :: Parser a -> Parser a
lexeme = L.lexeme sc

symbol :: Text -> Parser Text
symbol = L.symbol sc

pInt :: Parser Int
pInt = lexeme L.decimal

pList :: Parser [Int]
pList = between (symbol "[") (symbol "]") (pInt `sepBy` symbol ",")

run :: Text -> Either String [Int]
run = first errorBundlePretty . parse (sc *> pList <* eof) "<input>"
```

Points that matter:

- **`eof`** at the end, or your parser happily succeeds on a prefix.
- The **lexeme convention**: every token parser consumes _trailing_ whitespace,
  and the top-level parser consumes leading whitespace once. Mixing conventions
  produces parsers that work until they don't.
- **`errorBundlePretty`** renders the caret-and-line-number output that makes
  megaparsec worth using. Don't `show` the error.
- **`label`/`<?>`** names an expectation and improves the message a lot.
- **`try`** is needed when an alternative can fail _after consuming input_.
  `a <|> b` only tries `b` if `a` failed **without consuming**. This is the
  number-one source of mysterious parser failures.

```haskell
p = try (string "let" *> ...) <|> (string "letter" *> ...)
```

Combinator vocabulary: `many`, `some`, `optional`, `sepBy`/`sepBy1`,
`endBy`, `sepEndBy`, `between`, `choice`, `manyTill`, `notFollowedBy`,
`lookAhead`, `takeWhileP`/`takeWhile1P` (fast bulk consumption),
`Control.Monad.Combinators.Expr.makeExprParser` for operator precedence.

Indentation-sensitive grammars: `L.indentBlock`, `L.nonIndented`,
`L.lineFold`.

## 3. attoparsec shape

```haskell
import Data.Attoparsec.ByteString.Char8

parseOnly p input           :: Either String a
parse p input               :: Result a        -- Partial | Done | Fail
feed result moreInput
```

`Partial` is why attoparsec is the right choice for streams: you feed it more
bytes as they arrive from the socket and it resumes. Its error messages are
deliberately minimal (that's part of the speed), so it's the wrong tool for a
config file a human must fix.

`takeWhile`/`takeTill`/`scan` operate on whole chunks and are where the
performance comes from — a character-at-a-time attoparsec parser gives up its
advantage.

## 4. Parse, don't validate

The design principle worth stating: a parser's job is to turn an unstructured
input into a **type that makes the invalid states unrepresentable**, once, at
the boundary.

```haskell
-- bad: validate then keep the loose type
validateEmail :: Text -> Bool

-- good: parse into a type that carries the proof
newtype Email = Email Text          -- constructor not exported
parseEmail :: Text -> Either Err Email
```

Everything downstream then takes `Email` and cannot be handed a raw `Text`. The
same logic applies to `NonEmpty` over `[]`, `Natural` over `Int`, and a sum type
over a stringly-typed status.

## 5. Streaming: the problem

Lazy IO (`readFile`, `hGetContents`) gives you streaming but with unpredictable
resource lifetimes — see `io-and-mutable-state.md` §4. Reading a 10 GB file
strictly isn't an option either. Streaming libraries give incremental processing
with deterministic resource handling.

## 6. `conduit`

```haskell
import Conduit

main = runConduitRes $
       sourceFile "in.txt"
    .| decodeUtf8C
    .| linesUnboundedC
    .| filterC (T.isPrefixOf "ERROR")
    .| encodeUtf8C
    .| sinkFile "out.txt"
```

`ConduitT i o m r`: consumes `i`, produces `o`, effects in `m`, returns `r`.
`.|` fuses stages; `runConduit` runs; `runConduitRes` adds `ResourceT` so file
handles close deterministically.

Mature ecosystem: `conduit-extra` (process, network, zlib), `http-conduit`,
`persistent`'s streaming queries, `csv-conduit`, `conduit-aeson`.

## 7. `streamly`, `pipes`, `streaming`

- **`streamly`** — highest performance (fusion down to tight loops), concurrency
  built in (`parMapM`, `asyncly`), broad scope (it wants to be your whole
  concurrency+IO layer). Steeper learning curve, and the API changed
  significantly at 0.9/0.10 — pin the version and read _that_ version's docs.
- **`pipes`** — smallest, most principled core with laws; `pipes-safe` for
  resources. Excellent to learn from; smaller ecosystem than conduit.
- **`streaming`** — `Stream (Of a) m r`, closest to "a list with effects", the
  easiest mental model if you already think in `Traversable`. Pairs with
  `streaming-bytestring`.

All four solve the same problem. **Pick the one your dependencies already use** —
mixing conduit and pipes in a project means adapter code in every direction.

## 8. `ResourceT`

```haskell
runResourceT $ do
  (releaseKey, handle) <- allocate (openFile p ReadMode) hClose
  ...
  release releaseKey                 -- or let runResourceT do it
```

Registers cleanups in a scope that isn't lexically nested, which is exactly what
a streaming pipeline needs. Cleanups run in reverse registration order when the
`runResourceT` block exits, including on exception. Everything must complete
inside the block — returning a lazy value that still needs the handle is the
classic misuse.

## 9. Choosing between "parse it all" and "stream it"

Stream when: input is unbounded or larger than memory, latency to first output
matters, or the source is a socket. Otherwise read strictly and parse — a strict
`ByteString` plus attoparsec is simpler, faster, and easier to test than a
pipeline, and "the file is only 50 MB" is usually true.

## Gotchas

- **`<|>` doesn't backtrack after consuming input.** Wrap the left side in
  `try`, or factor the common prefix out.
- **Forgetting `eof`** makes a parser succeed on a prefix and silently ignore
  the rest of the file.
- **`many` on a parser that can succeed without consuming input loops forever.**
- **megaparsec's `space` consumer must be applied consistently** — pick "lexemes
  eat trailing space" and never deviate.
- **`show`ing a `ParseErrorBundle` gives you an unreadable dump**; use
  `errorBundlePretty`.
- **attoparsec's `parseOnly` on a lazily-read `ByteString`** reintroduces every
  lazy-IO hazard.
- **attoparsec `Partial` results that are never `feed`ed with empty input never
  finish** — you must `feed r ""` to signal EOF.
- **Streaming libraries don't mix.** Adapters exist but every conversion is a
  seam.
- **`runResourceT` closing before a lazy value is forced** produces
  use-after-close errors. Force inside the block.
- **`conduit`'s `sourceFile` without `runConduitRes` leaks the handle** on
  exception.
