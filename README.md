# model-router

`model-router` is the model decision and execution service for AGenNext.

It answers one simple question:

> Given a task, which model/runtime should handle it, and how should it be called?

For now, `model-router` is intentionally a single lightweight service. There is no separate model gateway.

## Responsibilities

`model-router` owns:

- selecting a model for a task
- selecting a runtime or provider
- applying simple routing rules
- calling the selected model through an adapter
- returning the model response or routing decision
- recording basic routing metadata later

## Not Responsibilities

`model-router` does not own:

- agent orchestration
- capability execution
- tool execution
- skill definitions
- UI flows
- workflow state

Those belong to other AGenNext components.

## Relationship With Agent-Kernel

```txt
Agent-Kernel
  = decides what capability should run

model-router
  = decides what model should be used
  = calls that model/runtime through an adapter
```

Typical flow:

```txt
Agent-Kernel
  ↓
model-router
  ↓
local model / remote model / custom runtime
```

## Current Design

The first version should stay small:

```txt
request
  ↓
normalize task
  ↓
choose model/runtime
  ↓
execute adapter
  ↓
return result
```

## Initial API Shape

Example decision/execution request:

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
  "model": "local-rule-engine",
  "runtime": "builtin",
  "output": {
    "capability": "analyze.echo",
    "reason": "Selected default analysis capability",
    "input": "Analyze uploaded content"
  }
}
```

## Adapter Direction

Adapters can be added later for:

- built-in rule engine
- local model runtimes
- remote model APIs
- custom in-house models

The core API should remain stable even as adapters change.

## Design Rule

Keep `model-router` lightweight.

Do not split it into more services until there is a real operational need.
