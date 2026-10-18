# Distributed joins with Bloom filters

Python starter project for Eugene Gu and Lance Tapang's distributed database proposal.
The goal is to compare full remote-table transfer, a fixed-size Bloom filter (10 bits
per key), and a filter size selected using the paper's transfer-cost model.

## Run

Requires Python 3.10 or newer. Uses only the Python standard library; no packages
or database server need to be installed. From this repository:

```sh
python -m bloomjoin --rows 1000 --overlap 0.1 --payload-bytes 32 --seed 42
python -m unittest discover -s tests -v
```

The first command creates/replaces `data/local.sqlite` and `data/remote.sqlite`
and writes `results/baseline.json`. Use `--data-dir` and `--output` for separate runs.
Both generated folders are ignored by Git. Do not point `--data-dir` at existing
research data: generation replaces the `records` tables.

## What works

- Seeded synthetic data with unique integer keys and ASCII payloads of the requested byte size.
- One SQLite database per site; a separate spawned process reads the remote database.
- Full remote-table transfer over a loopback TCP socket, in batches of 1,000 rows.
- A temporary table and exact SQL join at the local site.
- Automatic comparison of the complete ordered result with a reference SQL join.
- JSON metrics: framed application bytes in both directions, query time,
  transferred and nonmatching record counts, and filter build time (zero for baseline).

Query timing begins before the configuration request and ends after the final join.
It includes serialization, remote reading, transfer, and temporary-table loading.
It excludes data generation, process startup/connection, and reference validation.
Count bytes at the local endpoint only; TCP/IP overhead is outside this metric.
Loopback timing does not represent a real geographically distributed network.
The current runner holds the join result in memory; begin with small datasets.

## Layout

- `bloomjoin/data.py`: synthetic SQLite databases
- `bloomjoin/protocol.py`: framed JSON messages and byte counting
- `bloomjoin/worker.py`: remote database process
- `bloomjoin/experiment.py`: full-transfer run, metrics, exact reference check
- `bloomjoin/strategies.py`: explicit unimplemented Bloom and sizing interfaces
- `tests/`: baseline correctness and generation checks

## Next work

Bloom filtering and the cost strategy's transfer integration remain unimplemented.
The pure sizing function is implemented and tested; see
[the model and integration notes](docs/cost-sizing.md) for the Section 4.1 equation,
selectivity assumption, units, rounding, limits, and proposed metadata contract.
No optimized distributed results are claimed.

To measure the sizing metadata exchange and record a proposed filter size:

```sh
python -m bloomjoin --rows 100 --collect-sizing --output results/sizing-diagnostic.json
```

This still runs full transfer. The optional `sizing` metrics record remote JSON
row width, counts, proposed bits/hashes, and metadata bytes. Metadata exchange
and scanning are included in query time; metadata bytes are already included
in total application bytes. The default run does not request these statistics.
Implement the filter and fixed-size strategy, then integrate cost-selected sizing.
Keep the same serializer, result
projection, join destination, byte accounting, and timing boundaries across methods.

Planned experiment values from the proposal: 10,000 / 100,000 / 1,000,000 rows,
0% / 1% / 10% / 50% / 100% remote-key overlap, and 32 / 128 / 512-byte payloads.
Vary one factor around a baseline and repeat runs; large sweeps are future work.

Reference: Ramesh, Papapetrou, and Siberski, *Optimizing Distributed Joins with
Bloom Filters*, ICDCIT 2008, pp. 145-156, DOI: 10.1007/978-3-540-89737-8_15.
Verify Section 4.1 against the paper before implementing the cost-selected strategy.

## Contributor guidance

Read [AGENT.md](AGENT.md) before working on an issue. Agents must keep changes
scoped to the assigned task and update relevant tests as they go. `AGENTS.md`
points to the same rules for agent discovery.

## Benchmark the baseline

```sh
python -m bloomjoin.benchmark --rows 1000 --overlap 0.1 --payload-bytes 32 --seed 42 --repeats 3 --warmups 1 --output results/benchmark.json
```

The harness generates temporary databases once and reuses them for all runs.
Every warmup and measured run must pass exact SQL reference validation. Warmups
are excluded from the report's measured runs and timing summaries. JSON includes
raw measurements, configuration, environment, and mean/median/min/max/sample
standard deviation for query and filter-build times. Benchmark correctness tests
run with the existing unit-test command; they do not enforce timing thresholds.
Only `full` is implemented. Adding other strategies remains assigned student work.
Run larger datasets explicitly; the default is a small local smoke benchmark.
