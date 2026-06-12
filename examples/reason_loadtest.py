"""Cortex v2 Reason load-test harness.

Drives the v2 Reason endpoint at a fixed request rate and reports achieved
RPS, latency percentiles (p50/p95/p99), time-to-first-event for streaming,
and an error breakdown (429 vs 5xx vs other). Used for the launch-readiness
runs described in docs/reason/checklist.md.

WARNING: every request spends real LLM credits against the target
environment. Point this at staging unless you are intentionally load-testing
production, and keep --max-tokens low.

Set (same variables as examples/, see examples/README.md):
    export MAGICKMIND_API_KEY="sk-..."
    export MAGICKMIND_BASE_URL="https://api.magickmind.ai"  # optional
    export MAGICKMIND_REASON_MODEL="provider/model"           # singular-llm
    export MAGICKMIND_REASON_MODEL_A="provider/model-a"       # mcts*
    export MAGICKMIND_REASON_MODEL_B="provider/model-b"       # mcts
    export MAGICKMIND_RLM_MAIN_MODEL="provider/main-model"    # *rlm*
    export MAGICKMIND_RLM_SUB_MODEL="provider/sub-model"      # *rlm*
    export MAGICKMIND_RATING_MODEL="provider/rating-model"    # mcts*
    export MAGICKMIND_AGGREGATOR_MODEL="provider/agg-model"   # mcts*

Usage:
    python examples/reason_loadtest.py --scenario singular-llm --rps 5 --duration 60
    python examples/reason_loadtest.py --scenario mcts-mixed --rps 0.5 --duration 120 --stream
    python examples/reason_loadtest.py --scenario singular-llm --rps 20 --duration 30 --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv
from magickmind import (
    LLM,
    MCTS,
    RLM,
    Client,
    MagickMindError,
    RateLimitError,
    ReasonFailedEvent,
    Singular,
)

SCENARIOS = ("singular-llm", "singular-rlm", "mcts", "mcts-mixed")

DEFAULT_PROMPT = "Reply with the single word: ok."


@dataclass
class RequestResult:
    ok: bool
    latency_s: float
    ttfe_s: float | None = None
    status_code: int | None = None
    error: str | None = None
    cost_usd: float | None = None


@dataclass
class RunStats:
    results: list[RequestResult] = field(default_factory=list)
    shed: int = 0
    wall_s: float = 0.0

    @property
    def completed(self) -> list[RequestResult]:
        return [r for r in self.results if r.ok]

    @property
    def failed(self) -> list[RequestResult]:
        return [r for r in self.results if not r.ok]


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"error: {name} must be set for this scenario")
    return value


def build_algorithm(scenario: str, max_tokens: int) -> Singular | MCTS:
    """Build the algorithm config for a scenario from environment variables."""
    if scenario == "singular-llm":
        return Singular(LLM(_require_env("MAGICKMIND_REASON_MODEL"), max_tokens=max_tokens))
    if scenario == "singular-rlm":
        return Singular(
            RLM(
                main_model_config=_require_env("MAGICKMIND_RLM_MAIN_MODEL"),
                sub_model_config=_require_env("MAGICKMIND_RLM_SUB_MODEL"),
            )
        )
    if scenario == "mcts":
        return MCTS(
            nodes=[
                LLM(_require_env("MAGICKMIND_REASON_MODEL_A"), max_tokens=max_tokens),
                LLM(_require_env("MAGICKMIND_REASON_MODEL_B"), max_tokens=max_tokens),
            ],
            rating_model=_require_env("MAGICKMIND_RATING_MODEL"),
            aggregator_model=_require_env("MAGICKMIND_AGGREGATOR_MODEL"),
        )
    if scenario == "mcts-mixed":
        return MCTS(
            nodes=[
                LLM(_require_env("MAGICKMIND_REASON_MODEL_A"), max_tokens=max_tokens),
                RLM(
                    main_model_config=_require_env("MAGICKMIND_RLM_MAIN_MODEL"),
                    sub_model_config=_require_env("MAGICKMIND_RLM_SUB_MODEL"),
                ),
            ],
            rating_model=_require_env("MAGICKMIND_RATING_MODEL"),
            aggregator_model=_require_env("MAGICKMIND_AGGREGATOR_MODEL"),
        )
    raise ValueError(f"unknown scenario: {scenario}")


async def run_one(
    client: Client,
    algorithm: Singular | MCTS,
    prompt: str,
    stream: bool,
) -> RequestResult:
    start = time.monotonic()
    try:
        if stream:
            events = await client.reason(
                algorithm=algorithm,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            ttfe: float | None = None
            failed_event: ReasonFailedEvent | None = None
            async for event in events:
                if ttfe is None:
                    ttfe = time.monotonic() - start
                if isinstance(event, ReasonFailedEvent):
                    failed_event = event
            if failed_event is not None:
                return RequestResult(
                    ok=False,
                    latency_s=time.monotonic() - start,
                    ttfe_s=ttfe,
                    error=f"reason_failed: {failed_event.error_code or failed_event.message}",
                )
            return RequestResult(ok=True, latency_s=time.monotonic() - start, ttfe_s=ttfe)

        response = await client.reason(
            algorithm=algorithm,
            messages=[{"role": "user", "content": prompt}],
        )
        cost = response.usage.litellm_cost_usd if response.usage else None
        if response.success is False:
            return RequestResult(
                ok=False,
                latency_s=time.monotonic() - start,
                error=f"reason_failed: {response.error}",
                cost_usd=cost,
            )
        return RequestResult(ok=True, latency_s=time.monotonic() - start, cost_usd=cost)
    except RateLimitError as exc:
        return RequestResult(
            ok=False, latency_s=time.monotonic() - start, status_code=429, error=str(exc)
        )
    except MagickMindError as exc:
        return RequestResult(
            ok=False,
            latency_s=time.monotonic() - start,
            status_code=getattr(exc, "status_code", None),
            error=str(exc),
        )
    except Exception as exc:  # noqa: BLE001 - load test must survive any failure
        return RequestResult(
            ok=False, latency_s=time.monotonic() - start, error=f"{type(exc).__name__}: {exc}"
        )


async def run_load(args: argparse.Namespace) -> RunStats:
    api_key = _require_env("MAGICKMIND_API_KEY")
    base_url = os.environ.get("MAGICKMIND_BASE_URL", "https://api.magickmind.ai")
    algorithm = build_algorithm(args.scenario, args.max_tokens)

    stats = RunStats()
    in_flight = 0
    tasks: list[asyncio.Task[None]] = []

    async with Client(
        api_key=api_key,
        base_url=base_url,
        timeout=args.timeout,
        max_retries=0,  # observe raw 429/5xx; SDK retries would mask them
    ) as client:

        async def worker() -> None:
            nonlocal in_flight
            try:
                stats.results.append(
                    await run_one(client, algorithm, args.prompt, args.stream)
                )
            finally:
                in_flight -= 1

        total = max(1, int(args.rps * args.duration))
        start = time.monotonic()
        for i in range(total):
            # Open-loop pacing: launch at the scheduled arrival time regardless
            # of how many earlier requests are still running.
            target = start + i / args.rps
            delay = target - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            if in_flight >= args.max_in_flight:
                stats.shed += 1
                continue
            in_flight += 1
            tasks.append(asyncio.create_task(worker()))

        if tasks:
            await asyncio.gather(*tasks)
        stats.wall_s = time.monotonic() - start
    return stats


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(pct / 100 * len(ordered)) - 1)
    return ordered[index]


def summarize(args: argparse.Namespace, stats: RunStats) -> dict[str, Any]:
    completed = stats.completed
    failed = stats.failed
    latencies = [r.latency_s for r in completed]
    ttfes = [r.ttfe_s for r in completed if r.ttfe_s is not None]
    costs = [r.cost_usd for r in stats.results if r.cost_usd is not None]
    wall = stats.wall_s or args.duration

    rate_limited = sum(1 for r in failed if r.status_code == 429)
    server_errors = sum(
        1 for r in failed if r.status_code is not None and r.status_code >= 500
    )

    return {
        "scenario": args.scenario,
        "stream": args.stream,
        "target_rps": args.rps,
        "duration_s": round(wall, 1),
        "attempted": len(stats.results),
        "shed_at_max_in_flight": stats.shed,
        "completed": len(completed),
        "achieved_rps": round(len(completed) / wall, 2) if wall else None,
        "error_rate": round(len(failed) / len(stats.results), 4) if stats.results else None,
        "errors": {
            "rate_limited_429": rate_limited,
            "server_5xx": server_errors,
            "other": len(failed) - rate_limited - server_errors,
        },
        "latency_s": {
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
            "p99": percentile(latencies, 99),
            "max": max(latencies) if latencies else None,
        },
        "ttfe_s": {
            "p50": percentile(ttfes, 50),
            "p95": percentile(ttfes, 95),
            "p99": percentile(ttfes, 99),
        }
        if args.stream
        else None,
        "total_cost_usd": round(sum(costs), 4) if costs else None,
        "sample_errors": [r.error for r in failed[:5]],
    }


def print_report(report: dict[str, Any]) -> None:
    def fmt(value: float | None) -> str:
        return f"{value:.3f}" if value is not None else "-"

    lat = report["latency_s"]
    print(f"\n=== Reason v2 load test — {report['scenario']}"
          f"{' (streaming)' if report['stream'] else ''} ===")
    print(f"target {report['target_rps']} rps for {report['duration_s']}s"
          f" | attempted {report['attempted']} | completed {report['completed']}"
          f" | achieved {report['achieved_rps']} rps")
    print(f"error rate: {report['error_rate']} | errors: {report['errors']}"
          f" | shed: {report['shed_at_max_in_flight']}")
    print(f"latency  p50={fmt(lat['p50'])}  p95={fmt(lat['p95'])}"
          f"  p99={fmt(lat['p99'])}  max={fmt(lat['max'])}  (seconds)")
    if report["ttfe_s"]:
        ttfe = report["ttfe_s"]
        print(f"ttfe     p50={fmt(ttfe['p50'])}  p95={fmt(ttfe['p95'])}"
              f"  p99={fmt(ttfe['p99'])}  (seconds)")
    if report["total_cost_usd"] is not None:
        print(f"total LLM cost: ${report['total_cost_usd']}")
    for err in report["sample_errors"]:
        print(f"  sample error: {err}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scenario", choices=SCENARIOS, default="singular-llm")
    parser.add_argument("--rps", type=float, default=1.0, help="target request rate")
    parser.add_argument("--duration", type=float, default=60.0, help="run length in seconds")
    parser.add_argument("--stream", action="store_true", help="use SSE streaming requests")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--max-tokens", type=int, default=32,
                        help="max_tokens applied to plain LLM nodes to bound cost")
    parser.add_argument("--timeout", type=float, default=120.0, help="per-request timeout")
    parser.add_argument("--max-in-flight", type=int, default=256,
                        help="safety cap on concurrent requests; excess arrivals are shed")
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    return parser.parse_args()


async def main() -> None:
    load_dotenv()
    args = parse_args()
    stats = await run_load(args)
    report = summarize(args, stats)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)


if __name__ == "__main__":
    asyncio.run(main())
