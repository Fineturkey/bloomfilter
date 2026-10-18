# Rules for coding agents and contributors

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
