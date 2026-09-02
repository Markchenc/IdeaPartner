# IdeaPartner Case Suite

This directory contains researcher-facing diagnostic cases for evaluating the
research-idea-review skill. The first suite is deliberately small: four
cross-domain cases plus one case derived from an active research project.

The suite is designed for manual evaluation. It does not define a numeric idea
quality score or a single correct final verdict. Instead, every case records the
review behaviors that should become visible if positioning, domain grounding,
maturity conditioning, contribution conditioning, and the M5 dependency chain
are working as intended.

## Case matrix

| ID | Domain | Maturity | Primary contribution | Main capability under test |
|---|---|---|---|---|
| 01 | HCI / AI-assisted writing | early | HCI/design research | Early-stage framing without premature method demands |
| 02 | Machine learning / multimodal RL | middle | method/algorithm | Closest-work collision and contribution boundary |
| 03 | Computer vision / vision-language evaluation | developed | dataset/benchmark | Benchmark-conditioned review and construct validity |
| 04 | AI infrastructure / LLM serving | developed | system/AI infrastructure | End-to-end value, cost transfer, and workload validity |
| 05 | Dialogue NLP / personality recognition | developed | method/algorithm | Full-chain review on a real research direction |

## Files in each case

- `idea.md`: the only case material supplied at M0.
- `case.yaml`: evaluation metadata. Do not provide it to the M1 worker.
- `researcher-confirmation.md`: the simulated researcher response shown only
  after M1 has been presented. If its corrections differ from M1, update and
  replace M1 before proceeding.
- `expected-review-behavior.md`: a private manual-evaluation reference. Never
  include it in a worker packet or prompt.

## Evaluation protocol

1. Start a fresh run from `idea.md`.
2. Inspect the generated M1 before opening the other case files.
3. At the checkpoint, provide `researcher-confirmation.md` as the researcher's
   response. Apply any stated correction to M1 and wait for the refreshed card
   to be confirmed when necessary.
4. Complete M2 through M7 with live evidence verification.
5. Only after the final report is produced, compare the run with
   `expected-review-behavior.md` and record a manual assessment.

The metadata and expected behaviors are intentionally excluded from runtime
inputs. This prevents answer leakage and keeps the cases useful for diagnosing
semantic failures rather than testing whether a model can repeat a rubric.

## Interpretation boundary

Passing these five cases shows that the workflow exhibits several intended
review behaviors under controlled examples. It does not establish that the
skill outperforms expert peer review. Stronger claims would require blinded
expert comparison, repeated runs across models, and a larger independently
authored case set.
