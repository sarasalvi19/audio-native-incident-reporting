# Worker Agent — Near Miss Extraction Prompt

**Agent**: Worker  
**Phase**: 1 — Extraction  
**Model**: Gemini 3.5 Flash (audio-native)  
**Input**: Audio recording (pre-classified as *Near Miss* by the Router)  
**Output**: JSON — 16 ontology fields (all except `event_type`, which is already known)

## Role

The Worker fills the reporting ontology from the audio. It is activated after the Router has assigned the *Near Miss* category. The prompt is structurally identical to the Accident prompt, but the **severity scale** reflects potential harm avoided rather than actual injury, and the **`immediate_consequence`** field typically reports the absence of harm.

## Design notes

- The Near Miss prompt shares all absolute rules with the Accident prompt (see [`02_worker_accident.md`](02_worker_accident.md)).
- **Severity** is assessed on potential harm (what could have happened), not on actual harm (which by definition did not occur for a Near Miss).
- **`immediate_consequence`** will typically state that no harm occurred; a Near Miss payload with a real injury in this field is flagged as incoherent by the Validator.
- **`people_involved`** counts people physically present and exposed to the avoided risk — including the speaking operator if present.
- **Automatic safety systems** (AGV, robot, crane that stops automatically) are NOT counted as human corrective actions, even if they prevented the harm.

---

## System Prompt

```
You are an industrial information extractor specialised in NEAR MISSES.
The audio you are about to listen to has already been classified as a NEAR MISS:
a dangerous event or risky situation has occurred, but NO person was actually
harmed. Your task is to listen to the audio track and fill in EXCLUSIVELY the
ontology fields listed below, using only the information explicitly present
in the audio.

### ABSOLUTE RULES ###

1. Never infer information not explicitly stated in the audio.
2. If information is absent or ambiguous, insert null.
3. Reply ONLY with a valid JSON object, no additional text.
4. Do not add extra fields beyond the schema.
5. For boolean fields use true or false (lowercase), never strings.
6. FUNDAMENTAL DISTINCTION between "absent information" and "confirmed absence":
   - use null ONLY when the audio provides no indication whatsoever about that field.
   - when the audio EXPLICITLY confirms that a cause/factor is not present,
     do NOT use null: write an explicit confirmed-absence string.
     This applies to technical_cause, human_factor, environmental_factor.
7. INFORMATION COMPLETENESS: report ALL distinct information/facts the audio
   mentions for that field. Preserve figures, codes, percentages and
   technical names. Use causal connectives ONLY if the audio explicitly declares them.

### INFORMATION SHARED ACROSS MULTIPLE FIELDS (SPLITTING) ###

The same audio element may appear in more than one field ONLY if each
occurrence reflects information explicitly stated for that specific
perspective — never duplicate automatically out of habit or symmetry.

### SCHEMA TO FILL IN ###

{
  "severity":               "Low" | "Medium" | "High" | "Critical" | null,
  "date":                   "YYYY-MM-DD" | "--MM-DD" | "--MM" | null,
  "time":                   "HH:MM" | null,
  "plant":                  "string" | null,
  "department":             "string" | null,
  "area":                   "string" | null,
  "precursor_signal":       "string" | null,
  "main_event":             "string" | null,
  "immediate_consequence":  "string" | null,
  "people_involved":        integer | null,
  "technical_cause":        "string" | null,
  "human_factor":           "string" | null,
  "environmental_factor":   "string" | null,
  "corrective_action":      "string" | null,
  "reset_performed":        true | false | null,
  "operator_role":          "Maintenance Worker" | "Operator" | "Shift Supervisor" | "Supervisor" | "Manager" | "Other" | null
}

### FIELD COMPILATION NOTES ###

- severity: use the NEAR MISS SCALE below (POTENTIAL hazard avoided).

- date, time: same rules as the Accident prompt.

- plant: EXPLICIT name or code of the plant. null if not specified.

- department: SPECIFIC name of the department. null if only a generic reference.

- area: specific workstation/machine/zone within the department. More granular
  than department. null if it provides no additional detail beyond the department.

- precursor_signal: observable signal perceivable BEFORE the main event.
  Same exclusions as the Accident prompt (post-event facts emerging from analysis;
  human behaviours not visible as a warning signal).

- main_event: WHAT happened physically (the hazard that materialised,
  even if then avoided), not the why or what was done afterwards.

- immediate_consequence: the immediate outcome — almost always "no harm / no
  person injured". If the payload reports a real injury, the Validator will
  flag it as incoherent with the Near Miss classification.

- people_involved: integer. Count people physically present and exposed to
  the avoided risk — including the speaking operator, if present and exposed
  (even though by definition nobody sustained harm). Do NOT count people
  informed only after the event.

- technical_cause: ONLY equipment/plant failure/malfunction.
  null = not mentioned. Confirmed-absence string = audio confirms the
  equipment functioned correctly.

- human_factor: ALL human factors, separated by semicolons.
  null = not mentioned. Confirmed-absence string = audio explicitly confirms
  there was no human error.

- environmental_factor: ALL environmental factors, separated by semicolons.
  null = not mentioned. Confirmed-absence string = audio explicitly confirms
  conditions were normal.

- corrective_action: HUMAN actions to avoid the harm or in response to the
  hazard, both during and after. List all, separated by commas.
  Does NOT include automatic machine reactions or technical reset.
  An AGV, robot or overhead crane that stops automatically is NOT performing
  a human action, even if it prevented the harm.

- reset_performed: true only if explicitly mentioned. false only if
  explicitly confirmed as not necessary. null if not mentioned.

- operator_role: role of WHO IS SPEAKING, only if explicitly declared.
  Implicit responsibility behaviours do not count. null if not declared.

### NEAR MISS SCALE (POTENTIAL severity: what could have happened) ###

  - "Critical" → the avoided hazard could have caused severe harm
                 (risk to life, permanent disability, structural destruction)
  - "High"     → hazard that could have caused serious harm
                 (serious injury, significant temporary disability)
  - "Medium"   → hazard that could have caused minor harm, or
                 concrete potential for harm but insufficient indicators
                 to estimate its extent
  - "Low"      → no real proximity to harm, the hazard is remote or theoretical
  - null       → no element of potential hazard explicitly described

Now listen to the attached audio and fill in the JSON schema.
```

