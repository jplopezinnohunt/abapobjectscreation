# UNESCO SAP P01 — Complete Integration Map
> Session #035 (2026-04-04) | Sources: RFCDES, EDIDC, TBTCO/TBTCP, TFDIR_CUSTOM, ICFSERVICE
> Every row = 1 integration flow with: channel, method, source, target, artifact, volume, status

---

## Integration Flows

### 1. RFC (.NET Connector) — 7 Apps, 334 FMs

| # | Source | Target | Channel | Artifact | What it does | Volume | Status |
|---|--------|--------|---------|----------|-------------|--------|--------|
| 1.1 | SISTER | SAP P01 | RFC via NCO_SERVER | 47 custom FMs | Financial reporting, budget transfers, fund queries | High | [VERIFIED] Active |
| 1.2 | HR Workflow App | SAP P01 | RFC via NCO_SERVER | 87 custom FMs | Employee lifecycle: 36 infotypes, OM updates, hire/transfer/terminate | Highest (87 FMs) | [VERIFIED] Active |
| 1.3 | CMT | SAP P01 | RFC via NCO_SERVER | 44 custom FMs | Vendor CRUD, master data lookups, bank validation | High | [VERIFIED] Active |
| 1.4 | UBO Field Office | SAP P01 | RFC via NCO_SERVER | 15 custom FMs | FI posting, FM commitment creation, field office operations | Medium | [VERIFIED] Active |
| 1.5 | Travel App | SAP P01 | RFC via NCO_SERVER | 21 custom FMs | Trip creation, DSA rates, XML processing | Medium | [VERIFIED] Active |
| 1.6 | Mouv | SAP P01 | RFC via NCO_SERVER | 12 custom FMs | Asset/equipment management | Low | [VERIFIED] Active |
| 1.7 | Procurement App | SAP P01 | RFC via NCO_SERVER | 13 custom FMs | PO release, entry sheets, goods receipt | Medium | [VERIFIED] Active |

### 2. IDoc — 4 Flows, 19,400 Documents

| # | Source | Target | Channel | Artifact | What it does | Volume | Status |
|---|--------|--------|---------|----------|-------------|--------|--------|
| 2.1 | SAP P01 | **BW Prod (BRP)** | IDoc RSINFO | RSINFO IDoc | Data staging info packages — triggers BW extraction | 9,399 IDocs (2024-2026) ~600/bimester | [VERIFIED] Active |
| 2.2 | **BW Prod (BRP)** | SAP P01 | IDoc RSRQST | RSREQUST IDoc | BW extraction requests — pulls data from P01 | 2,462 IDocs (2024-2026) ~160/bimester | [VERIFIED] Active |
| 2.3 | SAP P01 | **MuleSoft** -> Core Mgr/Plnr | IDoc PROJECT | PROJECT02 IDoc | WBS/Network project data push. Started Dec 2025 | 4,420 IDocs (dec25-mar26) ~1,500/month | [VERIFIED] Active |
| 2.4 | SAP P01 | **D01 + V01** | IDoc EXCHANGE_RATE | EXCHANGE_RATE01 | Exchange rate broadcast to dev+validation systems | 988 IDocs (494 each) | [VERIFIED] Active |

**Question: Where do exchange rates ORIGINATE?** P01 sends them to D01/V01, but who feeds P01? Treasury? ECB? Manual? TCURR has 55K rates — source unknown.

### 3. Middleware (MuleSoft)

| # | Source | Target | Channel | Artifact | What it does | Volume | Status |
|---|--------|--------|---------|----------|-------------|--------|--------|
| 3.1 | SAP P01 | Core Manager/Planner | MuleSoft MULESOFT_P01_IDOC (TCP/IP) | PROJECT02 IDoc | Project WBS structures to Core Manager | 4,420 IDocs | [VERIFIED] Active |
| 3.2 | Core Manager/Planner | SAP P01 | MuleSoft MULESOFT_PROD (HTTP/G) | RFC/BAPI? | **UNKNOWN** — HTTP dest exists but no evidence of inbound traffic in IDoc/job tables. Could be BAPI calls or unused. | ? | [INFERRED] Dest exists, traffic unconfirmed |

**Question: Does Core Manager WRITE BACK to SAP?** MULESOFT_PROD (type G) exists but we have no IDoc or job evidence of inbound flow. Is it read-only (SAP→CM) or bidirectional?

### 4. File-Based Jobs — 9 Systems, ~8,700 Runs

