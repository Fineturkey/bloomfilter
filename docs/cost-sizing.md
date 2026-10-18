# Cost sizing: model stage

Source: Ramesh, Papapetrou and Siberski,
[Optimizing Distributed Joins with Bloom Filters](https://opapapetrou.win.tue.nl/papers/icdcit08-djoins.pdf),
Section 4.1, equations (1)-(4), PDF pages 4-5.

## Paper equation

With equal table cardinalities `r`, selectivity `a`, filter length `m` bits,
remote row width `w2 = len(key) + rowlen(T2)` bits, and joined result width
`wj = len(key) + rowlen(T1) + rowlen(T2)` bits:

```
C(m) = m + [r*a + r*(1-a)*exp(-m*ln(2)^2/r)]*w2 + r*a*wj
m* = r/ln(2)^2 * ln((1-a)*ln(2)^2*w2)
k* = m/r * ln(2)
```

Cost is transferred bits, not CPU time. The approximation assumes optimal real
hash count and uniform independent hashes. The last term transfers the exact
result to the user; it is independent of `m`. The paper assumes database
statistics are available. It does not specify integer rounding or memory caps.

## Implementation decisions

`choose_filter_size(n, R, record_width, *, selectivity=0.0)` returns a named
tuple `(bit_count, hash_count)`. Width is **bytes**, converted to bits internally.
Counts represent unique non-null integer keys, as in the current schema.
Unequal counts use this adaptation of the size-dependent cost:

```
C(m) = m + [R*a + R*(1-a)*exp(-m*ln(2)^2/n)]*8*record_width
m* = n/ln(2)^2 * ln((R/n)*(1-a)*ln(2)^2*8*record_width)
```

The result stays at the local site, so the paper's final user-transfer term is
omitted. The three positional arguments cannot identify selectivity: the default
`a=0` is a conservative nonmatch estimate, not knowledge of actual overlap or the
paper's full statistics-based optimizer. An optional estimate makes this explicit.
Do not obtain that estimate from the reference join or silently use generated
ground truth. The experiment's overlap setting is not remotely available metadata.

Clamp a nonpositive continuous optimum to the no-filter sentinel `(0, 0)`;
empty tables also return that sentinel and should short-circuit the join. At
selectivity one, bypass the filter. Otherwise round bits upward to a whole byte
(at least eight bits), cap at 8 MiB of packed storage, and round `k*` to the
nearest integer with halves upward, clamping to 1..32. These are engineering
choices: rounding and caps mean this is not an exact integer optimum. No candidate
search or bit array is allocated; work uses a constant number of scalar/log
operations. Invalid counts, nonfinite numbers, nonpositive width, booleans and
out-of-range selectivity raise `ValueError`, including on empty input.

## JSON sizing and metadata contract for integration

Proposed width estimate: stream every remote row through exactly the channel's
compact `json.dumps(row, separators=(",", ":")).encode("utf-8")` serializer;
accumulate length plus one byte for its batch separator, divide by row count.
This includes key digits, quoting, escaping and UTF-8 encoding, unlike SQLite's
storage width or the synthetic payload length. For an empty table use zero row
count and short-circuit before calling the function with a width. Stream the
scan rather than retaining the entire table. This is a full scan estimate of
mean row contribution, not an exact prediction of batch/message overhead.

During query timing, the local site should request sizing metadata and the
remote site should reply with row count and estimated mean row bytes. Count
both messages and their four-byte framing through the existing `Channel` at
the local endpoint. Count any exchanged selectivity statistics too. Local
cardinality comes from local SQL. Include metadata scan/serialization in query
time. Keep actual application bytes separate from this raw-bit model: JSON
filter encoding, batch envelopes, control messages and framing add bytes.
Choose filter serialization jointly with Issue 1 before claiming wire optimality.

## Remaining issue work

Issue 1's `BloomFilter` and shared filter/transfer path are still unimplemented.
This change does not add a runnable `cost` strategy, metadata messages, or a
three-method comparison command. Once that path exists, integrate both fixed
and cost sizing through it; preserve exact SQL verification and count all
messages. Extend the existing benchmark to generate one dataset for all three
methods, retain raw verified runs and per-method summaries, and expose the
existing data controls plus repeat count. Start with small inputs.
