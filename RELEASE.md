# Release Readiness

model-router is part of the AGenNext core runtime.

## Boundary

model-router selects and routes model requests. It does not orchestrate agents or execute capabilities.

## Release Requirements

- Clear API contracts
- Explicit routing rules
- No hidden cloud dependency
- No random SDK dependency
- Airgap-compatible routing paths
- Versioned releases

## Primitive Rule

External model systems may be adapters. They must not become core dependencies.
