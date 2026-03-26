# SAP Transport Object Taxonomy — Quick Reference

Source: 5 Transport Intelligence Reference Documents (Session #008)

## 1. The PGMID / OBJECT / OBJ_NAME Triple

| PGMID | OBJECT | OBJ_NAME | Meaning |
|-------|--------|----------|---------|
| R3TR | PROG | ZMYREPORT | Full ABAP program (source + text + properties) |
| LIMU | REPT | ZMYREPORT | Only text elements (subobject — avoid transporting alone) |
| R3TR | TABU | T001 | Table content ROWS (not structure). Keys in E071K. |
| R3TR | TABL | ZMYTABLE | Table DEFINITION (DDIC structure). No data rows. |
| LANG | PROG | ZMYREPORT | Language-specific parts only (translations) |

Rule: Always transport R3TR (full object), never LIMU fragments.

## 2. OBJFUNC — The Action Flag

| OBJFUNC | Action | Risk |
|---------|--------|------|
| ' ' (blank) | Standard: export current state, overwrite target | Normal |
| D | Delete object in target | CRITICAL |
| M | Delete ALL rows + recreate from source | CRITICAL — entire table wipe |
| K | Key-based: only rows matching E071K keys | Normal for TABU |
| I | Insert all rows (additive, no delete) | Risky if keys overlap |

**Ghost Entry Trap**: Developer creates row → saves to TR → deletes row before release. SE09 shows the entry but NOTHING exports. OBJFUNC stays blank (not 'D'). Always verify via export log.

## 3. Request Types (E070.TRFUNCTION)

| Type | Code | Client Scope | Typical Objects |
|------|------|-------------|-----------------|
| Workbench | K | Client-independent (all clients) | PROG, CLAS, FUGR, TABL, TRAN, SICF |
| Customizing | W | Client-specific | TABU rows, SOBJ, SPRO recordings |
| Transport of Copies | T | One-time, no lock | Emergency patches |
| Relocation | R | Package move | TADIR reassignment |

## 4. Development Objects (Workbench K)

| OBJECT | Name | Risk | Notes |
|--------|------|------|-------|
| PROG | ABAP Program | MEDIUM | Full source transported, not individual lines |
| CLAS | ABAP Class | MEDIUM | Full class definition ships — contract may change silently |
| FUGR | Function Group | HIGH | **Replaces ALL FMs in target** — not just changed ones |
| TABL | DB Table Definition | HIGH | Field deletion/type change breaks programs silently |
| VIEW | View | MEDIUM | Maintenance view changes affect SM30 editing |
| DTEL | Data Element | LOW | Unless domain/type assignment changed |
| DOMA | Domain | HIGH | Fixed value changes affect validation across all fields |
| TRAN | Transaction | LOW | Navigation change only |
| DEVC | Package | LOW | Metadata, rarely causes issues |
| XPRA | Post-Import Program | HIGH | **EXECUTES after import** — review code first |
| ENQU | Lock Object | MEDIUM | Locking granularity change → deadlocks |
| NROB | Number Range | CRITICAL | **Overwrites current counters** → duplicate doc numbers |
| INTF | ABAP Interface | MEDIUM | Contract change → all implementors must retransport |
| SHLP | Search Help | LOW | F4 help behavior changes |

## 5. Customizing / TABU Objects — Impact by Table

### FI (Finance) — CRITICAL
| Table | Content | Impact |
|-------|---------|--------|
| T030/T030R | Account Determination | Silent G/L change — affects ALL future postings immediately |
| T001B | Posting Periods | **NEVER transport to PRD** — overwrites period open/close status |
| T001 | Company Code | New = new legal entity (rare post-go-live) |
| T011/FAGL_T011 | Financial Statement Versions | Balance sheet report output changes |
| SKA1/SKB1 | GL Account Master | Reclassification P&L↔BS changes reporting globally |
| T003 | Document Types | Number range or reversal type change |
| T004F | Field Status Groups | Optional→required field change breaks postings |
| T880 | Global Parameters | Extremely rare, always CRITICAL |
| FAGL_SCENARIO | Ledger Scenarios | Parallel ledger dimension change — cannot retroactively fix |

### HR (Human Capital) — CRITICAL
| Table | Content | Impact |
|-------|---------|--------|
| T512W | Wage Type Valuation | Wrong row = incorrect salary calculations silently |
| T511 | Wage Type Catalog | Master list — T512W depends on this |
| T512Z | WT Permissibility per Infotype | Which WTs allowed on which infotype |
| T510 | Pay Scale Groups | Salary amounts for TARIF valuation |
| T549A | Payroll Accounting Areas | Payroll area structure |
| T549Q | Payroll Periods | Period calendar — NEVER transport during open payroll |
| T554S/T554C | Absence Types/Valuation | Counting rule changes trigger retro payroll |
| T503 | Employee Group/Subgroup | WT permissibility grouping |
| T001P | Personnel Area/Subarea | Country grouping (MOLGA) determines schemas |
| T508A | Work Schedule Rules | Planned hours/shift pattern |
| Payroll Schema (ZU00) | R3TR PROG (special) | **CRITICAL** — entire payroll calculation sequence |
| PCR | R3TR PROG (special) | **HIGH** — rule table called by schema |
| Feature (DECI) | R3TR DECI | Decision tree for schema/PCR selection — no code diff visible |

### PSM-FM (Public Sector)
| Table | Content | Impact |
|-------|---------|--------|
| FMDERIVE | Derivation Strategy | **CRITICAL** — assigns FM account assignments to every posting |
| FMCI | Commitment Items | Budget line item categories |
| FM01 | FM Areas | Top-level FM structure (one-time setup) |
| T043 | AVC Tolerance Keys | Budget overrun tolerance — 100% = budget check disabled |
| FMRP_CRIT | Cover Groups | Funds covering each other's deficits |
| FMRB | RIB Rules | Revenue Increasing the Budget |

### PS (Project System)
| Table | Content | Impact |
|-------|---------|--------|
| OPST | Status Profile | Allowed business transactions per status |
| T420 | Budget Profile | AVC tolerance/carryforward settings |
| PROJ/PRPS | **ALARM** | Master data — NEVER transport via CTS |
| NROB | Number Ranges | NEVER transport — set manually |

### Bank/DMEE
| Table | Content | Impact |
|-------|---------|--------|
| T012/T012K | House Banks/Accounts | GL reconciliation account reference |
| T042/T042Z | Payment Methods | DMEE format assignment |
| T042I | Ranking Order | Bank selection for F110 |
| DMEE | Format Tree | **CRITICAL** — exact byte-level format of payment files |
| OBPM4 | Selection Variants | **NEVER transported** — recreate manually per system |

### RE-FX (Real Estate)
| Table | Content | Impact |
|-------|---------|--------|
| TIVCDCONDTYPE | Condition Types | Cash flow recalculation on affected contracts |
| TIVCDFLOWTYPE | Flow Types | Posting direction (debit/credit) change |
| TIVCDFLOWREL | Account Determination | **CRITICAL** — RE-FX equivalent of T030 |
| VIOB01/VIOB03/VIMI01 | **ALARM** | Architectural master data — NEVER transport |
| VICNCN | **ALARM** | Contract master data — NEVER transport |
| TIVNROBJ | Number Ranges | NEVER transport |

### Dunning (FI-AR)
| Table | Content | Impact |
|-------|---------|--------|
| T047A | Dunning Procedure Header | Interval, max level, min amounts |
| T047B | Dunning Levels | Days-in-arrears — legal timing in RE |
| T047C | Dunning Charges | FI postings on escalation |
| T047E | Dunning Form Assignment | Must match FORM/SFON in target |
| MHND | **ALARM** | Dunning history — NEVER transport |
| KNB5 | Customer Dunning Data | Master data — should NOT be in transport |

### Workflow (BC-BMT-WFM)
| Object | Content | Impact |
|--------|---------|--------|
| PDWS | Workflow Template | Must be manually added to transport from SWDD |
| PDTS | Standard Task | Must be manually added from PFTC |
| SWETYPV | Event Linkage | May arrive INACTIVE — verify SWE2 after transport |
| SWWWIHEAD | **ALARM** | Runtime work items — NEVER transport |
| SWU3 | Runtime Config | NOT transported — run manually in each target |

### Flexible Workflow (S/4HANA)
| Object | Content | Impact |
|--------|---------|--------|
| V_SWF_FLEX_SCACT | Scenario Activation | Without business config = no approvers = silent block |
| SWFVISU | UI Navigation | Missing = approvers can't see document |
| SWF_FLEX_TASKFLT | Task Filter | Missing = no action buttons in My Inbox |
| WS00800238 activation | PO Flex WF | **Disables classic release strategy** — irreversible |

### Invoice Unblock
| Table | Content | Impact |
|-------|---------|--------|
| T169G | Tolerance Keys | Widening = immediate AP control reduction |
| T169V | Tolerance per Co Code | Company-code-specific tolerance |
| T161W | Payment Block Reasons | Deleting a reason affects existing invoices |
| RBKP_BLOCKED | **ALARM** | Operational blocked invoice data — NEVER transport |

### BCM Payment
| Object | Content | Impact |
|--------|---------|--------|
| BCM Auto-Approval Rules | Mark Rules for Auto Payments | **CRITICAL** — payments skip dual control |
| BNK_INI Role | First-level Edit | Removed = payment batches go to nobody |
| BNK_COM Role | Approval Levels | Removing a level = fewer approvers |
| BUSISB001 Event Linkage | SWE2 | Must be ACTIVE or no workflow triggers |
| T042V (OBPM variants) | Selection Variants | **NEVER transported** — recreate manually |

## 6. ALARM Objects — Reject Transport Immediately

| Object | Why |
|--------|-----|
| TABU RBKP_BLOCKED | Operational blocked invoice data |
| TABU MHND | Dunning history (operational) |
| TABU SWWWIHEAD | Workflow runtime work items |
| TABU PROJ / PRPS | PS master data, not config |
| TABU VICNCN / VIOB01 | RE-FX contract/master data |
| TABU T001B | Posting period status — NEVER via transport to PRD |
| TABU TIVNROBJ | RE-FX number ranges |
| Any OBJFUNC='D' or 'M' | Destructive action — requires explicit approval |
| R3TR NROB | Number range counter overwrite |

## 7. SAP-Generated Artifacts (False Positives)

| Object | Parent | How Generated |
|--------|--------|---------------|
| TABU TDDAT | Custom Table | SE54 table maintenance generator |
| FUGR Z_*_MAINT | Maintenance View | SE54 auto-generated — replaces ALL FMs on transport |
| SICF nodes | OData Service | SEGW activation |
| IWSG/IWOM | OData | SEGW build |
| LIMU REPT | PROG | Text elements modified separately |
| ENQU | Custom Table | SE11 lock object generator |
| XPRA | Migration code | Post-import execution program |
| TABU CWBNTCUST | OSS Note | SNOTE application |

## 8. Pre-Import Checklist

| # | Check | How | Risk if skipped |
|---|-------|-----|-----------------|
| 1 | Request type K vs W | E070.TRFUNCTION | Wrong client scope |
| 2 | Contains XPRA? | E071 WHERE OBJECT='XPRA' | Post-import program executes without review |
| 3 | Contains NROB? | E071 WHERE OBJECT='NROB' | Number range overwrite |
| 4 | OBJFUNC='D' or 'M'? | E071.OBJFUNC | Unintended deletion or table wipe |
| 5 | Account determination? | E071K WHERE OBJ_NAME IN ('T030','VKOA') | Silent G/L change |
| 6 | FUGR artifact overwrite? | Compare FUGR contents source vs target | FMs deleted silently |
| 7 | Export log RC < 8? | Transport log | Incomplete objects |
| 8 | Auth objects (AGR, SUCU)? | E071 WHERE OBJECT LIKE 'AGR%' | Security role overwrite |

## 9. Cross-Module Pattern Triggers

| Pattern in E071 | Module | Action |
|----------------|--------|--------|
| T512W + T511 together | HR | Payroll config change — require simulation |
| T549Q + T549A | HR | Payroll period+area — NEVER during open payroll |
| DECI (Feature) | HR | Feature transport — compare source vs target |
| FMDERIVE transport | PSM-FM | Check if values included — verify master data alignment |
| T043 tolerance change | PSM-FM | Budget officer approval required |
| PROJ or PRPS | PS | **ALARM** — master data, investigate origin |
| DMEE + T042Z together | Bank | Full payment format change — verify OBPM1/OBPM4 |
| T001B | FI | **ALARM** — never import to PRD |
| T030 + T042Z same TR | FI+Bank | Double CRITICAL — split into two transports |
| SKB1 with OBJFUNC='M' | FI | GL account mass deletion — require pre-import backup |
| FAGL_SCENARIO + FAGL_T001L | FI/New GL | Parallel ledger structural change |
| TIVCDFLOWREL | RE-FX | CRITICAL — verify RERAZA G/L replacements |
| VIOB01/VIOB03/VIMI01 | RE-FX | **ALARM** — architectural master data |
| T047E without FORM/SFON | Dunning | Form assignment without form object — F150 will fail |
| TIVCDFLOWTYPE + T047C same TR | RE-FX+Dunning | Two FI posting chains — dual sign-off |
| V_SWF_FLEX_SCACT without business config | Flex WF | No approvers = silent block |
| WS00800238 activation | Flex WF/MM | Disables classic PO release strategy |
| BCM auto-approval + T042Z same TR | BCM+FI | Payment method AND auto-approval — CFO sign-off |
| SWWWIHEAD in any transport | Workflow | **ALARM** — reject immediately |
| PDWS without PDTS | Workflow | Steps reference missing tasks |
| MHND in transport | Dunning | **ALARM** — dunning history corruption |

## 10. Logical Objects (Hidden Complexity)

Logical objects have empty E071K — keys resolved dynamically at export time:
- **AGR_*** (Roles): displayed keys are simulation only
- **NROB** (Number Ranges): includes current counter status
- **SPRX/WDYR** (Web Dynpro): multiple internal tables

Security Note #2671160: verify TLOGOCHECK parameter for unauthorized data transport.

## 11. Account Determination Chains

### FI: T030 chain
T030 → Transaction Key → G/L Account (direct)

### RE-FX: 5-step chain
1. Condition Type (TIVCDCONDTYPE)
2. Flow Type (TIVCDFLOWTYPE)
3. Account Determination Value (TIVCDFLOWREL) ← T030 equivalent
4. Account Symbol (RERAZB)
5. G/L Account Replacement (RERAZA) ← company-code-specific, verify manually

### FBZP: 6-level dependency chain
1. Company Code → Paying Co Code (T042A)
2. Paying Co Code Settings (T042B)
3. Payment Methods / Country (T042Z) — DMEE tree must exist
4. Payment Methods / Co Code (T042C)
5. House Banks (T012/T012K)
6. Ranking / Bank Selection (T042I)

## 12. Post-Transport Actions by Module

### Workflow: After EVERY transport
1. SWU3 → Automatic Customizing (all green)
2. SWE2 → verify event linkages active
3. PFTC → verify General Task flag or assign agents
4. SWU_OBUF → synchronize org buffer
5. SWUS → event simulation test
6. SWI2_DIAG → check stuck work items

### BCM: After EVERY transport
1. SWU3 → verify SAP_WFRT user
2. SWE2 → verify BUSISB001 active
3. BNK_MONI → check batch approval status
4. Auto-approval rules → verify no unintended auto-approve
5. OBPM4 → recreate selection variants
6. BNK_INI/BNK_COM → verify role assignments
7. End-to-end test with small F110 payment run

### RE-FX: After account determination transport
1. Verify RERAZA (G/L replacement) manually in target
2. Run RECACC (Check Customizing) in target
3. RERAPP simulation before production
