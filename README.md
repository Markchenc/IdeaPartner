# IdeaPartner

IdeaPartner is a collection of skills for the first mile of research: positioning, examining, and eventually developing research ideas before they become full proposals or papers.

## Current implementation

V1 provides a single-review skill at [`skills/research-idea-review`](skills/research-idea-review/SKILL.md). It:

1. structures and confirms the idea's field, scenario, research object, difficulty, contribution type, and maturity;
2. compiles a review route;
3. builds a historical evolution tree and layered field prior;
4. reconstructs the idea into six researcher-facing sections;
5. reviews it through a contribution- and maturity-conditioned dependency chain;
6. performs a small number of targeted challenges;
7. returns the structured idea, evidence-grounded review, and overall decision guidance.

The skill deliberately avoids a single quality score, paper-acceptance prediction, and autonomous completion of missing idea content.

## Repository layout

```text
skills/
  research-idea-review/
    SKILL.md
    agents/openai.yaml
    references/
docs/
  adr/
  plans/
```

The planned V2 continuous companion will build on lessons from V1 after the single-review workflow has been exercised and revised.

## Use

Load or install the `research-idea-review` skill in a compatible Codex environment, then provide one research idea in natural language. The skill first returns a structured positioning card and waits for researcher confirmation before beginning literature-grounded review.
