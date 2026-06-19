# Domain — Document Attachment & Email Notification (GOLDEN reference)

> **Golden reference source** (CP-001: knowledge over velocity). Reusable, PROVEN in-house patterns for:
> (1) **email with a PDF attachment**, (2) **attach a document to a business object** (GOS / ArchiveLink),
> (3) **test-system recipient control**, (4) **receive a binary (PDF) via OData** (CREATE_STREAM).
> Source = N_MENARD (Nicolas) HR PA-WF + the HR Benefits Fiori app. Captured during the CRP `unescrp`
> S-143 work (PDF→FI-document attach + completion email) — consulted to avoid reinventing.

## Golden objects (read-back from D01 / already in `extracted_code`)

| Object | What it demonstrates | Path |
|---|---|---|
| `YCL_HR_WF_MAIL_PA_STAFF` | **Email WITH PDF** to staff: extends the mail GENERATOR; redefines `set_attachment` (pulls the stored doc), `get_data`/`replace_in_header` (body templating), `filter_authorized_email` (test control). | `extracted_code/HCM/YHR_PA_WF/YCL_HR_WF_MAIL_PA_STAFF.abap` |
| `YCL_HR_WF_MAIL_GENERATOR` (+ `_PA_S1`, `_PA_S1_ACTION`) | Base mail class family (the `cl_bcs` send + template engine); one concrete class per WF notification type. | `extracted_code/HCM/YHR_PA_WF/` |
| `YCL_HRWF_INTERN_GOS` | **GOS read/manage** of attachments on a business object (BDS doc-ids: `GET_DOCUMENT_KEY_FROM_ID`, `UPDATE_FILE_NAME_IN_GOS`, `IS_ATTACHED_FILE`). | `extracted_code/HCM/YHR_PA_WF/YCL_HRWF_INTERN_GOS.abap` |
| `ZCL_HR_FIORI_BENEFITS` (`create_attachment` + `create_doc_in_archive`) | **Receive + attach (ArchiveLink)**: stores a received PDF in a content repository and links it to a business object. | `extracted_code/HCM/CLAS/ZCL_HR_FIORI_BENEFITS/` |
| `ZCL_ZHR_BENEFITS_COMMO_DPC_EXT`, `ZCL_ZHRF_OFFBOARD_DPC_EXT` | **Receive a binary via OData `CREATE_STREAM`** (+ serve via `GET_STREAM`) — the FE/external uploads the file. | `extracted_code/HCM/CLAS/.../_iwbep_if_mgw_appl_srv_runtime_create_stream.abap` |
| `Y_HR_PAWF_MANAGE_LETTER`, `YHR_PA_WF_ATTACHMENT_MANAGE` | Manage WF letters in the content server / WF attachment manager (not yet extracted — readback from D01 when needed). | (live on D01) |

## The patterns

### 1. Email with a PDF attachment
A base `cl_bcs` mail class (`YCL_HR_WF_MAIL_GENERATOR`) + one concrete subclass per notification type that
**redefines `set_attachment`** to fetch the document. The attachment is read from a custom table (Nicolas:
`YTHRPAWF_ATTACH` by `wftype/pernr/attty`), then `cl_bcs` sends it. Body fields via `<TOKEN>` templating
(`replace_in_header` / `get_data` / `put_to_container`).

### 2. Attach a document to a business object — BO-AGNOSTIC (the key for reuse)
Two standard-SAP mechanisms, both keyed by `(sap_object, object_id)` so they attach to **ANY** business object:
- **ArchiveLink** (`ZCL_HR_FIORI_BENEFITS=>create_doc_in_archive`): `SCMS_XSTRING_TO_BINARY` →
  `ARCHIVOBJECT_CREATE_TABLE` (store in content repo) → **`ARCHIV_CONNECTION_INSERT( sap_object, object_id, ar_object, … )`** (link to the BO, TOA01). Needs a content repository + a doc type linked to the BO (OAC2/OAC3 config).
- **GOS** (`BDS_BUSINESSDOCUMENT_CREATEF` / `cl_gos`): attach to the BO via its key; uses the default repository
  (SOFFDB) — **lower config**, viewable in the BO transaction → *Services for Object → Attachment list*.

> **Reuse for an FI document:** set `sap_object = 'BKPF'`, `object_id = BELNR+BUKRS+GJAHR` → the PDF attaches to
> the accounting document (the JV), visible in **FB03 → Services for Object**. (CRP `unescrp` completion-notifier:
> the cert PDF → the JV's BKPF. GOS is the lower-config path for FI docs.)

### 3. Test-system recipient control (Nicolas's actual model)
`YCL_HR_WF_MAIL_PA_STAFF=>filter_authorized_email`: reads the allow-list table **`YTBC_MAIL_AUTH`** (key `yappl`,
e.g. `'PA_WF'`); any recipient NOT in the list gets `'TEST'` appended to its address → invalid → never reaches a
real user in a test system. (CRP `unescrp` chose a TVARVC-redirect variant instead — `ZCL_CRP_NOTIF_ENV`; this
allow-list is the alternative, documented here as the reference.)

### 4. Receive the PDF via OData
`CREATE_STREAM` (`/IWBEP/IF_MGW_APPL_SRV_RUNTIME~CREATE_STREAM`) on a media entity — the FE/external system PUTs
the binary; the handler gets it as `is_media_resource-value` (xstring). No custom FunctionImport needed.

## Provenance
Read-back from HQ-SAP-D01 (read-only, `unescrp/scripts/probes/readback_nmenard_obj.py`) during CRP `unescrp`
S-143. These are foreign (N_MENARD / HR) objects — **reference only, never modified** (own `Z*`/`Y*` only rule).
Cross-ref: `unescrp` plan `~/.claude/plans/quisiera-que-hagamos-una-toasty-lemon.md` (F4/F5 PDF→FI-doc attach).
