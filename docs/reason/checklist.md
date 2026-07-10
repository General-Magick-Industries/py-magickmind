# Cortex v2 Reason — Launch Checklist

Production-readiness reference for launching the Cortex v2 Reason API: target
load and SLOs, the load-testing procedure, per-`api_key` rate limits, monitoring,
and the go/no-go checklist. The rollback procedure lives in
[rollback_plan.md](rollback_plan.md); the wire format is in
[../resources/reason_v2.md](../resources/reason_v2.md).

## Scope

v2 launches as a fully additive surface: one endpoint
(`POST /v2/chat/completions` at the API edge), no presets, no server-side tools,
no stored responses. v1 endpoints are untouched and stay available throughout.
"Launch-ready" means the items in the checklist at the bottom of this page are
all checked, with evidence linked.

## Target Load and SLOs

Proposed targets for the launch sign-off run. Reason latency is dominated by
upstream model providers, so total-latency SLOs are per-scenario and
time-to-first-event (TTFE) is the primary responsiveness signal for streaming.

| Scenario | Sustained RPS (aggregate) | TTFE p95 | Total p95 | Error rate |
|---|---|---|---|---|
| Singular + LLM | 50 | ≤ 2 s | ≤ 15 s | < 0.5% |
| Singular + RLM | 5 | ≤ 3 s | ≤ 90 s | < 0.5% |
| MCTS (LLM nodes) | 10 | ≤ 3 s | ≤ 60 s | < 0.5% |
| MCTS mixed (LLM + RLM) | 5 | ≤ 3 s | ≤ 120 s | < 0.5% |

Notes:

- **Error rate counts 5xx and `reason.failed` terminal events.** 429s are
  excluded — they are the rate limiter working as intended. Degraded-but-
  successful responses (`degradations` non-empty) are tracked separately and
  alarmed at > 5% over 15 minutes.
- Total-latency targets assume the cheap default prompt in the harness and
  bounded `max_tokens`; they exist to catch queueing and orchestration
  regressions, not to bound arbitrary user workloads.
- After the first sign-off run, replace any target this table gets wrong with
  the measured baseline plus headroom, and keep the table updated.

## Load Testing

The harness is `examples/reason_loadtest.py`. It drives the endpoint through
the SDK with `max_retries=0` (so raw 429/5xx are observed rather than retried
away), paces arrivals open-loop at the target RPS, and reports achieved RPS,
p50/p95/p99 latency, TTFE percentiles for streaming runs, an error breakdown,
and total LLM cost for the run.

Every request spends real LLM credits — run against **staging** and keep
`--max-tokens` low (default 32).

Environment setup is the same as `examples/` (see `examples/README.md`):
`MAGICKMIND_API_KEY`, optional `MAGICKMIND_BASE_URL`, and the per-scenario model
variables (`MAGICKMIND_REASON_MODEL`, `MAGICKMIND_REASON_MODEL_A/_B`,
`MAGICKMIND_RLM_MAIN_MODEL`, `MAGICKMIND_RLM_SUB_MODEL`,
`MAGICKMIND_RATING_MODEL`, `MAGICKMIND_AGGREGATOR_MODEL`).

### Sign-off runs

Run each scenario at its target RPS for at least 10 minutes, non-streaming and
streaming:

```bash
python examples/reason_loadtest.py --scenario singular-llm --rps 50 --duration 600
python examples/reason_loadtest.py --scenario singular-llm --rps 50 --duration 600 --stream
python examples/reason_loadtest.py --scenario singular-rlm  --rps 5  --duration 600
python examples/reason_loadtest.py --scenario mcts          --rps 10 --duration 600
python examples/reason_loadtest.py --scenario mcts-mixed    --rps 5  --duration 600 --stream
```

Then two stress runs:

```bash
# Overload: 2x target — expect graceful 429s/queueing, not 5xx
python examples/reason_loadtest.py --scenario singular-llm --rps 100 --duration 300

# Rate-limit verification: a single key driven past its per-key limit
python examples/reason_loadtest.py --scenario singular-llm --rps 5 --duration 120
```

Pass criteria:

