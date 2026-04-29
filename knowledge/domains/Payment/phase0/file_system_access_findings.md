# File system access findings — getting V000 baseline XMLs

**Generated**: 2026-04-29 · **Driver**: build V000 baseline for V001 simulation

## What worked

### ✅ File system access via UNC + SAP-std FMs

`RZL_READ_DIR_LOCAL` and `RZL_READ_FILE_LOCAL` are RFC-callable on P01 with our auth. Path resolution:

- `\\hq-sapitf\SWIFT$\P01` → 7 entries (ack/error/filtered/input/output)
- `\\hq-sapitf\SWIFT$\P01\output\psr\archive` → 998+ entries (`IIEP_SOGE_*.out`)
- `\\hq-sapitf\SWIFT$\P01\input\done archive` → 998 entries (`*.processed`)
- `\\hq-sapitf\SWIFT$\P01\output\filtered` → 998 entries (`<timestamp>.out`)

### Logical paths in PATH table (T-code FILE)

```
Z_BNK_PRO  → \\hq-sapitf\SWIFT$\<SYSID>\output\<FILENAME>      (output sent to bank)
Z_BNK_REPRO → \\hq-sapitf\SWIFT$\<SYSID>\output\psr\<FILENAME>  (re-process)
Z_BNK_ARC   → \\hq-sapitf\SWIFT$\<SYSID>\output\psr\archive\<FILENAME>  (archived)
Z_BNK_ACK   → \\hq-sapitf\SWIFT$\<SYSID>\ack\<FILENAME>  (acknowledgements)
Z_BNK_ERR   → \\hq-sapitf\SWIFT$\<SYSID>\output\psr\error\<FILENAME>  (errors)
Z_EBS_PRO   → \\hq-sapitf\SWIFT$\<SYSID>\output\ebs\<FILENAME>  (bank statements)
```

## What we found IN the archive (unfortunately not what we wanted)

### `output\psr\archive\IIEP_SOGE_*.out` files — these are **SWIFT NetWork acks/wrappers (MT101)**, NOT pain.001 XML

Sample content:
```xml
<DataPDU xmlns="urn:swift:saa:xsd:saa.2.0">
  <Header>
    <SenderReference>IIEP_SOGE_02INTEUR0084</SenderReference>
    <NetworkDeliveryStatus>NetworkAcked</NetworkDeliveryStatus>
    <RequestType>pain.fin.mt101</RequestType>  ← MT101 (SWIFT legacy), not pain.001
  </Header>
  <Contents>
    <AckNack>
      <PseudoAckNack>{1:F21UNESFRPPAXXX...}{4:{177:2209231257}{451:0}{311:ACK}</PseudoAckNack>
    </AckNack>
  </Contents>
</DataPDU>
```

**Conclusion**: these are SAA Alliance acknowledgements after the bank received the file. The actual pain.001 XML payment files were **deleted by SAA after successful submission**.

### `input\done archive\*.processed` (998 files) — couldn't read

`RZL_READ_DIR_LOCAL` lists them, but `RZL_READ_FILE_LOCAL` returns NOT_FOUND. Possibly because:
- File is locked / in-use by SAA
- Filename length issue with .processed extension
- OS permissions different for "done archive" subfolder

## Why pain.001 XMLs are not directly accessible

The DMEE flow at UNESCO:
1. F110 generates pain.001 XML in `<Z_BNK_PRO>` = `\\hq-sapitf\SWIFT$\P01\output\<FILENAME>`
2. SAA Alliance Lite2 picks up the file, packages in DataPDU, transmits to bank
3. SAA **deletes the original XML** after successful transmission
4. SAA stores its own ACK/wrapper in `<Z_BNK_ARC>` archive
5. The ACK has `<DataPDU>` envelope with metadata, not the original payload

**Net result**: P01 production XMLs are NOT retained on disk after submission.

## Alternative paths to get V000 baseline

### Option 1: SAP DMEE Test mode (BEST)
Tx DMEE → "Test" function generates a test XML for any tree against synthetic FPAYHX/FPAYP data. The output XML can be saved or captured.
- **Pros**: any tree, any data, generates fresh XML on demand
- **Cons**: requires SAP GUI session OR a custom RFC FM that triggers DMEE_API_RUN

### Option 2: F110 proposal mode (XVORL='X') file capture (38% of P01 traffic)
Run F110 with proposal flag. SAP generates the XML but doesn't post the payment. The XML lands briefly in `\\hq-sapitf\SWIFT$\P01\output\` before SAA picks it up.
- **Pros**: real production-shape data
- **Cons**: race with SAA; may need SAA disabled or redirected

