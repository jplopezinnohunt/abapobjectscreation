---
# Bus header — contract C-4 v1.1 (sole owner: C0). Derived from the prose below; nothing invented.
msg_type: REQUEST
request_id: v01_pa0105_subty0001
from_project: unescrp                 # "(CRP app - test-case builder, S-178)"
date: 2026-07-03
status: OPEN                          # no DONE_v01_pa0105_subty0001.md on disk as of 2026-07-25
system_role: V01
why: "v01_pa0105 holds only SUBTY='0010' (email); there is no PERNR -> SAP logon user (BNAME) mapping, so no golden employee can be gated on having a SAP user or resolved as the step-01 workflow actor."
resource_requested: "Re-extract PA0105 for V01 including SUBTY='0001' (system user name) alongside the existing 0010, and re-land v01_pa0105 in v01_gold_master_data.db"
extract_spec:
  - source_table: PA0105
    keys: [PERNR, SUBTY, USRID]       # for subty 0001 the value lands in USRID, not USRID_LONG
    filters: {SUBTY: "0001", ENDDA: ">= today", company: "UNES"}
consumers:
  - "unescrp/scripts/probes/check_actor_chain.py --golden-db <v01 db>"
  - "unescrp/specifications/test-data/crp-usable-test-data.xlsx (Golden set V01)"
  - "unescrp/specifications/test-data/crp-test-scenario-model.md section 4"
  - "unescrp/.claude/agents/crp-test-case-builder.md"
resolve_via: UNKNOWN                  # no resolve_via line; message states only that "the golden DB is the sole path" (V01 is SSO-only)
# NOTE: this message carries an explicit DONE-verification query. C-4 v1.1 has no `verification` slot (C-2 does) - see report.
---

# Request: re-extract V01 `v01_pa0105` INCLUDING subtype 0001 (SY-UNAME → SAP logon user)

> **From:** `unescrp` (CRP app — test-case builder, S-178) · **Date:** 2026-07-03
> **Why:** The CRP test-case model gates every golden employee on having a **SAP logon user**
> (PA0105 **subty 0001** = system user name SY-UNAME → BNAME in USR02). Without it the person can
> neither log into the CRP app to submit a certificate NOR be resolved as the step-01 actor in the
> workflow (the `feedback_control_actor_not_role` hard rule). This was just verified on **D01** for the
> golden staff (`check_actor_chain.py --d01`, e.g. `10110932 → A_COWLING`). We need the same on **V01**,
> but the golden DB cannot answer it.

## What's there vs. missing (measured on the golden, 2026-07-03)
- `v01_gold_master_data.db` (mtime **2026-07-02 16:40**) HAS `v01_pa0105` with **7835 rows** — but
  **only `SUBTY='0010'` (email)**. `USRID_LONG` holds the e-mail (e.g. `10110932 → A.COWLING@UNESCO.ORG`).
- It has **ZERO `SUBTY='0001'` rows** (`SELECT count(*) FROM v01_pa0105 WHERE SUBTY='0001'` = 0).
  So there is **no PERNR → SAP logon user (BNAME)** mapping in the DB.
- `v01_usr02` (5552 rows) DOES contain the expected BNAMEs (e.g. `A_COWLING`, `R_AGRANE`, `A_ASSALY`
  all EXIST) — so the users seem provisioned on V01; only the **PERNR→BNAME link (IT0105/0001) is not
  extracted**. The extraction currently pulls only the email subtype.

## What to extract (add subtype 0001 to the V01 PA0105 pull)
Re-extract **PA0105** for V01 with **`SUBTY='0001'`** (the "system user name" communication subtype)
in addition to the existing `0010`. Keep the same columns:

| Column | Meaning |
|---|---|
| `PERNR` | personnel number |
| `SUBTY` | `0001` = SY-UNAME (SAP logon), `0010` = email |
| `USRID` (CHAR12) | for subty 0001 this is the **BNAME** (SY-UNAME); prefer `USRID` over `USRID_LONG` for 0001 |

Only **infotype-active / current** records (`ENDDA >= today`) are needed. Company `UNES`.

## Suggested action
1. Add `SUBTY='0001'` to the V01 PA0105 RFC read (same mechanism as the current `0010` pull);
   include the `USRID` field (the 0001 value lands in `USRID`, not `USRID_LONG`).
2. Re-land `v01_pa0105` in `v01_gold_master_data.db` (lowercase, same table name), so both subtypes
   coexist, and bump the extraction manifest / `extraction_status.md`.

## Consumers / impact in unescrp
- `scripts/probes/check_actor_chain.py --golden-db <v01 db>` — the S-178 SAP-user gate for V01
  (today it can only run against D01 live; V01 is SSO-only for us, so the golden DB is the sole path).
- `specifications/test-data/crp-usable-test-data.xlsx` → *Golden set V01* — cannot be finalized (the
  "Staff SAP user" column) until this lands. The D01 tab is already rebuilt with verified SAP users.
- Rule/agent: `specifications/test-data/crp-test-scenario-model.md` §4, `.claude/agents/crp-test-case-builder.md`.

## Verification (how we'll confirm DONE)
`SELECT PERNR, USRID FROM v01_pa0105 WHERE SUBTY='0001'` returns rows for the golden V01 PERNRs
(`10000152, 10001250, 10001977, 10002139, 10002161, 10002259, 10002711, 10003785, 10004022, 10005507,
10006039, 10007774`). Rename this file `DONE_v01_pa0105_subty0001.md` when landed.
