# Solution Space Exploration

Your task is to help me understand all possible solutions to my problem (i.e. to fully explore the solution space).

First, ask me to describe my problem.
There may be important context on the problem in `.current_agent_context/background_context.md` exists, ask my permission to read this file if it exists.

Then, ask me which of the following methods I would like us to use to systematically explore the solution space:
(number them for me so I can make an easy choice)

- MECE (Mutually Exclusive, Collectively Exhaustive)
- First-principles thinking
- Divergent -> Convergent thinking
- SCAMPER
- Systems Thinking
- 6 Thinking Hats (de Bono)
- Morphological Analysis
- A coverage checklist
- MECE (software edition). Dimensions:
  - Data: shape, volume, ownership, lifecycle
  - Computation: sync vs async, stateless vs stateful
  - Interfaces: APIs, contracts, UX, versioning
  - Control flow: orchestration vs choreography
  - State: where it lives, how it mutates
  - Failure modes: partial failure, retries, idempotency
  - Deployment: Monolith / Modular Monolith / Microservices
  - Execution: Synchronous / Asynchronous / Event:driven
  - State: Centralized / Distributed / Client:side
  - Data: SQL / NoSQL / Hybrid
  - Consistency: Strong / Eventual
  - Ownership: Single team / Multiple teams
  - Build vs Open Source vs Buy: Custom / OSS / SaaS
  - Coupling: Tight / Loose
  - Scaling: Vertical / Horizontal
  - Functional: Core use cases, Edge cases, Non:goals
  - Non-Functional: Latency, Throughput, Availability, Security, Cost
  - Architecture: Data ownership, State management, Communication patterns, Deployment model
  - Operability: Logging / metrics / tracing, Rollbacks, Feature flags, Disaster recovery
  - Evolution: Versioning, Migration strategy, Backward compatibility

Once I've chosen a method, talk me through implementing this method through a guided discussion.

Our goal is to explore the solution space as comprehensively as possible.
