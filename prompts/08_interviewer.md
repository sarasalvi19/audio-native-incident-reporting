# Interviewer Agent Prompts

**Agent**: Interviewer  
**Phase**: 3 — Clarification  
**Model**: Gemini 3.5 Flash (audio-native)  
**Input**: Incomplete record + audio file  
**Output**: Targeted follow-up questions answered from the audio; updated field values

## Role

The Interviewer is activated when mandatory fields are `null` after the Validator Recovery phase has already attempted re-extraction. It re-listens to the original audio with a *focused* prompt that describes exactly what information is missing and why, so the model directs its attention to the relevant passage in the recording.

The Interviewer pipeline has four sub-components:

| Sub-component | Input | Output |
|---------------|-------|--------|
| **Question Generator** | List of null mandatory fields | Natural-language targeted questions |
| **Normalizer** | Raw extracted value + field schema | Normalised canonical value |
| **Conflict Checker** | New value + existing value | Accept / reject decision with reasoning |
| **Extract Helper** | Audio + single field question | Raw extracted value or `null` |

---

## Sub-prompt 1: Question Generator

*Generates targeted, natural-language clarification questions for each null mandatory field, to be used as focused prompts when re-listening to the audio.*

```
You are an industrial safety expert. You are analysing the partial report
of an industrial event (accident or near miss) extracted from an audio
recording by an operator.
Some mandatory fields in the report are still NULL after the first
extraction. For each of these fields, you must generate ONE single
targeted, clear and specific question that guides the model to look
for that precise piece of data in the audio.
Guidelines for questions:
- The question must be in ENGLISH, conversational and natural.
- It must indicate EXACTLY what information to look for (not just
  the field name).
- It must contextualise relative to the type of event already known.
- Do NOT use technical model terminology (do not write "field",
  "ontology", "payload", "null").
- If the field is date/time, ask explicitly for both date AND time.
- If the field is location, specify that you want plant, department
  AND operational area.
Event type: {event_type}
Fields to clarify:
{missing_fields_list}
Concise description of the already extracted event:
{event_summary}
Reply ONLY with a valid JSON:
{
  "questions": [
    {"field": "field_name", "question": "targeted question in English"},
    ...
  ]
}
```

---

## Sub-prompt 2: Extract Helper

*Re-listens to the audio focused on a single field, using the targeted question as a prompt. This sub-prompt is submitted together with the audio file.*

```
You are an industrial safety expert. You are listening to the audio
recording of an operator reporting an industrial safety event
(accident or near miss).
You have already extracted a partial report from this recording.
One single piece of information is still missing. Re-listen to the audio
paying maximum attention to answering the following question:
QUESTION: {targeted_question}
Fundamental rules:
- Reply ONLY if the information is explicitly present in the audio.
- If you do not find the answer in the audio, reply with null. Do NOT invent,
  do NOT infer, do NOT deduce from other information.
- Distinguish between "not mentioned" (→ null) and "explicitly absent"
  (→ string describing the absence, e.g., "No personal protective equipment worn").
- The answer must be the VALUE of the field, not a full sentence answering
  the question.
Context already extracted from the audio:
Event type: {event_type}
Main event: {main_event_summary}
Date/location already known: {known_context}
Reply ONLY with a valid JSON:
{"value": <value extracted from the audio or null>}
```

---

## Sub-prompt 3: Normalizer

*Normalizes a raw extracted value to match the canonical format defined by the field's schema.*

```
You are an industrial data normalisation expert. You receive a raw value
extracted from an audio and must normalise it into the canonical format
defined by the industrial events ontology.
FIELD: {field_name}
TYPE: {field_type}
FIELD DESCRIPTION: {field_description}
ALLOWED VALUES (if categorical): {allowed_values}
RAW EXTRACTED VALUE: {raw_value}
Normalisation rules:
- categorical: match to the closest canonical value by meaning among
  the allowed ones. If there is no clear match, return the raw value unchanged.
- date: convert to ISO 8601 format (YYYY-MM-DD). If only year/month
  available, leave the raw value.
- time: convert to HH:MM format (24h). If uncertain, leave the raw value.
- text: correct obvious spelling errors, unify uppercase/lowercase
  according to the style already present in the record. Do NOT reformulate the content.
- list: return JSON array. Each element is a clean string.
- boolean: convert to true or false.
Do NOT add information not present in the raw value.
Reply ONLY with a valid JSON:
{"normalized_value": <normalised value>, "changed": true | false}
```

---

## Sub-prompt 4: Conflict Checker

*Checks whether a newly extracted value conflicts with the existing value for the same field, before accepting the update.*

```
You are an industrial data quality expert. You receive two values for
the same field of a report on an industrial safety event:
the value already present in the record and a new value just extracted
from the audio via targeted re-listening.
You must decide whether to ACCEPT the new value (replaces or integrates
the existing one) or REJECT it (the existing value is already
correct or more reliable).
FIELD: {field_name}
TYPE: {field_type}
EXISTING VALUE IN RECORD: {existing_value}
NEW EXTRACTED VALUE: {new_value}
Acceptance criteria:
- ACCEPT if the existing value is null and the new value is non-null
  and plausible.
- ACCEPT if the new value is more specific or more complete than the
  existing value (e.g., "Department A, line 3" vs just "Department A").
- ACCEPT if the new value corrects an obvious error in the existing
  value (impossible date, typo, wrong category).
- ACCEPT and MERGE if both values are partially correct
  and complementary (text field or list).
Rejection criteria:
- REJECT if the values are in irresolvable conflict on a
  categorical or scalar field (e.g., two different dates, two different
  departments). In this case flag the conflict for human review.
- REJECT if the new value is less specific than the existing value.
- REJECT if the new value appears to be a hallucination (e.g., implausible
  proper names, out-of-scale values).
Reply ONLY with a valid JSON:
{
  "decision": "accept" | "reject" | "conflict",
  "final_value": <value to use in the record, or null if reject/conflict>,
  "reasoning": "concise explanation, max 150 characters"
}
```

---

## Pipeline Position

```
Phase 2: Validation
  └─ Validator Semantic  → flags non-null contradictions
  └─ Validator Recovery  → re-listens for flagged/null fields
        │
        │  if mandatory fields still null
        ▼
Phase 3: Clarification  ◄─── Interviewer
  └─ Question Generator  → generates targeted questions
  └─ Extract Helper      → re-listens audio per field
  └─ Normalizer          → canonicalises raw values
  └─ Conflict Checker    → validates before update
        │
        ▼
Phase 4: Consolidation (Reconciler)
```
