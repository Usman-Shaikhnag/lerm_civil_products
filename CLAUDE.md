# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

AGENTS.md (imported above) is the primary guide: repo layout, commands, gotchas, and the production deploy procedure. Keep shared guidance there so other agents see it too. This file only adds the cross-module wiring that AGENTS.md leaves out.

## How a test flows from SRF to a material module

- The flow is SRF (`lerm.civil.srf`) → Sample (`lerm.srf.sample`) → ELN (`lerm.eln`), all in `lerm_civil/models/`. The ELN is where a technician enters results.
- An ELN does not import any material module. It finds the form to open at runtime: `material.product_based_calculation` (a `product.template` line filtered by `grade_id`) holds an `ir_model`. The ELN opens that model with `default_eln_ref`, `default_sample_id` and `default_srf_id` in the context, and stores the created record's id in `model_id` (see the open-calculation action in `lerm_civil/models/eln.py`). Per-parameter forms work the same way through `lerm.parameter.master.ir_model` and `eln.parameters.result.model_id`.
- So a new material model only becomes reachable after it is linked to a product/grade record (or a parameter master) through `ir_model`. That link is master data in the DB, not code.
- Material models (e.g. `mechanical.cement.normalconsistency` in `cement_opc/models/opc.py`) set `_inherit = "lerm.eln"` and keep an `eln_ref` back-pointer. Conformity and NABL computes look up limits with `lerm.parameter.master` searched by a **hardcoded `internal_id` UUID** and read `parameter_table` for the current grade. Those UUIDs must exist in the target DB's parameter master records, so copying a module between databases can silently break the computes.
- `lerm.parameter.master` also points to the report actions (`main_report_template`, `datasheet_report_template`). That is how an ELN picks which QWeb report a module prints.

## Agent skills

### Issue tracker

Issues live as local markdown files under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), recorded as a `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` + `docs/adr/` at the repo root (created lazily). See `docs/agents/domain.md`.
