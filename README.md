# model-router

model-router owns model selection and routing decisions for AGenNext.

## Decision

model-router decides which certified model should be used for a task, request, agent, workflow, tenant, policy, cost target, latency target, quality requirement, or risk posture.

It does not execute model calls directly.

```txt
model-repository
  = candidate models, testing, build, eval, staging

model-registry
  = certified production-grade model catalog

model-router
  = model selection and routing decision layer

model-gateway
  = model provider/runtime access and execution layer
```

## Scope

model-router owns:

- model routing policies
- task-to-model selection
- fallback model selection
- cost-aware routing
- latency-aware routing
- quality-aware routing
- tenant-aware routing
- policy-aware routing
- safety/risk-aware routing
- benchmark-aware routing
- capability matching
- routing decision records

model-router does not own:

- candidate model testing
- production certification
- model serving
- provider credential custody
- final platform authority
- benchmark execution

## Boundary

| Component | Responsibility |
|---|---|
| model-router | Selects the best certified model for a task/context |
| model-gateway | Executes calls to model providers/runtimes |
| model-registry | Certified production-grade model catalog |
| model-repository | Candidate model build/test/eval/staging repository |
| Agent-Bench | Benchmark suites and result publishing |
| Agent-Eval | Scoring/rubrics/quality metrics |
| Agent-Policies | Routing constraints and governance policies |
| Agent-Platform | Final authority for high-risk model routing decisions |

## Routing inputs

A routing decision may consider:

- task type
- modality
- required capabilities
- latency budget
- cost budget
- quality threshold
- benchmark results
- eval scores
- safety profile
- tenant policy
- data sensitivity
- provider availability
- fallback requirements

## Routing lifecycle

```txt
request received
  ↓
normalize task and policy context
  ↓
query model-registry for certified eligible models
  ↓
rank models by capability, quality, latency, cost, and risk
  ↓
select primary and fallback model
  ↓
model-gateway executes selected route
  ↓
record routing decision and outcome
```

## Rule

Only certified models from model-registry should be eligible for production routing unless Agent-Platform explicitly approves an exception.
