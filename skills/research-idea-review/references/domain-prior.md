# Targeted Domain Prior (M3)

M3 builds the field model required to judge this idea. It is neither a generic literature summary nor an exhaustive systematic review. Its output must explain how the field arrived at its current state, where the idea attaches, what evidence norms govern the track, and which gaps remain unsafe to judge.

Execute M3 as three isolated discovery tasks followed by one independent synthesis/grounding task. All four tasks read the original input, confirmed M1 positioning, and M2 route.

## Phase 1: compile the evidence scope

M2 supplies a structured search brief before any M3 worker starts:

- canonical and researcher-used terms for the problem scenario, research object, core difficulty, and contribution;
- historical names and likely terminology changes;
- primary track and adjacent fields where collision or mechanism transfer is plausible;
- contribution-specific evidence norms to recover;
- data, benchmark, resource, and deployment questions;
- current-date frontier cutoff;
- inclusion and exclusion boundaries;
- decisive unknowns that would change positioning or later M5 judgments.

Compile a query matrix instead of one long query:

~~~text
concept family × search purpose × time/venue scope
~~~

Purposes should include origin/definition, method family, known limitation, closest work, negative result, dataset/benchmark, evaluation validity, adjacent collision, and recent practice where applicable.

### Retrieval tool routing

Use whichever academic retrieval tools are available, but separate their roles:

- bibliographic indexes such as AMiner, OpenAlex, Semantic Scholar, Crossref, and arXiv for discovery, identity, citation lineage, and terminology expansion;
- original PDFs or HTML papers for claims, assumptions, experiments, limitations, and exact locators;
- official dataset/benchmark pages and repositories for versions, licenses, protocols, and accessibility;
- first-party project or industrial documentation for current system behavior and deployment constraints;
- general web search for candidate discovery and terminology, followed by direct-source inspection.

No single index has complete coverage. For a decisive closest-work or non-existence-like conclusion, vary both query language and index before treating coverage as adequate.

## Phase 2: foundation and historical paths (m3-foundation)

Recover how problem definitions, assumptions, and solution families evolved.

1. Find authoritative surveys, tutorials, position papers, or field histories only as maps.
2. Follow their references to inspect primary foundational works.
3. Search historical terminology and predecessor tasks, not only the idea's current vocabulary.
4. Trace important transitions: a changed problem definition, assumption, objective, representation, data regime, evaluation norm, or deployment condition.
5. Record consensus separately from active controversy.
6. Search for repeated failures, theoretical limits, and negative results that explain why a branch stalled or changed direction.

The worker should return candidate branch nodes and evidence claims, not a polished evolution tree. Citation count may help discover influential work but cannot establish validity or relevance.

## Phase 3: data and research infrastructure (m3-data)

Map the actual evidence environment in which this idea would be tested:

- datasets, populations, environments, workloads, and collection regimes;
- benchmark tasks, canonical baselines, protocols, and versions;
- metrics, the constructs they approximate, and known validity limits;
- data leakage, contamination, shortcuts, representation gaps, distribution shift, and annotation reliability;
- available code, models, tools, systems, licenses, access requirements, and maintenance status;
- realistic compute, latency, throughput, cost, safety, privacy, and ethical constraints where relevant.

Inspect official dataset cards, benchmark documentation, repositories, licenses, and first-party system documents when these facts affect feasibility. Do not infer current accessibility from an old paper.

## Phase 4: frontier, practice, and collision search (m3-frontier)

Start from recent closest candidates, then expand backward and sideways:

1. Search the exact problem–object–scenario combination.
2. Separately search the proposed intervention or method family.
3. Search cited and citing work around closest candidates.
4. Search terminology variants, workshop/preprint work, and recent benchmark changes.
5. Search adjacent fields for equivalent framing or mechanisms under different names.
6. Look for null results, ablations, replication failures, and practitioner reports that challenge the proposed motivation.
7. Inspect first-party industrial practice only when deployment behavior or engineering constraints matter.

Prioritize primary papers, original code, benchmark documentation, and first-party reports. A search snippet or generated summary can identify a candidate but cannot support a novelty, mechanism, or blocker conclusion.

## Phase 5: synthesize and ground (m3-synthesis)

Use a fresh worker context so discovery narratives do not become accepted conclusions by momentum.

### Verify and deduplicate

- Merge duplicate versions by DOI, arXiv ID, OpenAlex ID, repository, and exact title/author metadata.
- Prefer the final peer-reviewed version when it contains the decisive material; retain a preprint version only when version differences matter.
- Reopen every source used for closest-work, mechanism, non-existence-like, or blocker claims.
- Bind each narrow evidence claim to a verified source and a page, section, figure, table, repository file/version, or official documentation location.
- Preserve contradictory sources and state whether the conflict is factual, scope-based, methodological, or temporal.

Runtime identity verification confirms that a source exists and roughly matches supplied metadata. This worker remains responsible for semantic grounding: whether the inspected passage actually supports, contradicts, or only contextualizes the claim.

### Build the historical evolution tree

Organize history around changes in problems, assumptions, and solution paths:

~~~text
problem origin
├── branch A: framing or method family
│   ├── foundational node
│   ├── transition: what changed and why
│   ├── recent node
│   └── unresolved tension / established limit
├── branch B: competing path
│   └── ...
└── adjacent-field branch
    └── collision or transferable mechanism
~~~

Each node should state its problem, key assumption, contribution, relevant evidence, and relationship to parent/competing nodes. Add cross-links for shared data, evaluation, mechanisms, or hidden equivalent formulations.

Attach the current idea to one or more nodes as continues, combines, redirects, or challenges. Explain the natural next step from the closest branch and how the idea differs from it.

### Build the layered field map

- **Foundation:** canonical definitions, classic works, method families, accepted knowledge, established failures, and unresolved controversies.
- **Data/infrastructure:** datasets, benchmarks, metrics, protocols, resources, access constraints, and validity risks.
- **Frontier/practice:** recent closest work, live attempts, negative results, emerging concerns, industrial practice, and plausible gaps.

### Compare closest work

For each closest candidate, compare at least:

~~~text
problem and scenario
research object and boundary
assumptions
contribution type and core claim
mechanism or method direction
data/evidence setting
evaluation logic
known limitation
relationship to this idea
~~~

Separate “different,” “novel,” and “valuable.” Do not conclude that a contribution does not exist merely because covered searches did not find it.

## Phase 6: coverage audit and stopping

The synthesis worker reports:

- branches, time periods, terminology variants, data settings, and adjacent scopes covered;
- which M4/M5 judgments the evidence can safely support;
- conflicts and unresolved candidates;
- uncovered scopes that could materially change novelty, value, mechanism, or feasibility;
- why further retrieval is unlikely to change a key judgment.

Stop when:

- the main historical branches and transitions are represented;
- the idea can be attached to the tree;
- closest work and the natural next-step path are inspectable;
- relevant evidence norms, data, evaluation, and resource constraints are understood;
- frontier tensions, important negative evidence, and likely adjacent collisions are covered;
- each decisive downstream claim has a canonical evidence claim or is explicitly marked uncertain.

If a stopping condition is unmet, constrain or abstain from the affected M5 judgment. Do not compensate by increasing prose volume.

## Evidence-triggered repositioning

Minor terminology or branch refinements update M3. Set repositioning.required to true only when verified evidence changes the primary domain, track, research object, core difficulty, contribution type, or maturity enough to alter the review route. The runtime will stop before M4 for researcher confirmation.

Use the exact M3 payload structures in [artifact contracts](artifact-contracts.md).