- Achieved RPS within 5% of target for every sign-off run.
- Latency/TTFE percentiles and error rate within the SLO table above.
- Overload run produces 429s (or queueing) with **zero** increase in 5xx rate.
- Rate-limit run shows 429s beginning at the configured per-key threshold, with
  the standard error body (see `docs/resources/reason_v2.md`) the SDK surfaces
  as `RateLimitError`.

Save each run's `--json` output alongside the launch checklist as the load
testing report.

The harness also supports a `singular-lambda` scenario for the Lambda RLM node
(`MAGICKMIND_LAMBDA_MAIN_MODEL` / `MAGICKMIND_LAMBDA_SUB_MODEL`). Add it to the
sign-off matrix with its own SLO row once the API edge accepts lambda nodes —
at the time of writing the edge rejects them, so the scenario cannot run end to
end yet.

## Per-api_key Rate Limits

v2 identity is the `api_key` alone, so limits are keyed and enforced
**per-`api_key` at the API edge — never globally** — one noisy tenant must not
be able to starve others. Proposed launch defaults (tune against the measured
load-test baseline before sign-off):

| Limit | Default per api_key | Rationale |
|---|---|---|
| Requests per minute | 60 (token bucket, burst 20) | Generous for interactive use; caps runaway loops |
| Concurrent in-flight requests | 8 | Bounds upstream-provider fan-out; MCTS/RLM multiply LLM calls per request |

Notes:

- RLM cost scales with recursion (and MCTS multiplies it per candidate), so a
  flat request count under-prices heavy algorithms. The concurrency cap is the
  launch-time guard; algorithm- or token-weighted limits are a post-launch
  refinement once real traffic shows the distribution.
- Over-limit requests receive **429** with the standard error body and a
  `Retry-After` header where the limiter can compute one. The error body shape,
  the SDK's retry/backoff behavior, and the streaming retry rule are documented
  in [../resources/reason_v2.md](../resources/reason_v2.md) — that reference is
  the source of truth for wire-level details.
- Verify limits with the rate-limit run above before launch: 429s must appear
  at the configured threshold and disappear when the rate drops back under it.

## Monitoring

Every request emits a hierarchical span tree whose root span carries
`algorithm`, `total_llm_calls`, `total_tokens`, `total_cost_usd`,
`failed_count`, and a `degraded` flag — dashboards and alerts are built on
these attributes plus edge HTTP metrics.

Dashboard panels (per algorithm, with `trace_id` available for drill-down):

- Request rate, error rate (5xx + `reason.failed`), and 429 rate
- Latency p50/p95/p99 and streaming TTFE
- Degraded-response rate (`degraded` flag)
- LLM calls, tokens, and cost per request (catches cost regressions and
  runaway recursion)

Launch alerts:

| Alert | Threshold (proposed) |
|---|---|
| Error rate | > 0.5% over 5 min |
| TTFE p95 | > 2× SLO over 10 min |
| 429 rate | > 10% of requests over 10 min (limits likely mis-tuned) |
| Degraded-response rate | > 5% over 15 min (upstream provider trouble) |
| Cost per request | > 3× scenario baseline over 15 min |

## Launch Checklist

Complete in order; attach evidence (report files, dashboard links, drill log)
next to each item.

- [ ] Wire-format reference (`docs/resources/reason_v2.md`) published and
      validated: a non-implementing engineer built a working v2 client from the
      doc alone, without the SDK or proto.
- [ ] Sign-off load-test runs completed for all four scenarios (streaming and
      non-streaming); reports saved; all SLOs met.
- [ ] Overload run completed: 429s/queueing under 2× load, no 5xx increase.
- [ ] Per-`api_key` rate limits configured at the edge and verified with the
      rate-limit harness run (429 + standard error body + `RateLimitError` in
      SDK).
- [ ] Dashboards live for the panels above; links recorded here.
- [ ] Alerts configured with on-call routing; test-fired once.
- [ ] Rollback plan rehearsed in staging within the 5-minute target; drill log
      recorded in [rollback_plan.md](rollback_plan.md).
- [ ] v1 regression check: v1 endpoints exercised before and after enabling v2;
      no behavior change (v2 is strictly additive).
- [ ] On-call briefed on this runbook and the rollback plan; launch window
      announced.
