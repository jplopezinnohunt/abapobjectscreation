# Knowledge: UNESCO AVC Derivation Strategy (P01)

## 1. Functional Context
UNESCO uses "Alternative Account Assignments" to group expenditures at a higher level than the individual WBS or Fund. This allows for flexible budget management where multiple projects can share a single "Control Bucket" (AVC Object).

## 2. Technical Component Map (Extensions)

### A. The Cockpit: `YFM_ADD_RULEDERAVC`
- **Transaction:** `YFM_ADD_RULEDERAVC`
- **Program:** `YFM_COCKPIT` (Sub-program `YFM_COCKPITF01`)
- **Key Logic:**
    - **SNC-Protected BDC:** The program wraps standard transaction `FMAVCDERIAOR`.
    - **Hardcoded Environment:** Specifically forces `APPL = FM`, `SUBCLASS = 21`, `ENV = 9HZ00001`.
    - **Automation Workflow:**
        1. Derivation Rule Update (`FMAVCDERIAOR`)
        2. AVC Re-initialization (`FMAVCREINIT`)
        3. Structure Verification (`FMAVCR02`)

### B. Configuration Tables (Derivation Rules)
The real "configuration" resides in these generated tables:

| Table | Step ID | Strategy | Logic |
| :--- | :--- | :--- | :--- |
| **`FMAFMAP013500109`** | 0007 | AFMA | **AVC Object Derivation.** Maps Fund + Center + Item to a 2-character Control Type (e.g., PC, TC). |
| **`FMAFMTP013500110`** | 0004 | AFMT | **Tolerance Profile Derivation.** Maps internal keys to Profiles like `Z100` (Strict) or `Z200` (Warning). |
| **`TABADRS`** | N/A | Multiple | **Step Registry.** Defines which fields are source and which are target. |

## 3. Discovered Rule Patterns (P01 Audit)
Selected mappings from the live P01 environment:

| Fund | Center Prefix | Target AVC Object | Interpretation |
| :--- | :--- | :--- | :--- |
| `570M` | `570MEX` | **PC** | Project-based Control |
| `IBE` | `ADMRCS` | **TC** | Travel/Admin Control |
| `633UBO` | All | **Z100** | Strict 100% budget check profile |

## 4. Integration with PS (Project System)
The derivation uses the `OBJNR` (Object Number) of the WBS element. If the derivation fails to find a project-specific rule, it falls back to the static `FMFINCODE` (Fund) rule, which explains why linking the PS structure to FM is technically paramount for UNESCO.

---
*Stored in /knowledge/domains/PSM/EXTENSIONS/avc_derivation_technical_autopsy.md*
