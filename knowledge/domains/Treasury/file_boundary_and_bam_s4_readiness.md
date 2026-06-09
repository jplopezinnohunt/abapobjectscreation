---
name: Treasury — file-I/O boundary + Bank Account Management (BAM) S/4 readiness (s079)
description: Two verified/applied findings for Treasury. (1) The FILE boundary discovered from extracted_code (AN-OPENDATASET): custom payment/bank programs do direct file I/O — the join between SAP and external systems (DMEE out / MT940 in). (2) BAM S/4HANA readiness: house bank accounts migrate T012K → FCLM_BAM_AMD (S4TWL 2870766) — Treasury is where R_S4_READINESS first lands because we hold T012/T012K. Applied model: FILE_IO_BOUNDARY (see applied_models.json).
type: project
---

# Treasury — file boundary + BAM S/4 readiness

## 1. File-I/O boundary (AN-OPENDATASET, applied — no extraction)
Scan of the 1,215 extracted custom .abap files: only **6 do direct file I/O** (`OPEN DATASET`: 11 FOR
OUTPUT, 3 FOR INPUT, 19 TRANSFER). They cluster in **payment/treasury**:
- Standard: RFFORI99 (payment medium), RPRAPA00 / RPRAPADE_ALV / RPRAPAFO_ALV (Travel payment).
- **Custom (Z/Y): `YTBAI001` (bank), `ZFPAYM_END` (payment).**

Why it matters: the **file is the JOIN** between SAP and the external world — payment runs WRITE files to
banks (DMEE), bank statements are READ from files (MT940). Without modeling the file, the process map
"ends" at SAP and "restarts" later, looking like two processes when it is one (the F_INTERFACE_FILE point).
To resolve WHERE these write/read (logical→physical paths): **EXT-FILES** (PATH/FILENAMECI/FILENAME, tcode
FILE, AL11) — D01-ok config.

## 2. BAM — Bank Account Management S/4HANA readiness (verified, S4TWL 2870766)
On S/4HANA, house bank accounts **migrate from `T012K` to `FCLM_BAM_AMD`** (linked via `FCLM_BAM_ACLINK2`)
**before go-live** — via report `FCLM_BAM_MIGRATION` (manual) or activity **CM1** (auto, account type 01).
Classic FI12 house-bank config → the **Manage Bank Accounts** Fiori app (BAM / BAM-lite).
- **Readiness signal we can assess:** populated `T012K`. We HOLD T012/T012K context (top-read tables in the
  dependency graph), so Treasury is the domain where **R_S4_READINESS** can first be scored from our data
  (count house bank accounts in T012K that must migrate; flag config gaps).
- Source: research wh5gw9exu (FINANCE_READINESS factor, S4TWL 2870766). Brownfield path (in-place SUM/DMO).

## Capability impact (Treasury_EBS)
- **F_INTERFACE_FILE** stays PARTIAL but now has the concrete custom file-I/O programs identified (design
  half of the file model). To HAVE: EXT-FILES + EXT-VARIANT (the path each writes).
- **R_S4_READINESS**: BAM factor is now a concrete, scoreable-from-T012K readiness check (method verified;
  apply when running the S/4 readiness pass).
