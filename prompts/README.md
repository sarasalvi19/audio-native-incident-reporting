# Prompt Library

This directory contains the system and user prompts for all LLM agents in the Multi-Agent System. All LLM agents run on the audio-native **Gemini 3.5 Flash**. The Gatekeeper is deterministic and has no prompt.

## Agent–prompt mapping

| File | Agent | Phase | Input | Output |
|------|-------|-------|-------|--------|
| [`01_router.md`](01_router.md) | Router | Extraction | Audio only (no metadata) | JSON: event category (Accident / Near Miss / Out of Scope) + confidence |
| [`02_worker_accident.md`](02_worker_accident.md) | Worker | Extraction | Audio (classified as Accident) | JSON: 16 ontology fields |
| [`03_worker_near_miss.md`](03_worker_near_miss.md) | Worker | Extraction | Audio (classified as Near Miss) | JSON: 16 ontology fields |
| [`04_explorer.md`](04_explorer.md) | Explorer | Extraction | Audio + Worker output + ontology fields and synonyms | JSON: wildcard fields (name, value, priority) |
| [`05_validator_semantic.md`](05_validator_semantic.md) | Validator (semantic judge) | Validation | JSON payload | JSON: flagged fields with explanation and suggested correction |
| [`06_validator_recovery.md`](06_validator_recovery.md) | Validator (recovery steps) | Validation | Audio + JSON payload + flag or empty mandatory field | JSON: corrected / recovered value, or unresolved with explanation |
| [`07_reconciler.md`](07_reconciler.md) | Reconciler | Validation | New record + candidate stored record (from deterministic SQL prefilter) | JSON: same-event judgement + new information |
| [`08_interviewer.md`](08_interviewer.md) | Interviewer | Clarification | Unresolved fields (with Validator explanation) + operator answer | JSON: question / normalised value |
| [`09_analyst.md`](09_analyst.md) | Analyst | Querying | NL question + DB schema | SQL query / report / dashboard indicators |

## Prompt design principles

### Classification (Router)

The Router listens to the audio alone, without metadata. It classifies the report from both the content and cues such as tone, pauses and background noise. Out-of-scope recordings stop the pipeline without creating a record. When the audio is ambiguous or degraded, the Router picks the most likely category, flags it as low confidence and asks the operator to confirm it.

### Category-specific extraction (Worker)

The category assigned by the Router determines which Worker prompt is used, because some criteria differ between the two categories. For accidents, `severity` measures the harm suffered. For near misses, it measures the harm avoided. `event_type` is set by the Router; the Worker fills the remaining 16 fields.

### No-inference rule (Worker)

Both Worker prompts enforce a strict no-inference rule: the agent leaves fields **null** rather than infer values the speaker did not state. Facts are linked causally only when the speaker does so.

This is intentional. A `null` activates downstream recovery:
1. the Validator re-listens to the audio;
2. the Reconciler looks for the information in stored records of the same event;
3. the Interviewer asks the operator targeted questions.

A wrongly inferred value would instead skip recovery and could only be caught if the Validator flagged it as inconsistent.

There are two exceptions: `severity` and `people_involved`. They require an assessment or a count rather than a stated value, so they are **always filled**. `operator_role`, by contrast, is filled only when the speaker states it.

### Null vs. confirmed absence

A key distinction runs through all prompts:

- **`null`** = the information was not mentioned. We do not know; it may exist but was not stated. This triggers recovery.
- **Explicit absence string** (e.g., `"No technical cause identified — system functioned correctly"`) = the audio explicitly confirms that a factor was absent. This does **not** trigger recovery.

This ensures that only genuinely missing fields are recovered downstream. It is critical for `technical_cause`, `human_factor` and `environmental_factor`.

### Open-ended exploration (Explorer)

The Explorer searches the audio for relevant information that the ontology does not cover. Its prompt lists all ontology fields with their synonyms, and it receives the Worker's output, so it reports only what the Worker could not capture. The prompt deliberately contains **no examples**: examples would act as a second ontology and limit the agent's freedom to propose new fields. Each wildcard field (name, value, priority) is stored in a dedicated column without altering the database schema.

### Cross-agent verification (Validator)

The semantic judge flags contradictions **within and between** fields of the payload, using category-specific criteria. It never flags `null` values.

Two recovery steps then re-listen to the audio:
1. one for each flagged field, treating the judge's suggestion as a hypothesis to verify rather than a correction to apply;
2. one for each **empty mandatory** field.

Fields that remain unresolved keep the judge's explanation, which is passed on to the Interviewer.

### Matching stored records (Reconciler)

The Reconciler runs before the Interviewer, so that the operator is not asked again for information already stored for the same event. A deterministic SQL prefilter selects candidate records that match on plant, department, date and event type, ignoring fields that are empty on either side. The judge then decides whether each candidate describes the same event and whether the new record adds information. Whether to discard, merge or keep both records is a human decision.

### Targeted clarification (Interviewer)

The Interviewer runs only if mandatory fields remain empty or inconsistencies remain unresolved. It asks the operator involved at most **3 natural-language questions** per run, starting from the central fact of the event and naming the specific contradiction when relevant. Questions use natural language, not database field names. Each answer is normalised to its field and checked against the other fields; any new conflict is left to the operator to resolve.

### Natural language querying (Analyst)

The Analyst runs on request, outside the reporting pipeline. It answers natural language questions through text-to-SQL over the stored records, generates reports and feeds a dashboard of key indicators. This agent was not evaluated in the paper (C5).