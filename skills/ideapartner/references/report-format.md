# Stage 3: reconstruction, fidelity check and final report

Read the original input, short plan, current review and supplied evidence view. It includes counterevidence as well as support. Verify the review is about the original claim; inspect decisive source passages when necessary. Do not redo general retrieval.

Return structured_idea with six provenance-labelled sections, assessment covering the four dimensions, one decision, recommendations and limitations. Use language zh or en for heading localization. Keep recommendations separate from the original idea. No scores or acceptance prediction.

Each report block has text, judgment_ids and evidence_refs. Cite evidence near the scientific claim, including important contrary evidence and limits. Do not introduce a new unreviewed source to support the final result; request targeted recheck when it would change the conclusion.

Submit structured data only. The renderer creates Markdown and citations; do not also author an equivalent full report_markdown. Present the main conclusion once, then the structured idea, dimensional review and actions.

For a material gap submit recheck_request (question_id, reason, affected_judgment_ids, needed_evidence) instead of final payload. At the recheck or time limit, narrow the claim, explain missing evidence and finish. Do not claim the Python validator proves semantic truth.