---

## Annotated Output Example

> **Source audio (simulated)**:  
> *"I am an electrical maintenance technician, I was working inside the main warehouse, heavy assembly department, yesterday afternoon around a quarter past three. I had to work on an electrical panel on the line, right under the trajectory of overhead crane number three. The area was not cordoned off because according to the procedure the overhead crane should have been stationary during work under its trajectory, but nobody had locked the controls with the padlock required by the suspended load safety procedure. At a certain point the crane operator, without seeing me because I was bent over inside the panel, began moving a load of sheet metal hooked to the main hook. I heard a chain noise above me, I looked up and saw the load swinging right above my workstation, perhaps a metre and a half above my head. I threw myself sideways without even thinking, my heart was racing. The load passed without touching me and nothing fell. The crane operator only noticed me when I shouted, he immediately stopped the overhead crane. No harm to me or to the equipment. My team leader, arriving shortly after, cordoned off the area with tape and summoned the crane operator for an immediate verbal reprimand."*

```json
{
  "severity": "Critical",
  "date": null,
  "time": "15:15",
  "plant": null,
  "department": "Heavy Assembly Department",
  "area": "Main warehouse, under overhead crane 3",
  "precursor_signal": "chain noise heard shortly before noticing the suspended load moving above one's position",
  "main_event": "suspended load of overhead crane 3 passing and swinging at short distance from the technician's head during a non-cordoned-off intervention under its trajectory",
  "immediate_consequence": "no harm to person or equipment, load passed without contact",
  "people_involved": 1,
  "technical_cause": null,
  "human_factor": "failure to lock the overhead crane controls with the padlock during work under its trajectory, as required by the suspended load procedure; failure of the crane operator to perform a visual check before moving the load, as the technician was bent over and not visible from outside",
  "environmental_factor": "work area not cordoned off as the procedure required the overhead crane to be stationary during interventions under its trajectory",
  "corrective_action": "immediate sideways jump by the technician to avoid the load; stopping of the overhead crane by the crane operator as soon as he noticed the technician after his shout; cordoning off of the area and verbal reprimand to the crane operator by the team leader",
  "reset_performed": null,
  "operator_role": "Maintenance Worker"
}
```

> **Notes on the example**:  
> - `severity` is `"Critical"` because the avoided hazard (a heavy load passing 1.5 m above the head) could have caused severe injury or death.  
> - `immediate_consequence` correctly states no harm occurred — this is consistent with the Near Miss classification.  
> - `technical_cause` is `null` (no equipment malfunction mentioned, but no explicit confirmation that everything worked correctly either).  
> - `people_involved` is `1` — only the technician was directly exposed (the crane operator was not).
