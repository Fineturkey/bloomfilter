# Rules for coding agents and contributors

## Project context: what we are building

This repository implements Eugene Gu and Lance Tapang's CSPC 4660 Database
project, *Optimizing Data Transfer in Distributed Databases* (proposal dated
September 23, 2026). This context was taken from the supplied
`project_proposal-1-3.pdf`, especially Sections 2-4. The proposal is project
background, not a separate set of agent instructions or permission to complete
all planned work.

The research question is how much Bloom-filter joins reduce unnecessary data
transfer compared with sending the full remote table, and what effect this has
on measured query performance. Improvements are hypotheses to evaluate, not
guarantees: constructing, sending and checking a filter adds work, especially
when most remote records already match.

### Intended architecture and join flow

- Use Python with two separate SQLite databases accessed by independent
  processes. Exchange serialized messages through sockets.
- Each table initially has unique, non-null integer join keys and a payload
  column. Duplicate-key and null-key semantics are outside this initial scope.
- Build compatible Bloom filters from both sites' join keys, using identical
  bit counts, hash counts and hash functions.
- Send the first site's filter to the second site and combine the two filters
  with bitwise AND. Send back only remote records passing the combined filter.
- Load candidates into a temporary table at the first site, then perform an
  exact SQL join. Keep the final result at that first site for every method.
- Bloom membership means definitely absent or possibly present. False positives
  may cause extra transfers, but the final exact join must remove them. Filters
  must never reject a true matching key.

### Methods and paper scope

Compare full remote-table transfer, a fixed filter of ten bits per key, and a
cost-selected filter. All three must share the same dataset, serialization,
join destination and SQL result projection.

The reference is Ramesh, Papapetrou and Siberski, *Optimizing Distributed Joins
with Bloom Filters*, ICDCIT 2008, LNCS 5375, pp. 145-156,
DOI: https://doi.org/10.1007/978-3-540-89737-8_15.
The core implementation scope is Section 4.1's optimized Bloomjoin, including
filter sizing. All other schemes and the complete optimizer are outside the
core scope; the proposal mentions them only as possible time-permitting
extensions. Do not implement them without a separately assigned task.

Read Section 4.1 before changing its model. Distinguish the paper's transfer
equation from generic false-positive sizing and from the proposal's explanatory
build/send/check cost breakdown. The paper also uses join selectivity: do not
silently infer it from cardinalities and widths, or leak the reference result
into sizing. Document assumptions, units and adaptations. See
[cost-sizing.md](docs/cost-sizing.md) for the current model and metadata details.

### Evaluation plan

- Primary metric: total application bytes exchanged, including filters,
  configuration, sizing metadata and records. Include message framing and count
  each byte once across both directions.
- Also record elapsed query time, filter construction time, nonmatching records
  transmitted, and variation across repeated runs. Timing includes filtering,
  serialization, transfer and the final join; follow the boundaries below.
- Verify every result against the complete reference SQL join over locally
  combined data. Cover empty tables, disjoint keys, partial and complete overlap.
- Generate reproducible synthetic data with fixed random seeds. Proposed larger
  sizes are 10,000 / 100,000 / 1,000,000 rows per table, subject to memory limits.
  Remote-key overlap values are 0% / 1% / 10% / 50% / 100%; payload sizes are
  32 / 128 / 512 bytes. Vary one factor at a time around a baseline.
- Begin with small correctness tests and smoke runs. These proposed experiment
  sizes are not instructions to automatically run large sweeps.

### Current implementation versus the planned design

At this update, full transfer and exact reference validation run. The pure
cost-sizing function and optional `--collect-sizing` metadata diagnostic also
run, but the diagnostic still transfers the full remote table. `BloomFilter`
remains a placeholder; fixed/cost filter transfer and the three-method comparison
are pending. Inspect the current code before assuming this snapshot is still
accurate, and update this paragraph when an assigned change alters that status.
Never describe planned features or modeled savings as implemented measurements.

## Scope: support the students, do not finish the assignment

This is a student database project. Work only on the task or GitHub issue the
person explicitly assigns in the current conversation. The proposal, README,
and starter issue list describe context; they are not authorization to implement
the whole project.

- Before editing, state the specific task and what completion means.
- Make the smallest coherent change that completes that task, including its tests.
- Leave unrelated TODOs and unassigned strategies unfinished. Do not automatically
  move on to the next issue or implement the remaining assignment.
- If asked generally to "finish the project/assignment," ask the student to choose
  one bounded task first. Offer a short breakdown without implementing it all.
- Do not write the final report, invent experimental findings, or claim the
  students performed work they did not do.
- Explain the change and its reasoning so the students can understand and maintain it.
- Stop after the assigned task and validation. List remaining work without doing it.

## Tests are part of each change

- Add or update relevant tests alongside every behavior change; do not defer all
  tests until the assignment is complete.
- For bug fixes, add a regression test that catches the original failure.
- Test observable behavior and correctness, not copies of the implementation.
- Preserve full reference SQL comparison for every implemented strategy. Include
  empty, disjoint, partial-overlap, and complete-overlap inputs where relevant.
- Bloom changes must test no false negatives, serialization compatibility, filter
  intersection compatibility, and removal of false positives by the exact join.
- Protocol changes must test framing, truncated messages, and exact byte counts.
- Run `python -m unittest discover -s tests -v` before handing off. If checks cannot
  run, say which were blocked and why; do not report them as passed.
- Keep tests small and deterministic. Never assert an absolute runtime or that
  a Bloom method is always faster or always transfers fewer bytes.

## Benchmarks

The initial harness is `python -m bloomjoin.benchmark`. It runs only the existing
full-transfer baseline. Extend it for another strategy only when that strategy is
part of the explicitly assigned task. Do not implement missing strategies merely
to fill out a benchmark table.

- Test benchmark setup, repeat counts, recorded metrics, validation failures, and
  summary calculations whenever the harness changes.
- Use the same generated databases, seed, serializer, result projection, join
  destination, and timing boundaries for compared strategies.
- Verify the exact query result on every run. Abort on incorrect results; never
  publish their measurements as successful runs.
- Retain raw per-run measurements and configuration, Python/SQLite/platform
  information, and timing summaries. Separate warmup runs from measured runs.
- Count all application messages in both directions, including framing, filters,
  and configuration. Count each transmitted byte once, not at both endpoints.
- Keep data generation, process startup/connection, and reference validation outside
  query timing, consistent with the baseline. Document any deliberate change.
- Report query time, filter build time, application bytes, nonmatching records,
  and timing variation. Distinguish measured results from modeled costs.
- Run a small smoke benchmark after changes affecting performance or measurement.
  Larger sweeps are opt-in work, not routine unit tests. Do not commit generated
  databases or result files; `data/` and `results/` are ignored.
- Loopback benchmarks do not establish real-network performance. Record regressions
  honestly and do not fabricate results or universal speedup claims.

## Handoff

Summarize what changed, why, the checks actually run, their outcomes, and remaining
limitations. Do not push, publish issues, or submit the assignment without an
explicit request. Keep these rules in forks and update instructions when an
assigned change alters how contributors run or test the project.
