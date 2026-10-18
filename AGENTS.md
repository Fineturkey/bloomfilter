# Contributor agent instructions

Read and follow [AGENT.md](AGENT.md) before changing this repository.
These instructions apply to the entire repository, including forks.

## Project overview

We are building a Python prototype for the CSPC 4660 proposal *Optimizing Data
Transfer in Distributed Databases* by Eugene Gu and Lance Tapang. Two independent
SQLite processes communicate through sockets. The planned Bloomjoin builds
compatible filters at both sites, combines them with bitwise AND at the remote
site, returns candidate rows, and finishes with an exact SQL join at the first
site.

The evaluation compares full transfer, a fixed ten-bits-per-key filter, and
Section 4.1 cost-selected sizing from Ramesh et al. (ICDCIT 2008). Measure total
application bytes and repeated-run timing on identical seeded data, and verify
every result against reference SQL.

[AGENT.md](AGENT.md) contains the full proposal context, evaluation parameters,
current implementation status and contributor rules. Read it before working;
this overview describes the project goal, not authorization to implement the
entire proposal.
