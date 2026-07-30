# Fault-injection reliability benchmark design

Status: design-only scaffold pending maintainer scope confirmation.

## Goals

The benchmark runs a real agent task under a deterministic, declarative fault
schedule and produces an inspectable reliability scorecard. It answers:

1. Did the run recover and complete the ordinary task?
2. Did replay avoid duplicating an already committed irreversible effect?
3. What recovery overhead did the fault add?

It does not replace the task's existing grader, infer external commits from
language-model output, or treat a fresh retry as successful resume.

## Scenario schema

Every scenario is a versioned document with:

```yaml
schema_version: 1
scenario_id: swebench.restart.after_action.v1
task:
  benchmark: swebench
  instance_id: example__project-123
agent:
  config: default
seed: 81321
faults:
  - fault_id: restart-1
    kind: sandbox_restart
    trigger:
      event:
        event_type: ActionEvent
        ordinal: 1
    parameters:
      restart_mode: hard
    release:
      kind: immediate
oracles:
  completion:
    kind: benchmark_native
  effects:
    kind: ledger
    ledger_path: /workspace/reliability/effects.jsonl
budgets:
  run_timeout_seconds: 1800
  recovery_timeout_seconds: 300
```

Required identity fields are `schema_version`, `scenario_id`, task identity,
agent/config identity, and seed. A run manifest records resolved defaults,
source revisions, images, resource factors, and generated fault timestamps.

## Determinism

The schedule takes an explicit integer seed. Random choices use a dedicated
scenario RNG and never module-global randomness. A schedule is compiled before
the run into ordered fault specifications. Trigger matching is deterministic
over the persisted event stream and explicit lifecycle phases.

Preferred trigger selectors:

- lifecycle phase, such as `workspace_ready` or `conversation_attached`
- event type plus ordinal
- action/tool-call ID
- logical operation ID from a scenario-owned effect

Wall-clock-only triggers are allowed for transport duration but are not the
primary placement mechanism because scheduler variance makes them hard to
reproduce.

Every injected fault produces a receipt containing the scenario/run/fault IDs,
seed, resolved trigger, observed event/tool-call ID, monotonic timestamp,
runtime and conversation identities, injector result, and release result.

## Fault interface

The scaffold defines a typed `FaultInjector` protocol:

- `arm(context, fault) -> FaultHandle`
- `inject(context, fault, handle) -> FaultReceipt`
- `release(context, fault, handle) -> FaultReceipt | None`

`FaultContext` exposes only explicit adapters: event observation, runtime
lifecycle control, transport control, process control, and receipt recording.
It must not grant graders access to hidden agent reasoning.

### Sandbox restart

Parameters:

- target: agent-server container or remote runtime
- restart mode: graceful, hard stop, or replacement
- persistence policy: preserve workspace/events, preserve events only, or
  scenario-defined
- reattach deadline

The injector records pre/post runtime ID, conversation ID, event-store
location, provider session ID when available, and first post-recovery event.

### Lost dispatch response

Parameters:

- boundary: tool-result-before-observation or remote transport response
- target tool/action selector
- drop count

The first milestone should implement only a boundary verified in the actual
execution path. A synthetic exception before dispatch is not a lost response.
The effect ledger independently records whether the external operation
committed.

### SIGKILL mid-tool-call

Parameters:

- target process/container
- target action selector
- signal (`SIGKILL` for the named scenario)
- optional replacement/start policy

The trigger requires a persisted action receipt and no persisted
observation/error at kill time. Cooperative `interrupt()` is a different fault
kind and must not be reported as SIGKILL.

### Network partition

Parameters:

- endpoint class: runtime control, conversation transport, tool transport, or
  scenario external service
- direction: ingress, egress, or both
- failure mode: drop, timeout, reset, or bounded latency
- release: duration or deterministic receipt trigger

The report names the actual wrapped client/endpoint. “Network partition”
without a boundary is invalid.

## Inspectable scenario effects

Duplicate-effect scenarios use a deterministic local service or ledger-backed
tool. Each logical action has:

- `operation_id`
- optional idempotency key
- request payload digest
- commit sequence and timestamp
- query endpoint or append-only ledger

The grader reads this evidence directly. The agent cannot mark its own effect
as successful. Initial scenarios should avoid real destructive external
systems; they can model an irreversible append, charge, or publish operation in
a local deterministic service.

## Run phases

