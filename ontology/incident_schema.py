"""
incident_schema.py
==================
SQLAlchemy model for the industrial incident reporting ontology.

This schema is used as the shared structured output format across all agents
in the GenAI Multi-Agent System described in:

  Salvi et al. (2027). "From Industrial Audio to Structured Records:
  A GenAI Multi-Agent System for Accident and Near-Miss Reporting."
  Proceedings of ICIEA 2027.

The table stores extracted data for both "Accident" and
"Near Miss" events processed from industrial operator audio recordings.

Field groups
------------
  Identification  : event_id, date, time, event_type, severity
  Location        : plant, department, area
  Event dynamics  : precursor_signal, main_event, immediate_consequence,
                    people_involved
  Cause analysis  : technical_cause, human_factor, environmental_factor
  Response        : corrective_action, reset_performed, operator_role

Mandatory fields (always filled): severity, plant, department,
  main_event, immediate_consequence.
Optional fields (filled only when explicitly stated in the audio): all others.

No-inference rule
-----------------
  null  = information absent or not mentioned in the audio (triggers
          downstream recovery: audio re-listening, then operator interview)
  str   = either a stated value OR an explicitly confirmed absence
          (e.g. "No technical cause — system functioned correctly")

The distinction between null (unknown) and an absence string (confirmed absent)
is critical: null activates recovery pipelines, an absence string does not.

Severity scale
--------------
  ACCIDENT (based on actual injury):
    "Critica"  → serious injury, hospitalisation
    "Alta"     → injury requiring emergency care
    "Media"    → minor injury, on-site treatment
    "Bassa"    → minimal bruise/abrasion, no care needed
    null       → confirmed accident but severity not described

  NEAR MISS (based on potential harm avoided):
    "Critica"  → avoided risk could have caused severe harm (life risk,
                  permanent disability, structural damage)
    "Alta"     → avoided risk could have caused serious harm
    "Media"    → avoided risk could have caused minor harm, or concrete
                  potential without enough detail to estimate severity
    "Bassa"    → no real proximity to harm; described risk is remote
    null       → no potential hazard element explicitly described
"""