### Option 3: Ask Marlies / Nicolas via email (FASTEST)
Send a request: "10 anonymized XMLs per tree (SEPA / CITI / CGI) from recent F110 runs".
- **Pros**: 1-day turnaround, real production data
- **Cons**: depends on their availability + privacy protocol

### Option 4: Build synthetic V000 from DMEE config
Read DMEE_TREE_NODE rows + apply known field-mapping rules + render valid pain.001 from synthetic FPAYHX data.
- **Pros**: full control, deterministic
- **Cons**: complex (re-implement SAP DMEE engine for 4 trees × ~2000 nodes)

## Investigation: P01 error folder (576 failed transmissions)

`\\hq-sapitf\SWIFT$\P01\output\psr\error` has **576 files** including:
- **OCITI*** prefix: 452 files (Citi outbound that failed transmission)
- **OSOGE*** prefix: 63 files (SocGen outbound failed)
- UNES_CITI: 39 .processed files
- UNES_SOGE: 19 .processed files
- IIEP_SOGE: 2 (residual)

These are FAILED transmissions that retained payload — should contain pain.001 XML.

**However**: all files in this folder return `NOT_FOUND` when reading via `RZL_READ_FILE_LOCAL`.

## Root cause: RFC name truncation

Diagnosis:
- `RZL_READ_DIR_LOCAL` truncates NAME field to ~32 chars (FIXED-WIDTH RFC structure)
- Real filenames are typically 40-50 chars (e.g., `OCITIFRPPXXXxxxTINA20210504085857.xml`)
- The DIR listing returns truncated `OCITIFRPPXXXxxxTINA2021050408585` (32 chars)
- `RZL_READ_FILE_LOCAL` rejects with NOT_FOUND because the truncated name doesn't exist on disk
- No `FILE_MASK` parameter available, no alternative FMs accessible (`EPS_OPEN_FILE`, `SUBST_GET_FILE_ATTRIBUTES`, `RZL_DIR_LIST_LOCAL`, `C13S_FILE_GET_NAME` all return NO_FUNCTION_FOUND)
- `SXPG_COMMAND_EXECUTE` exists but commands must be predefined in SM69 — auth-blocked

**Net result**: cannot programmatically retrieve real pain.001 XML from the file system via standard SAP-std RFC FMs with our authorization.

## Recommendation (final)

**3 alternative paths** — **Option C is fastest**:

### A. Custom RFC FM `Z_READ_LONG_FILE` (deploy to D01 via ADT)
- Code: ABAP report that reads file using `OPEN DATASET` with explicit long filename + `READ DATASET` into XSTRING
- Deploy: Pablo writes + ADT API or SE38 paste in D01
- ETA: 2-4 hours dev + 1 day testing
- Risk: requires production transport + S_DATASET auth verify

### B. SAP DMEE Test mode via custom RFC FM
- FM that wraps `cl_dmee_renderer=>render_xml( ... )` with synthetic FPAYHX
- Generates fresh XML without depending on file system
- ETA: 4-8 hours dev
- Risk: needs to construct synthetic FPAYHX correctly

### C. Email Marlies / Nicolas for samples ✅ FASTEST
- Request: "10 anonymized pain.001 XMLs per tree (SEPA / CITI / CGI variants)"
- They have direct access via SAP GUI (Tx DMEE Test or BCM batch download)
- ETA: 1 day
- Risk: zero
- Bonus: their human selection might pick representative scenarios we'd miss

### D. Build synthetic V000 from N_MENARD spec docs + DMEE config
- Use N_MENARD's TS DMEE CGI modifications doc as ground truth XML structure
- Apply YTFI_PPC_STRUC + DMEE node definitions to render synthetic
- ETA: 1-2 days
- Risk: synthetic ≠ real may miss edge cases

## Recommended path

**C (email) + D (synthetic)** in parallel:
- You email Marlies/Nicolas for 10 XMLs per tree
- I build synthetic V000 generator + V001 transformer + validator harness
- When real XMLs arrive, swap synthetic → real → run full pipeline → validation report

## Cross-reference

- Brain claim: file system access via UNC proven (record discovery — not blocking)
- N_MENARD email DMEE.eml (2026-04-29): had 3 docx attachments (specs only, no sample XMLs)
- Email draft: pending
- V001 transformer + comparator: build next regardless of source
