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

## Recommendation

**Option 3 + Option 4 in parallel**:
- **Option 3**: I draft a request email to Marlies/Nicolas asking for samples. You send it.
- **Option 4 (lite)**: I build a synthetic V000 generator using ONE representative XML structure per tree (using N_MENARD's spec docs as template), enough to demonstrate V001 transformer + validator end-to-end.

When their samples arrive, swap synthetic → real, re-run pipeline.

## Cross-reference

- Brain claim: file system access via UNC proven (record this discovery)
- N_MENARD email: 3 docx attachments may already include sample XMLs (check)
- Email draft: pending
- V001 transformer + comparator: to build next regardless of source
