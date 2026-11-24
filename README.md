# From Industrial Audio to Structured Records: A GenAI Multi-Agent System for Accident and Near-Miss Reporting

[![Conference](https://img.shields.io/badge/Conference-ICIEA%202027-blue)](https://www.iciea.eu/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](https://opensource.org/licenses/MIT)

This repository contains the reporting ontology and the agent prompts developed for the paper cited below. The system interprets operator audio directly — without transcription — and produces structured accident and near-miss records traceable to their sources. For the full architecture, evaluation and results, please refer to the paper.

> **From Industrial Audio to Structured Records: A GenAI Multi-Agent System for Accident and Near-Miss Reporting**  
> Sara Salvi, Silvia Colabianchi, Sara Chiappini, Francesco Costantino, Nicolò Sabetta  
> In *Advances in Industrial Engineering: Proceedings of the 14th International Conference on Industrial Engineering and Applications (Europe) — ICIEA 2027*  
> Lecture Notes on Multidisciplinary Industrial Engineering, Springer Nature  
> Department of Computer, Control, and Management Engineering Antonio Ruberti, Sapienza University of Rome, Italy  
> Department of Engineering and Science, Universitas Mercatorum, Rome, Italy

---

## Repository Contents

```
├── README.md                        ← This file
├── CITATION.cff                     ← Machine-readable citation
├── LICENSE                          ← MIT License
├── ontology/
│   ├── incident_schema.json         ← Field definitions, admissible values and synonyms (JSON)
│   └── incident_schema.py           ← SQLAlchemy model (Python)
└── prompts/
    ├── README.md                    ← Prompt design notes
    ├── 01_router.md                 ← Router
    ├── 02_worker_accident.md        ← Worker — Accident prompt
    ├── 03_worker_near_miss.md       ← Worker — Near Miss prompt
    ├── 04_explorer.md               ← Explorer
    ├── 05_validator_semantic.md     ← Validator — Semantic judge
    ├── 06_validator_recovery.md     ← Validator — Audio recovery steps
    ├── 07_reconciler.md             ← Reconciler
    ├── 08_interviewer.md            ← Interviewer
    └── 09_analyst.md                ← Analyst
```

The Gatekeeper is deterministic and has no prompt.

---

## Ontology

The reporting ontology is a fixed schema of **17 fields** with their admissible values and synonyms, shared by the *Accident* and *Near Miss* categories.

| Group | Fields |
|-------|--------|
| **Identification** | `event_type`, `severity`, `date`, `time` |
| **Location** | `plant`, `department`, `area` |
| **Event dynamics** | `precursor_signal`, `main_event`, `immediate_consequence`, `people_involved` |
| **Cause analysis** | `technical_cause`, `human_factor`, `environmental_factor` |
| **Response** | `corrective_action`, `reset_performed`, `operator_role` |

`event_type` is set by the Router. Five fields are mandatory (`severity`, `plant`, `department`, `main_event`, `immediate_consequence`) and are filled by the Worker; the remaining eleven are optional. See [`ontology/`](ontology/) for the full schema.

---

## Agents

| # | Agent | Type | Prompt file |
|---|-------|------|-------------|
| 1 | Router | LLM | [`01_router.md`](prompts/01_router.md) |
| 2 | Worker | LLM | [`02_worker_accident.md`](prompts/02_worker_accident.md), [`03_worker_near_miss.md`](prompts/03_worker_near_miss.md) |
| 3 | Explorer | LLM | [`04_explorer.md`](prompts/04_explorer.md) |
| 4 | Validator | LLM | [`05_validator_semantic.md`](prompts/05_validator_semantic.md), [`06_validator_recovery.md`](prompts/06_validator_recovery.md) |
| 5 | Reconciler | LLM + deterministic | [`07_reconciler.md`](prompts/07_reconciler.md) |
| 6 | Interviewer | LLM | [`08_interviewer.md`](prompts/08_interviewer.md) |
| 7 | Gatekeeper | Deterministic | — |
| 8 | Analyst | LLM | [`09_analyst.md`](prompts/09_analyst.md) |

For the role, activation mode and design rationale of each agent, see the paper and [`prompts/README.md`](prompts/README.md).

---

## Citation

If you use this ontology or these prompts in your work, please cite:

```bibtex
@inproceedings{salvi2027audiomas,
  title     = {From Industrial Audio to Structured Records: A GenAI Multi-Agent System for Accident and Near-Miss Reporting},
  author    = {Salvi, Sara and Colabianchi, Silvia and Chiappini, Sara and Costantino, Francesco and Sabetta, Nicol{\`o}},
  booktitle = {Advances in Industrial Engineering: Proceedings of the 14th International Conference on Industrial Engineering and Applications (Europe)},
  series    = {Lecture Notes on Multidisciplinary Industrial Engineering},
  publisher = {Springer Nature},
  year      = {2027},
  address   = {Rome, Italy}
}
```

A machine-readable citation is available in [`CITATION.cff`](CITATION.cff). Once the paper is published, update the BibTeX entry and `CITATION.cff` with volume, page numbers and DOI, and add:

```
  note = {First published in [Volume, page number, 2027] by Springer Nature. https://doi.org/[DOI]}
```

---

## Authors

- **Sara Salvi** — Sapienza University of Rome ([ORCID: 0009-0007-4704-4835](https://orcid.org/0009-0007-4704-4835))
- **Silvia Colabianchi** — Universitas Mercatorum ([ORCID: 0000-0002-1811-8619](https://orcid.org/0000-0002-1811-8619))
- **Sara Chiappini** — Sapienza University of Rome
- **Francesco Costantino** — Sapienza University of Rome ([ORCID: 0000-0002-0942-821X](https://orcid.org/0000-0002-0942-821X))
- **Nicolò Sabetta** — Sapienza University of Rome ([ORCID: 0009-0009-0653-455X](https://orcid.org/0009-0009-0653-455X))

**Contact**: sara.salvi@uniroma1.it  
**Sapienza University of Rome**: DIAG — Department of Computer, Control, and Management Engineering Antonio Ruberti, Via Ariosto 25, Rome, 00185, Italy  
**Universitas Mercatorum**: Department of Engineering and Science, Piazza Mattei 10, Rome, 00186, Italy

---

## License and Copyright

### Repository contents (ontology and prompts)

The ontology and prompts in this repository are independent research artifacts released by the authors under the [MIT License](https://opensource.org/licenses/MIT). See the [`LICENSE`](LICENSE) file for the full licence text.

© 2026 Sapienza University of Rome, Universitas Mercatorum, Sara Salvi, Silvia Colabianchi, Sara Chiappini, Francesco Costantino, Nicolò Sabetta

### Associated paper

The paper *From Industrial Audio to Structured Records: A GenAI Multi-Agent System for Accident and Near-Miss Reporting* is accepted for publication by **Springer Nature** in *Advances in Industrial Engineering — Proceedings of the 14th International Conference on Industrial Engineering and Applications (Europe) — 2027* (Lecture Notes on Multidisciplinary Industrial Engineering). The manuscript is **not** part of this repository. Copyright in the paper is vested in the authors; Springer Nature holds exclusive publishing rights.

**When reproducing the Version of Record or extracts from it**, include the acknowledgement required by the publisher:
> *"First published in [Volume, page number, year] by Springer Nature"*

**When reusing the paper in a thesis**, add:
> *"Reproduced with permission from Springer Nature"*

**When sharing or posting the Accepted Manuscript**, include the following disclaimer as required by Springer Nature:
> *"This version of the contribution has been accepted for publication, after peer review but is not the Version of Record and does not reflect post-acceptance improvements, or any corrections. The Version of Record is available online at: http://dx.doi.org/[insert DOI]. Use of this Accepted Version is subject to the publisher's Accepted Manuscript terms of use https://www.springernature.com/gp/open-research/policies/accepted-manuscript-terms"*

The Accepted Manuscript may be posted on a personal or institutional website immediately upon acceptance. Public release on institutional or funder repositories is permitted after a **12-month embargo** from the date of first publication.
