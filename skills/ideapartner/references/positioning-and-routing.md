# Positioning and Routing (M0–M2)

## M0: input check

The only required input is the researcher's current idea description. Optional context includes known related work, target community, intended contribution, available data/resources, time constraints, and the decision the researcher wants help making.

Proceed when at least one of these is identifiable:

- a research object;
- a phenomenon, failure, tension, or need;
- an intended scientific or practical change.

If none is identifiable, ask one focused question. Do not expand a broad topic into a proposal on the researcher's behalf.

## M1: structured positioning card

Produce this complete structure while keeping uncertain alternatives visible.

### 1. Domains

- Primary domain
- Related domains
- Adjacent domains where prior-art collision is plausible

### 2. Problem scenario and track

- Technical, social, or scientific setting
- Relevant actors, users, or systems
- Operating environment and constraints
- Concrete task, problem family, or research track

Treat the scenario as a first-class object because it determines the relevant field prior, evidence norms, data, and practical constraints.

### 3. Research object

- Core research object
- Unit of analysis or intervention
- Scope boundary
- Nearby objects explicitly out of scope

### 4. Core difficulty or target problem

- Observed problem
- Claimed core difficulty
- Object to explain, change, or optimize
- Intended change

Record the researcher's current claim. Do not yet decide whether the claimed difficulty is the root cause.

### 5. Core contribution type

- Primary contribution type
- Optional secondary contribution type
- Current contribution claim
- Claim clarity
- Claimed significance

Use one of these contribution families when possible: new problem/framing; method/algorithm; theory; empirical discovery/measurement; system/AI infrastructure; dataset/benchmark; HCI/design research; application/translation; replication/negative result.

At M1, assess whether the contribution claim is intelligible. Do not validate actual novelty or significance before M3/M5.

### 6. Maturity

- `early`: a problem, observation, tension, or perspective exists, but contribution mechanism and validation are incomplete;
- `middle`: a contribution point and method/direction exist, but evidence, experiment, or risk handling is incomplete;
- `developed`: problem, contribution, method, and experimental setting form a preliminary closed loop.

Include:

- maturity rationale;
- currently assessable parts;
- parts that should not yet be required.

### Control metadata

- Positioning confidence: high, medium, or low, with reasons
- Ambiguities requiring confirmation
- Alternative positioning when more than one reading is plausible

## Mandatory researcher checkpoint

Present the M1 card and ask the researcher to confirm or correct it. Explicitly ask whether the domains, scenario/track, research object, core difficulty, contribution type, and maturity reflect their intent. Stop and wait.

Do not phrase inferred content as if the researcher supplied it.

After the M1 worker submission is ingested, the runtime enters `WAITING_FOR_POSITIONING_CONFIRMATION`. Do not record confirmation from your own interpretation of silence or an earlier message. Record it only after the researcher responds to the displayed card. If they correct M1, emit a refreshed M1 task, replace the artifact, show the new card, and wait again.

## M2: route compilation after confirmation

M2 is an internal planner. It may identify an obvious mismatch, but it must not issue the final review.

### Preliminary consistency pass

Check:

```text
scenario ↔ research object
research object ↔ core difficulty
core difficulty ↔ contribution claim
available method direction ↔ scenario constraints
```

Use mismatches to create review questions, not premature rejection.

### Maturity calibration

Long prose is not evidence of maturity. A detailed method with an unstable problem definition may still be early; a concise idea with a clear contribution and decisive validation path may be middle or developed.

### Compile the route

Produce the structured M2 artifact with:

- confirmed/calibrated `maturity`;
- `alignment_questions` created by the preliminary consistency pass;
- `m3_scope`: historical branches, adjacent collision scopes, terminology variants, field evidence norms, data/resource questions, inclusion/exclusion boundaries, and a current-date frontier cutoff;
- `m4_assessability`: which of the six sections are assessable, provisional, or not yet required;
- `review_lens_seed`: primary/secondary contribution, maturity depth for A–D, likely blocker scopes, and field norms M3 must recover.

M2 must be usable as a search brief by three workers that do not share its reasoning context. Avoid references such as “as discussed above”; materialize the needed scope and questions in the artifact.

Do not create numeric weights. The route changes questions, evidence requirements, applicability, and gate semantics.

Follow the exact top-level payload contract in [artifact contracts](artifact-contracts.md).