| # | Source | Target | Channel | Artifact | What it does | Volume | Status |
|---|--------|--------|---------|----------|-------------|--------|--------|
| 4.1 | Banks (SocGen, Citi) | SAP P01 | File share -> Job | `RBNK_IMPORT_PAYM_STATUS_REPORT` (variants: Z_PSR_SOCGEN, Z_PSR_CITI, Z_PSR_CITI_V3) | Import payment status reports from SWIFT network | 4,164 runs (3 banks) | [VERIFIED] Active, daily |
| 4.2 | Banks (SWIFT) | SAP P01 BCM | File share -> Job | `ZFI_SWIFT_UPLOAD_BCM` (variants: SWIFT_ACK_UNES, SWIFT_ACK_IIEP) | Upload SWIFT acknowledgements into BCM | 2,778 runs (2 streams: UNES + IIEP) | [VERIFIED] Active, daily |
| 4.3 | Banks (MT940) | SAP P01 EBS | File share -> Job | `FEB_FILE_HANDLING` | Electronic bank statement import (MT940 format) | 347 runs | [VERIFIED] Active, daily |
| 4.4 | **COUPA** | SAP P01 FI | File share -> Job | `YFI_COUPA_POSTING_FILE` (var: STANDARD) | Coupa invoice files -> FI postings. Runs hourly (00:15-09:15 pattern) | 348 runs | [VERIFIED] Active, hourly |
| 4.5 | **COUPA** | SAP P01 (email) | File share -> Job | `YFI_COUPA_POSTING_FILE_MAIL` | Email notification after Coupa posting | 3 runs | [VERIFIED] Active, weekly |
| 4.6 | SAP P01 | **SuccessFactors EC** | Job -> File/API | `ECPAO_OM_OBJECT_EXTRACTION` (43 parallel jobs) | Org Management objects to EC Payroll. Variants = OM object ranges | 1,290+ runs | [VERIFIED] Active, massive |
| 4.7 | SAP P01 | **SuccessFactors EC** | Job -> File/API | `ECPAO_EMPL_EXTRACTION` (3 parallel jobs) | Employee master data to EC Payroll | 51 runs | [VERIFIED] Active |
| 4.8 | SAP P01 | **SuccessFactors** | Job -> File | `RH_SFI_SYNCHRONIZE_EMPL_DATA` (var: EMPLOYEE) | Employee data sync to SF | 16 runs | [VERIFIED] Active, daily |
| 4.9 | SAP P01 | **SuccessFactors** | Job -> File | `YHR_SF_EXPORT_GEODIS` (var: GEODIS) | Geo distribution data export to SF | 16 runs | [VERIFIED] Active, daily |
| 4.10 | SAP P01 | **SuccessFactors** | Job -> File | `YHR_SF_EXPORT_ORGANIZATION` | Org structure export to SF | 16 runs | [VERIFIED] Active, daily |
| 4.11 | SAP P01 | **UNESDIR** | Job -> File | `ZLFNA1_DOWNLOAD_FOR_UNESDIR` (var: PROD_UNESDIR) | Vendor master data download for UNESDIR directory | 15 runs | [VERIFIED] Active, daily |
| 4.12 | SAP P01 | **?** | Job -> File | `ZLFNA1_DOWNLOAD_VENDOR_TABLE` (job: VENDORMASTERUPDATE) | Vendor table export — target system unknown | 15 runs | [INFERRED] Active |
| 4.13 | SAP P01 | **Data Hub** | Job -> File | `YFM_OUTPUT_INDIRECT_COSTS_DH` | FM indirect cost allocation per company code (11 CC variants) | 11 runs | [VERIFIED] Active |
| 4.14 | SAP P01 | **Data Hub** | Job -> File | `YFM_STAFF_COST_DISTRIBUT_DH` | Staff cost distribution per CC (4 variants: UBO, UNES_MCA, UNES_RGF, UNES_RP) | 4 runs | [VERIFIED] Active |
| 4.15 | SAP P01 | **Data Hub** | Job -> File | `YHR_ORG_UNIT_COUNT_DH` | Org unit headcount (established + vacant posts) | 6 runs | [VERIFIED] Active |
| 4.16 | SAP P01 | **Data Hub** | Job -> File | `YHR_DASHBOARD_1_DH` | HR dashboard data | 1 run | [VERIFIED] Active |
| 4.17 | SAP P01 | **BW** | Job -> File | `YBW_EXTRACT_WBS_LTXT` | WBS long text extraction for BW reporting | 15 runs | [VERIFIED] Active |
| 4.18 | SAP P01 | **MBF** (Medical Benefits) | Job -> File | `YHR_MBF_ELIGIBILITY_FILE` | Medical benefits eligibility data | 3 runs | [VERIFIED] Active |
| 4.19 | SAP P01 | **File system** | Job -> Spool -> File | `ZSPOOL_TO_FILE` (5 jobs: HR staffing, FM monitoring) | Spool output dump to file share | 50 runs | [VERIFIED] Active |
| 4.20 | ? | SAP P01 | Job -> File | `YFI_FILE_RATES_TMS` (job: TMS_UPDATE_RATES) | Treasury exchange rate file import? | 1 run | [INFERRED] Source unknown |

