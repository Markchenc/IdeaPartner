# Artifact Contracts

Task packets contain exact required top-level keys. This reference defines the stable nested contracts. Keep content concise but structurally complete. Do not add fabricated values to satisfy a field; use an explicit missing or uncertain value where the contract allows it.

The `artifact_contract` entry in every generated task packet is only a pointer to this shared serialization reference. It does not add a new reviewer or evaluation dimension. M5 has a larger payload section because its four isolated workers need a common handoff shape.

## Common submission envelope

```json
{
  "task_id": "m4-reconstruction",
  "summary": "Two to four sentences for supervisor state tracking; not a replacement for the artifact.",
  "attention_items": ["Only exceptions, coverage gaps, or researcher decisions that need attention."],
  "consumed_inputs": [
    {
      "artifact_id": "m3-synthesis",
      "artifact_version": 1,
      "used_for": "Constrained closest-work comparisons and field evidence norms."
    }
  ],
  "payload": {}
}
```

Copy every input's `artifact_id` and `artifact_version` from the packet. `used_for` must name the actual role of that particular input in the output. Artifact versions identify the registered upstream result; they do not verify literature existence or semantic truth.

The supervisor reads `summary` and `attention_items` to manage its compact main context. Downstream workers still read the complete pinned artifacts; summaries never satisfy a scientific dependency.

## M1 positioning

Required payload keys:

```text
domains
scenario
research_object
core_difficulty
contribution
maturity
control
```

Use the structure in [positioning and routing](positioning-and-routing.md). Preserve alternatives and uncertainty inside these objects rather than choosing a convenient interpretation silently.

## M2 route

```json
{
  "maturity": "early | middle | developed",
  "alignment_questions": [],
  "m3_scope": {
    "branches": [],
    "adjacent_collision_scopes": [],
    "evidence_norms_to_find": [],
    "data_and_resource_questions": [],
    "frontier_cutoff": "<date>"
  },
  "m4_assessability": {},
  "review_lens_seed": {
    "primary_contribution": "<type>",
    "secondary_contribution": null,
    "maturity_depth": {},
    "likely_blocker_scopes": []
  }
}
```

## M3 discovery artifacts

M3-foundation, M3-data, and M3-frontier share this contract:

```json
{
  "scope": {"included": [], "excluded": [], "time_window": ""},
  "queries": [{"query": "", "purpose": "", "result_note": ""}],
  "sources": [],
  "evidence_claims": [],
  "coverage": {"covered": [], "gaps": [], "conflicts": [], "next_queries": []}
}
```

### Source record

```json
{
  "source_id": "stable-local-id",
  "source_type": "paper | dataset | benchmark | repository | official_docs | first_party_report",
  "title": "Exact title",
  "authors": ["Author"],
  "year": 2025,
  "url": "https://...",
  "identifiers": {
    "doi": "10....",
    "arxiv": "2501.00001",
    "openalex": "W...",
    "semantic_scholar": "..."
  },
  "content_locator": "page/section/commit/version inspected"
}
```

Supply at least one DOI, arXiv ID, OpenAlex ID, or public HTTPS URL. Do not write a `verification` field; ingestion creates it. Search-result snippets are candidate discovery material, not source records for decisive claims.

`source_type` is a closed set. Use exactly one of `paper`, `dataset`, `benchmark`, `repository`, `official_docs`, or `first_party_report`. Arbitrary values are rejected, and every URL-only source type must pass HTML-title identity matching; reclassification cannot turn mere URL reachability into verification.

### Evidence claim

```json
{
  "claim_id": "stable-claim-id",
  "claim": "Narrow proposition actually supported or challenged",
  "source_ids": ["stable-local-id"],
  "relation": "support | contradict | context",
  "locator": "page, section, figure, table, or documented passage"
}
```

A real source is not automatically relevant evidence. The M3 worker must inspect it and bind a narrow claim to a locator. Ingestion accepts evidence claims only when all referenced sources were independently verified.

## M3 synthesis

```json
{
  "evolution_tree": {},
  "field_map": {"foundation": {}, "data": {}, "frontier": {}},
  "idea_attachment": {"nodes": [], "relation": "continues | combines | redirects | challenges"},
  "closest_work": ["source-id"],
  "evidence_claims": [],
  "coverage": {
    "sufficient_for": [],
    "insufficient_for": [],
    "gaps": [],
    "conflicts": [],
    "stopping_reason": ""
  },
  "repositioning": {"required": false, "reason": "", "proposed_change": null}
}
```

