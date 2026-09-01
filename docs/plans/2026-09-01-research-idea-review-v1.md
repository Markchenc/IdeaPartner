# Research Idea Review V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a researcher-facing Codex skill that positions a research idea, constructs a targeted field prior, reconstructs the idea, and evaluates it through a maturity- and contribution-conditioned dependency chain.

**Architecture:** The repository hosts multiple skills under `skills/`. V1 is an instruction-only skill with a concise entrypoint and progressively loaded references for positioning, domain-prior construction, idea reconstruction, the M5 review chain, and final synthesis. The skill pauses after M1 for researcher confirmation and exposes only M4, M5, and M7 in the final report.

**Tech Stack:** Markdown skill instructions, YAML UI metadata, Git, Codex skill validator.

---

### Task 1: Record the V1 architecture decision

**Files:**
- Create: `docs/adr/0001-position-first-single-review.md`

**Steps:**
1. Document the problem, chosen workflow, alternatives, trade-offs, and failure behavior.
2. Verify that the ADR distinguishes positioning, prior construction, idea reconstruction, review, and synthesis.

### Task 2: Create the skill entrypoint and UI metadata

**Files:**
- Create: `skills/research-idea-review/SKILL.md`
- Create: `skills/research-idea-review/agents/openai.yaml`

**Steps:**
1. Define precise discovery text and exclusions.
2. Encode the fixed M0–M7 workflow and the mandatory M1 confirmation checkpoint.
3. Route conditional details to supporting references.
4. Keep automatic invocation enabled and add a researcher-facing default prompt.

### Task 3: Implement positioning, routing, and domain-prior guidance

**Files:**
- Create: `skills/research-idea-review/references/positioning-and-routing.md`
- Create: `skills/research-idea-review/references/domain-prior.md`

**Steps:**
1. Define the structured M1 positioning card and human confirmation behavior.
2. Define M2 maturity calibration and review-route selection without performing the final review.
3. Define M3 as a historical evolution tree plus foundation, data/infrastructure, and frontier/practice layers.
4. Add stopping, uncertainty, citation, and material-repositioning rules.

### Task 4: Implement idea reconstruction and the conditioned M5 chain

**Files:**
- Create: `skills/research-idea-review/references/idea-reconstruction.md`
- Create: `skills/research-idea-review/references/review-chain.md`

**Steps:**
1. Define the six-section M4 researcher-facing idea representation.
2. Preserve the distinction between user-stated, evidence-supported, inferred, and missing content.
3. Compile contribution type, maturity, and field evidence norms into every M5 task.
4. Implement M5-A/B in parallel, M5-C dependent on A/B, and M5-D dependent on C.
5. Define evidence, abstention, gate, conflict, and lightweight M6 challenge behavior.

### Task 5: Implement final synthesis and repository documentation

**Files:**
- Create: `skills/research-idea-review/references/report-format.md`
- Create: `README.md`

**Steps:**
1. Define the final report as M4 structured idea, M5 review, and M7 synthesis.
2. Prohibit weighted totals, venue acceptance prediction, and unsupported completion of missing idea content.
3. Explain repository purpose, current V1 scope, layout, and use.

### Task 6: Validate, review, commit, and publish

**Files:**
- Inspect all created files.

**Steps:**
1. Run the bundled Codex skill validator against `skills/research-idea-review`.
2. Check all local Markdown reference links resolve.
3. Review the diff for duplicated instructions and accidental scope expansion.
4. Commit the completed V1 implementation on `main` with a focused message.
5. Push the commit to `origin/main`.