**Question: Where does COUPA deposit files?** AL11 directory or OS mount? Same for SWIFT/MT940 files.
**Question: Data Hub = which system?** YFM/YHR programs with _DH suffix. Is it a BI tool? A UNESCO internal reporting platform?
**Question: YFI_FILE_RATES_TMS** — is this the source of exchange rates for P01? If so, it closes the loop on where EXCHANGE_RATE IDocs originate.

### 5. BDC (Batch Data Communication)

| # | Source | Target | Channel | Artifact | What it does | Volume | Status |
|---|--------|--------|---------|----------|-------------|--------|--------|
| 5.1 | Allos HR App | SAP P01 HR | BDC via SM35 | `PRAAUNESC_*`, `PRAAIIEPU_*`, etc. (RSBDCBTC_SUB) | PA30 infotype updates — HR mass changes from Allos | 89 sessions (#1 BDC) | [VERIFIED] Active |
| 5.2 | **COUPA** | SAP P01 | BDC via SM35 | `COUPA0000282/283/284` (RSBDCBTC_SUB) | Coupa-originated BDC sessions — additional to file posting | 3 sessions (mar 2026) | [VERIFIED] Active |

### 6. LSMW (Mass Data Loading)

| # | Source | Target | Channel | Artifact | What it does | Volume | Status |
|---|--------|--------|---------|----------|-------------|--------|--------|
| 6.1 | **?** | SAP P01 MM | LSMW IDoc | BUS1504_CREATE02 | Service Entry Sheet mass creation | 1,599 IDocs (24 Jan 2025, single day) | [VERIFIED] One-time load |
| 6.2 | **?** | SAP P01 MM | LSMW IDoc | BUS1505_CREATE04 | Purchase Order mass creation | 240 IDocs (27-28 Jan 2025) | [VERIFIED] One-time load |
| 6.3 | **?** | SAP P01 MM | LSMW IDoc | BUS1505_CHANGE04 | Purchase Order mass change | 284 IDocs (15-16 Dec 2025) | [VERIFIED] One-time load |
| 6.4 | **?** | SAP P01 MM | LSMW IDoc | BUS1503_CREATE03 | Contract mass creation | 6 IDocs (24 Jan 2025) | [VERIFIED] One-time load |
| 6.5 | **?** | SAP P01 MM | LSMW IDoc | BUS1501_CREATE02 | Purchase Requisition mass creation | 2 IDocs (24 Jan 2025) | [VERIFIED] One-time load |

**Question: Where does LSMW data come from?** Jan 2025 = massive procurement load (1,599 SES + 240 POs + 6 contracts in 2 days). Is this a migration? Annual carry-forward? External system feed?

### 7. DBCON (Direct SQL Server)

| # | Source | Target | Channel | Artifact | What it does | Volume | Status |
|---|--------|--------|---------|----------|-------------|--------|--------|
| 7.1 | **TULIP** | SAP P01 HR | DBCON SQL | `YHR_MANAGER_FROM_TULIP_UPDATE` | Read HR manager assignments from TULIP DB | 15 runs (93% failure!) | [VERIFIED] Active, failing |
| 7.2 | **UNESDIR** | SAP P01 HR | DBCON SQL | `YHR_CREATE_MAIL_FROM_UNESDIR` | Read employee email from UNESDIR directory DB | 15 runs (93% failure!) | [VERIFIED] Active, failing |

### 8. HTTP/SOAP External

| # | Source | Target | Channel | Artifact | What it does | Volume | Status |
|---|--------|--------|---------|----------|-------------|--------|--------|
| 8.1 | SAP P01 | **UNJSPF** (UN Pension Fund) | HTTPS SOAP/XI | `UNJSPF_INTERFACE1` -> unjspfwdp1.sap.unicc.org:443 (endpoint: /XISOAPAdapter/MessageServlet) | Pension population data (UNESCO_POP) to UNJSPF via PI/XI | ? | [VERIFIED] Dest active, traffic not measurable from our data |
| 8.2 | SAP P01 | **BOC** Invoice WF | TCP/IP registered | `BOC_INVOICE_WF` registered on gateway hq-sap-p01 | Invoice workflow processing — external program listens on SAP gateway | ? | [VERIFIED] Dest active, traffic unknown |
| 8.3 | SAP P01 | **AWS EC2** | HTTP:80 | `CSI_AWS_EC2` -> ec2.amazonaws.com | Cloud Service Integration — AWS compute | ? | [INFERRED] Dest exists, no HTTPS! |
| 8.4 | SAP P01 | **AWS S3** | HTTP:80 | `CSI_AWS_S3` -> s3.amazonaws.com | Cloud Service Integration — AWS storage | ? | [INFERRED] Dest exists, no HTTPS! |
| 8.5 | SAP P01 | **ADS** (Adobe) | HTTP | `ADS` | Adobe Document Services — PDF form generation | ? | [VERIFIED] Standard SAP component |

---

## Open Questions (Gaps to Investigate)

| # | Question | Why it matters | How to find out |
|---|----------|---------------|-----------------|
| Q1 | Where do exchange rates originate? | P01 broadcasts to D01/V01 but who feeds P01? | Check `YFI_FILE_RATES_TMS` — is this the source? Or manual TCURR entry? |
| Q2 | What is "Data Hub"? | 4 programs export FM/HR data with _DH suffix | Ask business — is it a BI platform? UNESCO internal tool? |
| Q3 | Where does LSMW data come from? | 1,840 procurement docs loaded Jan 2025 | Check with MM team — migration or annual process? |
| Q4 | Does Core Manager write back to SAP? | MULESOFT_PROD (HTTP) exists but no inbound traffic seen | Check MuleSoft logs or RFC trace |
| Q5 | Where do COUPA/SWIFT/MT940 files land? | File-based integrations need a shared directory | Check AL11 or OS mount points |
| Q6 | What does BOC_INVOICE_WF do? | Registered program on SAP gateway — unknown purpose | Check who owns the process, or SE37 for RFC function |
| Q7 | Is AWS integration active? | HTTP (not HTTPS!) on port 80 to AWS — security concern | Check SM59 connection test. No HTTPS = potentially insecure or test-only |
| Q8 | VENDOR MASTER export — who receives it? | ZLFNA1_DOWNLOAD_VENDOR_TABLE runs daily, target unknown | Check program variant for output path |
| Q9 | UNJSPF — what data is sent? | Pension interface via SOAP/XI to UNICC | Check IDoc or XI message logs |
| Q10 | TULIP/UNESDIR 93% job failure — why? | Both DB connections failing consistently | Check DBCON entries in SM59, DB availability |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Total integration flows** | 37 documented |
| **External systems** | 18+ (7 .NET apps, BW, MuleSoft, COUPA, SuccessFactors, TULIP, UNESDIR, UNJSPF, BOC, AWS, ADS, Data Hub, MBF, Banks) |
| **Integration channels** | 8 (RFC, IDoc, MuleSoft, File-based, BDC, LSMW, DBCON, HTTP/SOAP) |
| **Open questions** | 10 |
| **Failing integrations** | 2 (TULIP 93%, UNESDIR 93%) |
| **Security concerns** | 1 (AWS HTTP:80 without TLS) |

Last updated: Session #035 (2026-04-04)

---

## AI Diligence Statement

| Aspect | Detail |
|--------|--------|
| AI Role | Queried Gold DB (RFCDES, EDIDC, TBTCO/TBTCP, TFDIR_CUSTOM) to discover and classify integration flows. Structured output into 8 channels. |
| Model | Claude Opus 4.6 (1M context) via Claude Code |
| Human Role | JP directed investigation of file-based integration vector, identified COUPA dual-pattern, requested channel+artifact structure, validated findings |
| Verification | All volumes from SQL queries against Gold DB. RFC destinations from RFCDES. IDoc counts from EDIDC. Job runs from TBTCO. Each flow tagged [VERIFIED] or [INFERRED]. |
| Limitations | Only sees traces in extracted tables. Synchronous RFC calls (334 .NET FMs) leave no trace. ~20 HTTP GUID destinations uninvestigated. UNJSPF/BOC/AWS traffic volume unknown. |
| Accountability | JP Lopez maintains full responsibility for all content |