M3 synthesis is the grounding boundary. Reopen decisive sources, reconcile duplicates and conflicts, and emit the canonical `evidence_claims` used by M4–M7. Later stages cite these claim IDs rather than attaching arbitrary papers directly.

## M4 reconstructed idea

Each of the six required section keys contains a list of items:

```json
{
  "text": "One inspectable idea statement",
  "provenance": "researcher_stated | evidence_supported | inferred | missing",
  "evidence_claim_ids": []
}
```

Only `evidence_supported` may have non-empty `evidence_claim_ids`, and each ID must exist in canonical M3 synthesis. `researcher_stated`, `inferred`, and `missing` must use an empty list.

Required section keys:

```text
problem_definition
limitations_and_core_difficulty
contribution_design
method_construction
experimental_setting
expected_difficulties
```

## M5 review artifacts

### What this contract is

The M5 artifact contract is an inter-agent transport boundary. It makes four separate workers exchange inspectable, evidence-linked results without relying on a shared context. It is not a final Idea Evaluation Ontology, a scorecard, or a claim that the runtime can mechanically reproduce expert metacognition.

The current four top-level fields have narrow roles:

- `review_lens` records the maturity, contribution type, field norms, applicable questions, and details deliberately not required for this route;
- `judgments` contains atomic review conclusions with provenance, canonical M3 evidence, alternatives, assumptions, coverage limits, change conditions, and actions;
- `conclusion` is the worker's task-level synthesis, not the overall M7 decision;
- `blocker` separates a high-evidence gate from an ordinary risk and states what it blocks.

The runtime validates structural presence, provenance/evidence closure, and the minimum direct evidence required to declare a blocker. It does not validate whether the worker selected the best field-specific questions, reasoned correctly about a mechanism, resolved every scientific conflict, or calibrated the conclusion like a domain expert. Those semantics currently come from M1–M4, the dependency chain, and the M5 instructions.

M5-A through M5-D share this shape:

```json
{
  "review_lens": {
    "maturity": "",
    "primary_contribution": "",
    "secondary_contribution": null,
    "field_norms": [],
    "applicable_questions": [],
    "not_yet_required": []
  },
  "judgments": [
    {
      "claim": "",
      "status": "",
      "provenance": "researcher_stated | evidence_supported | inferred | missing",
      "evidence_claim_ids": [],
      "counterevidence_or_alternative": "",
      "assumptions": [],
      "coverage_limit": "",
      "change_condition": "",
      "action": ""
    }
  ],
  "conclusion": "",
  "blocker": {
    "active": false,
    "scope": "none",
    "reason": "",
    "direct_evidence_claim_ids": []
  }
}
```

An active blocker requires at least one canonical M3 evidence claim that directly affects the core claim. A worker may still report an unresolved risk without declaring a blocker.

### Deferred M5 redesign

Keep this payload stable in the current PR. A later M5-focused PR may revise the internal judgment decomposition, contribution-conditioned question compiler, maturity-conditioned sufficiency rules, conflict representation, blocker semantics, and cross-task synthesis. That work should begin from actual review cases and does not belong to the runtime-concurrency and evidence-identity corrections here.

## M6 challenge

```json
{
  "selected_challenges": [
    {
      "type": "closest_prior_substitution | simpler_alternative | weakest_assumption",
      "target": "M5 judgment identifier or exact claim",
      "result": "",
      "evidence_claim_ids": []
    }
  ],
  "updates": [
    {
      "target": "M5-A | M5-B | M5-C | M5-D",
      "change": "strengthen | weaken | add_blocker | remove_blocker | no_change",
      "reason": "",
      "evidence_claim_ids": []
    }
  ]
}
```

Select no more than three challenges.

## M7 synthesis

```json
{
  "report_markdown": "# Research idea review ...",
  "conclusion": "calibrated overall decision",
  "citation_claim_ids": ["canonical-m3-claim-id"]
}
```

`citation_claim_ids` is the closure list for every literature-dependent statement retained in the final report. The runtime checks that each claim exists; the worker must render the corresponding verified source citation near the relevant statement.