from sqlalchemy import (
    Boolean, Column, Integer, String, Text
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Incident(Base):
    """
    Stores structured records extracted from industrial audio reports of
    accidents and near-miss events.

    Every record is traceable to one or more source audio files and
    is linked to a run identifier that allows multiple processing passes
    of the same recording to be tracked and compared.
    """

    __tablename__ = "incidents"

    # -------------------------------------------------------------------------
    # Primary key
    # -------------------------------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # -------------------------------------------------------------------------
    # Pipeline metadata (populated by the Gatekeeper agent)
    # -------------------------------------------------------------------------

    event_id = Column(
        String(64),
        nullable=True,
        index=True,
        comment=(
            "System-generated identifier assigned by the Gatekeeper agent. "
            "Format: INF-YYYYMMDD-NNN for accidents, NM-YYYYMMDD-NNN for near misses. "
            "Shared across multiple audio reports of the same event."
        ),
    )

    run_id = Column(
        String(64),
        nullable=True,
        comment=(
            "Identifier of the processing run that produced this record. "
            "Allows multiple runs of the same audio to be tracked."
        ),
    )

    audio_file = Column(
        String(256),
        nullable=True,
        comment="Path or identifier of the source audio file.",
    )

    flag_revision = Column(
        Boolean,
        default=False,
        nullable=False,
        comment=(
            "True if the record has been flagged for human review by the "
            "Gatekeeper (e.g., mandatory field still empty after all recovery "
            "attempts, or low-confidence classification unresolved)."
        ),
    )

    # -------------------------------------------------------------------------
    # Identification fields
    # -------------------------------------------------------------------------

    event_type = Column(
        String(32),
        nullable=True,
        comment=(
            "Event category assigned by the Router agent. "
            "Allowed values: 'Accident' | 'Near Miss'. "
            "Out-of-scope recordings do not produce a record."
        ),
    )

    severity = Column(
        String(32),
        nullable=True,
        comment=(
            "Severity level. Scale differs by event_type. "
            "ACCIDENT: Critica (hospitalisation) | Alta (emergency care) | "
            "Media (on-site treatment) | Bassa (no care needed) | null (not described). "
            "NEAR MISS: Critica (risk to life/permanent disability) | "
            "Alta (serious potential harm) | Media (minor potential harm) | "
            "Bassa (remote risk) | null (no hazard element described). "
            "This field requires an assessment and is therefore always filled "
            "if any indicator is present."
        ),
    )

    date = Column(
        String(10),
        nullable=True,
        comment=(
            "Event date. Format: YYYY-MM-DD (full date), --MM-DD (month+day, "
            "no year), --MM (month only). null if no date element is stated. "
            "Never inferred from context."
        ),
    )

    time = Column(
        String(5),
        nullable=True,
        comment=(
            "Event time in HH:MM (24-hour). null if not explicitly stated. "
            "Only a declared time or unambiguous moment (e.g. 'at noon' → '12:00') "
            "is accepted; never estimated from indirect cues."
        ),
    )

    # -------------------------------------------------------------------------
    # Location fields
    # -------------------------------------------------------------------------

    plant = Column(
        String(128),
        nullable=True,
        comment=(
            "Name or code of the plant/site, explicitly stated in the audio. "
            "null if the plant is not specifically identified."
        ),
    )

    department = Column(
        String(128),
        nullable=True,
        comment=(
            "Name or specific identifier of the department or production line. "
            "Generic references ('the department', 'the area') without a specific "
            "name are not stored here: null instead."
        ),
    )

    area = Column(
        String(256),
        nullable=True,
        comment=(
            "Specific workstation, machine, line or zone within the department — "
            "a finer spatial level than 'department'. Do not repeat the department "
            "or plant name. Multiple references separated by comma."
        ),
    )

    # -------------------------------------------------------------------------
    # Event dynamics fields
    # -------------------------------------------------------------------------

    precursor_signal = Column(
        Text,
        nullable=True,
        comment=(
            "Observable anomaly (sight/hearing/smell) perceivable BEFORE the "
            "main event that could have signalled a risk. Excludes: post-event "
            "technical findings; human behaviours/procedure violations that are "
            "not in themselves perceptible warning signals."
        ),
    )

    main_event = Column(
        Text,
        nullable=True,
        comment=(
            "Central fact of the event — WHAT happened physically/operationally, "
            "in a concise but complete sentence. Excludes causes and consequences."
        ),
    )

    immediate_consequence = Column(
        Text,
        nullable=True,
        comment=(
            "Direct and immediate effect of the event on the person involved. "
            "For Near Miss: typically 'no injury/damage' or describes the harm avoided. "
            "A Near Miss with a real injury in this field is flagged as incoherent."
        ),
    )

    people_involved = Column(
        Integer,
        nullable=True,
        comment=(
            "Integer count of people physically present and directly exposed to "
            "the risk at the time and place of the event. Includes the speaking "
            "operator if present. Excludes people informed only after the event."
        ),
    )

    # -------------------------------------------------------------------------
    # Cause analysis fields
    # -------------------------------------------------------------------------

    technical_cause = Column(
        Text,
        nullable=True,
        comment=(
            "Mechanical, electrical or electronic failure/malfunction only. "
            "null = not mentioned (triggers recovery). "
            "Explicit absence string = confirmed by audio that equipment functioned "
            "correctly (does NOT trigger recovery). "
            "Multi-step technical chains are reported in sequence."
        ),
    )

    human_factor = Column(
        Text,
        nullable=True,
        comment=(
            "All human factors (behaviours, omissions, procedure violations), "
            "including those of the injured person. Separated by semicolons. "
            "null = not mentioned. Explicit absence string = confirmed absent."
        ),
    )

    environmental_factor = Column(
        Text,
        nullable=True,
        comment=(
            "All physical/environmental conditions that contributed "
            "(visibility, noise, lighting, floor conditions, chemical agents, etc.). "
            "Separated by semicolons. "
            "null = not mentioned. Explicit absence string = confirmed absent."
        ),
    )

    # -------------------------------------------------------------------------
    # Response fields
    # -------------------------------------------------------------------------

    corrective_action = Column(
        Text,
        nullable=True,
        comment=(
            "Human decisions or actions taken during or immediately after the "
            "event: physical/organisational mitigation, first aid, reporting. "
            "Multiple actions separated by comma. "
            "Excludes automatic machine reactions and technical resets "
            "(see reset_performed)."
        ),
    )

    reset_performed = Column(
        Boolean,
        nullable=True,
        comment=(
            "True = audio explicitly mentions technical restart/re-arming of a "
            "system, alarm, machine or line. "
            "False = audio explicitly confirms no reset was needed/performed. "
            "null = topic not mentioned."
        ),
    )

    operator_role = Column(
        String(64),
        nullable=True,
        comment=(
            "Role of the SPEAKER (the person reporting the audio), not of other "
            "people mentioned. Filled only if the speaker explicitly declares "
            "their own role. "
            "Allowed values: Manutentore | Operatore | Capo turno | Supervisore | "
            "Responsabile | Altro. "
            "Implicit responsibility signals do NOT count. Undeclared = null."
        ),
    )

    # -------------------------------------------------------------------------
    # Pipeline telemetry (populated by the Gatekeeper agent)
    # -------------------------------------------------------------------------

    missing_fields = Column(
        Text,
        nullable=True,
        comment=(
            "JSON list of mandatory fields that remained null after all recovery "
            "attempts (Validator re-listening + Interviewer questions). "
            "Used by the Gatekeeper to decide whether to flag the record."
        ),
    )

    tokens_in = Column(
        Integer,
        nullable=True,
        comment="Total input tokens consumed by all agents for this run.",
    )

    tokens_out = Column(
        Integer,
        nullable=True,
        comment="Total output tokens produced by all agents for this run.",
    )

    def __repr__(self) -> str:
        return (
            f"<Incident id={self.id!r} event_id={self.event_id!r} "
            f"event_type={self.event_type!r} severity={self.severity!r}>"
        )
