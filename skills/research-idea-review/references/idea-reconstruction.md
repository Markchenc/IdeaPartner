# Structured Idea Reconstruction (M4)

M4 converts the confirmed idea and canonical M3 evidence into one inspectable review object. It organizes; it does not improve the idea invisibly. The isolated M4 worker must read the original input, confirmed M1 positioning, M2 route, and M3 synthesis from its task packet; none is optional or implied by prior conversation.

## Provenance states

Mark important content inline when its origin affects interpretation:

- **Researcher-stated**: explicitly supplied by the researcher;
- **Evidence-supported**: grounded in retrieved sources;
- **Inferred**: a limited interpretation needed to connect supplied claims;
- **Missing/uncertain**: not available or not safely inferable.

Never present inferred method details, data, hypotheses, or expected results as part of the researcher's original idea.

Represent every item as:

```json
{
  "text": "One inspectable statement",
  "provenance": "researcher_stated | evidence_supported | inferred | missing",
  "evidence_claim_ids": []
}
```

Only `evidence_supported` content may cite canonical M3 evidence claim IDs. A real paper ID by itself is insufficient because it does not establish the paper–claim relation. Researcher-stated, inferred, and missing items must keep `evidence_claim_ids` empty.

## Six-section structure

### 1. Problem definition

- research question or target problem;
- problem scenario and research object;
- relevant boundaries and constraints;
- intended outcome or knowledge target.

### 2. Limitations of existing approaches / core difficulty

- how the field currently handles the problem;
- observed limitations or unresolved tension;
- claimed core bottleneck;
- evidence that the limitation is real rather than rhetorical.

### 3. Core research point / contribution design

- the central nugget;
- proposed contribution;
- what changes relative to existing paths;
- intended knowledge or practical increment.

Perspectives, hypotheses, reframings, discoveries, artifacts, and theoretical claims belong here when they constitute the core contribution.

### 4. Method construction

- method, mechanism, theoretical route, design intervention, or investigation strategy;
- main components and their roles;
- intended connection to the core difficulty;
- unresolved parts appropriate to the current maturity.

If the idea is early and has no method direction, state that directly. Do not generate one merely to satisfy the template.

### 5. Experimental setting

- data, participants, environment, or workload;
- baseline or comparison logic;
- observations, metrics, or evidence sought;
- preliminary validation route.

For non-experimental contributions, interpret this as the appropriate evidence or validation setting rather than forcing a benchmark experiment.

### 6. Expected difficulties

- conceptual or theoretical risks;
- data and measurement risks;
- method or experiment risks;
- engineering, access, resource, safety, or ethical constraints;
- conditions that could invalidate the contribution.

## Researcher-facing output

Use concise prose or tables. Explicitly call out material ambiguities and missing sections, but do not treat every missing item as a defect. M5 determines whether a missing item is required at the confirmed maturity.

Use the six exact payload keys in [artifact contracts](artifact-contracts.md) so the runtime can preserve provenance without validating writing style.