1. Resolve scenario and seed.
2. Record source/image/config manifest.
3. Execute a matched no-fault baseline if one is not cached.
4. Prepare the real benchmark workspace and conversation.
5. Arm the compiled schedule.
6. Stream persisted events and lifecycle receipts to the scheduler.
7. Inject and release faults at resolved triggers.
8. Exercise the product's real resume/reattach path.
9. Run the ordinary benchmark grader.
10. Run inspectable reliability graders.
11. Emit per-run artifacts and aggregate scorecard.

Failed injection is not silently converted to an agent failure. It is a
separate `invalid_injection` outcome so reliability scores cannot improve when
the requested fault never happened.

## Scoring model

Report raw evidence and sub-scores. Do not collapse failures into a single
opaque model judgment.

### Completion/resume

Per run:

- `task_completed`: ordinary grader pass/fail
- `fault_injected`: required receipt present
- `history_restored`: persisted event continuity observed
- `runtime_reattached`: recovery path observed
- `provider_session_rebound`: true, false, or not applicable
- `fresh_retry_used`: whether a new attempt/workspace replaced recovery

`completion_resume_score` is 1 only when the fault was injected, the ordinary
task passed, required recovery receipts are present, and the scenario did not
fall back to a forbidden fresh retry. Otherwise it is 0. Aggregate as a rate
with numerator and denominator shown.

### No duplicate irreversible effect

For each logical operation:

```text
duplicate_count = max(0, committed_effect_count - intended_effect_count)
```

Per-run score is 1 only when all intended effects have exactly the expected
commit count and payload. Missing effects and duplicate effects are reported
separately. Aggregate:

- clean-effect run rate
- duplicated logical operations / attempted logical operations
- total excess commits

### Recovery overhead

Compare a faulted run with its matched baseline:

```text
wall_time_ratio = faulted_wall_time / baseline_wall_time
wall_time_delta = faulted_wall_time - baseline_wall_time
```

Also report recovery-window seconds, iteration delta, event delta, tool-call
delta, token/cost delta, and replay/detection time. Ratios with a zero or
missing baseline are null and excluded from aggregates, never coerced.

The aggregate scorecard presents medians and tail percentiles rather than a
hidden weighted scalar. If maintainers later request one headline number, its
formula and component weights must be published alongside the raw components.

## Grader interface

Each grader receives:

- resolved scenario and manifest
- baseline evidence when applicable
- persisted event evidence
- fault receipts
- runtime/recovery receipts
- ordinary benchmark result
- external effect ledger
- metrics and timestamps

It returns a typed result with `passed`, `value`, `reason_codes`, and
`evidence_refs`. Reason codes are stable and machine-readable; evidence
references point to concrete JSONL records, event IDs, or grader outputs.

No grader calls an LLM.

## Artifacts

Per run:

- `manifest.json`
- `resolved_schedule.json`
- `fault_receipts.jsonl`
- `recovery_receipts.jsonl`
- `events.jsonl` or an immutable reference to the product event store
- `effects.jsonl`
- `native_grader.json`
- `reliability_result.json`
- `metrics.json`

Aggregate:

- `scorecard.json`
- `scorecard.md`
- optional CSV rows for analysis

Secrets, provider transcripts not needed for grading, and raw environment
values are excluded or redacted.

## Scorecard

The Markdown scorecard groups by agent/config, scenario, fault kind, and seed
set. Columns:

- runs / valid injections
- ordinary task pass rate
- completion/resume rate
- clean-effect run rate
- duplicate operations and excess commits
- median and p95 recovery seconds
- median wall-time ratio
- median tool-call, token, and cost deltas
- invalid-injection and infrastructure-failure counts

Links from each aggregate row lead to inspectable per-run artifacts and reason
codes.

## Test strategy after scope approval

- schema validation and deterministic schedule compilation
- trigger matching over fixed event fixtures
- injector contract tests with fake adapters
- grader tests over hand-authored event/effect ledgers
- negative tests for fault-not-injected, fresh retry, missing baseline, missing
  effect, and duplicate effect
- one live local agent-server smoke scenario
- one real SWE-bench subset scenario only after the local smoke path is stable

The current test file is intentionally skipped and contains no feature logic.

## Phasing

Phase 1 is only this architecture/design and typed scaffold.

After maintainer buy-in, a proposed smallest Phase 2 is:

1. one local deterministic irreversible-effect tool;
2. one hard agent-server restart or lost-result fault at a verified boundary;
3. one small SWE-bench subset;
4. the three inspectable graders and Markdown/JSON scorecard.

Network partitions, provider-session rebound, and multiple concurrent unmatched
actions remain later milestones unless maintainers explicitly prioritize them.
