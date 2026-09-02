# ADR 0002: Codex-Native Artifact Pipeline

- Status: Accepted
- Date: 2026-09-02

## Context

The instruction-only V1 describes a sound review method but cannot guarantee that an agent stops at the positioning checkpoint, that isolated reviewers receive the required upstream context, or that later judgments use real and traceable evidence. A long single conversation also makes M3–M7 compete for the same context window and encourages hidden carry-over between cognitive tasks.

V1.1 must remain a Codex skill rather than become a standalone hosted multi-agent product. It should use separate agent contexts where available, preserve every important dependency across those contexts, and add deterministic checks only where a silent failure would invalidate the review.

## Decision

Adopt a Codex-native hybrid pipeline with four responsibilities:

1. The skill is the researcher-facing supervisor and owns the human interaction.
2. A standard-library Python runtime owns run state, task readiness, immutable artifact envelopes, dependency digests, checkpoints, evidence registration, and validation.
3. Separate Codex workers perform bounded M1–M7 cognitive tasks from generated task packets instead of shared conversation history.
4. Literature and web tools retrieve evidence; the runtime independently resolves source identities before those sources may support a judgment.

The runtime models every stage as an artifact-producing task. A task packet lists every required upstream artifact, not only its immediate parent. Each input is locked by SHA-256. A worker submission must acknowledge each required artifact and state how it was used. Ingestion fails if an input is missing, stale, unacknowledged, or has a different digest.

The dependency graph is explicit:

```text
input → M1 → researcher checkpoint → M2
                                  ├→ M3-foundation ─┐
                                  ├→ M3-data ───────┼→ M3-synthesis
                                  └→ M3-frontier ───┘

M1 + M2 + M3 → M4
M1 + M2 + M3 + M4 → M5-A and M5-B
M1 + M2 + M3 + M4 + M5-A + M5-B → M5-C
M1 + M2 + M3 + M4 + M5-A/B/C → M5-D
M1 + M2 + M3 + M4 + M5-A/B/C/D → M6
M1 + M2 + M3 + M4 + M5-A/B/C/D + M6 → M7
```

Only three validation families are implemented:

- control-flow integrity: checkpoints, task order, explicit dependencies, and stale-input detection;
- evidence integrity: resolvable source identities, registered citation closure, and direct verified evidence for blockers;
- provenance integrity: researcher-stated, retrieved/evidence-supported, inferred, and missing content remain distinguishable.

The runtime does not validate writing style, answer length, arbitrary headings, venue fit, or numeric quality scores.

## Consequences

### Positive

- Context isolation no longer discards M1–M3: dependencies are materialized and cryptographically pinned in every downstream task packet.
- The main context can remain small because it retains only run status, artifact paths, concise summaries, and exceptions.
- A review is resumable, auditable, and reproducible without a database or external Python dependency.
- Unverified candidates can inform further search but cannot silently become supporting evidence.
- An upstream correction makes downstream work observably stale instead of leaving a plausible but invalid report.

### Negative

- Workers must read task packets and return structured submissions, which adds orchestration overhead.
- Identifier resolution establishes that a source exists and matches basic metadata; it cannot prove that the source semantically entails every claim.
- Live source verification depends on network availability. Failure to resolve narrows or delays the review rather than being treated as evidence of non-existence.
- Replacing a major upstream artifact can require rerunning multiple downstream stages.

### Neutral

- The Python runtime does not call an LLM API. Codex remains responsible for selecting tools and dispatching isolated workers.
- M5-A and M5-B remain parallelizable, while all other dependencies are enforced sequentially.

## Alternatives Considered

### Keep the instruction-only skill and add more prompts

Rejected because prose cannot reliably enforce checkpoints, source closure, stale-dependency detection, or resumability.

### Build a standalone Python multi-agent service

Deferred because it would introduce model-provider configuration, deployment, authentication, and operational concerns before the scientific workflow is validated.

### Pass one growing transcript to every reviewer

Rejected because it defeats context isolation, increases contamination between tasks, and makes it impossible to know which version of an upstream conclusion a reviewer used.

## References

- [ADR 0001](0001-position-first-single-review.md)
- [V1.1 implementation plan](../plans/2026-09-02-codex-native-pipeline.md)
