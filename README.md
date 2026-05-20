# model-router

`model-router` is the model selection and routing service for AGenNext.

It answers one simple question:

> Given a task, which model should be used, and where should the request be routed?

`model-router` does **not** run models directly. It routes to `Model-Runner`, which owns actual model execution.

## Responsibilities

`model-router` owns:

- selecting a model for a task
- selecting the right runner endpoint
- applying routing rules
- applying fallback rules
- considering latency, cost, quality, modality, and policy constraints
- returning routing decisions
- recording routing metadata later

## Not Responsibilities

`model-router` does not own:

- model process execution
- model downloads
- GPU/runtime lifecycle
- token generation
- agent orchestration
- capability execution
- tool execution
- skill definitions

Those belong to other AGenNext components.

## Relationship With Agent-Kernel And Model-Runner

```txt
Agent-Kernel
  = capability orchestration

model-router
  = model selection and routing

Model-Runner
  = model execution
```

Typical flow:

```txt
Agent-Kernel
  ↓
model-router
  ↓
Model-Runner
  ↓
local model runtime
```

## Current Design

The first version should stay small:

```txt
request
  ↓
normalize task
  ↓
choose model
  ↓
route to Model-Runner
  ↓
return result or decision
```

## Initial API Shape

Example request:

```json
{
  "task": "plan-next-capability",
  "input": "Analyze uploaded content",
  "capabilities": ["analyze.echo"],
  "constraints": {
    "latency": "low",
    "cost": "low"
  }
}
```

Example response:

```json
{
  "model": "tinyllama-1.1b",
  "runner": "local",
  "route": "http://localhost:4100/v1/generate",
  "output": {
    "capability": "analyze.echo",
    "reason": "Selected default lightweight planner model",
    "input": "Analyze uploaded content"
  }
}
```

## Design Rule

Keep `model-router` lightweight.

Do not use external routing/proxy products unless there is a real need. AGenNext owns this layer.
