# Cortex v2 Reason — Rollback Plan

How to take the v2 Reason API out of service quickly and safely, and how to
rehearse doing it. Companion to [checklist.md](checklist.md).

**Hard target: from the rollback decision to v2 traffic fully stopped must take
no more than 5 minutes.**

## Why Rollback Is Cheap Here

The design makes rollback a configuration change, not a code revert:

- **v2 is fully additive.** v1 engines, RPCs, and endpoints are frozen and
  unmodified; the v2 service is registered alongside them. Disabling v2 cannot
  affect v1 traffic.
- **Cortex is stateless for v2.** No stored responses, no response chaining —
  so there is no v2 data to migrate, drain, or clean up. Conversation state
  lives in the orchestration layer and is untouched.
- **Single ingress.** All v2 traffic enters through `POST /v2/chat/completions`
  at the API edge. Closing that one route stops everything.

Rollback therefore means: **disable the v2 route at the API edge.** Do not
revert commits, redeploy old images, or touch v1 configuration under incident
pressure.

## Rollback Triggers

Roll back when any of these holds and is not explained by a transient upstream
blip already recovering:

- Error rate (5xx + `reason.failed`) above 0.5% for 10+ minutes.
- v2 traffic degrading v1 (shared infrastructure saturation: error rate or
  latency regression on v1 correlated with v2 load).
- Cost-per-request anomaly sustained at > 3× baseline (runaway recursion or
  provider pricing surprise).
- Security or data-handling defect in the v2 path.

A single on-call engineer is empowered to decide. Roll back first, diagnose
after — re-enabling is the same one-step change.

## Rollback Procedure

Timed against the 5-minute target. Times are cumulative from the decision.

| T+ | Step | Verify |
|---|---|---|
| 0:00 | Declare rollback in the incident channel; note the trigger. | — |
| 0:30 | Disable the v2 route at the API edge (config flag / route removal). v2 requests now receive **503**. | Config change applied |
| 1:30 | Confirm v2 is off: send one v2 request; expect 503. | `curl` or `examples/reason_loadtest.py --rps 0.2 --duration 10` shows 100% 5xx, 0 completed |
| 2:30 | Confirm v1 is healthy: exercise a v1 endpoint; check v1 dashboards. | v1 error rate and latency at baseline |
| 3:30 | Confirm in-flight v2 work has drained (request rate at the edge → 0; no orphaned upstream LLM calls accumulating on the cost panel). | Dashboards |
| 4:00 | Announce: v2 disabled, v1 unaffected, next update time. | — |

Re-enable is the same procedure in reverse: re-open the route, verify one
request succeeds, watch the dashboards for 15 minutes before announcing.

### What clients see during rollback

- New v2 requests fail with 503. The SDK retries 503 with exponential backoff
  (`max_retries`, default small) and then raises `MagickMindError` with
  `status_code=503`. Callers should catch `MagickMindError` and fall back or
  surface the failure.
- In-flight non-streaming requests either complete or fail with the same error.
- In-flight SSE streams either run to completion or terminate; the SDK does
  **not** restart a stream that has already emitted events, so a mid-stream cut
  surfaces as an error to the caller rather than a silent retry.
- v1 clients are unaffected throughout.

## Rollback Rehearsal

Rehearse against **staging** before launch, and again after any change to edge
routing. The drill is the full procedure above, timed, with synthetic load
running so the drain step is meaningful:

1. Start background load: `python examples/reason_loadtest.py --scenario
   singular-llm --rps 2 --duration 600` (staging credentials).
2. Execute the procedure table top to bottom, recording the actual time of each
   step.
3. Confirm the load-test report shows the cutover (completions stop, 5xx begin)
   and that v1 staging checks stayed green.
4. Re-enable, confirm recovery, record total elapsed time for both directions.

A drill **passes** when decision-to-traffic-stopped is ≤ 5 minutes and v1
metrics never moved.

### Drill log

| Date | Operator | Environment | Decision → v2 stopped | Re-enable → recovered | Pass | Notes |
|---|---|---|---|---|---|---|
| _yyyy-mm-dd_ | | staging | | | | |
