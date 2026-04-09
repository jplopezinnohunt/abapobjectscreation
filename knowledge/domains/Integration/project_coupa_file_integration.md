---
name: COUPA file-based integration discovery
description: COUPA integrates with SAP P01 via file-based jobs (not just BDC) — new system to map
type: project
---

COUPA is a new external system integrating with P01 via **file-based batch jobs** — SAP jobs read/write files from a shared location.

**Why:** This is a separate integration pattern from the BDC sessions (COUPA* in SM35) already known. File-based integration via background jobs is a third integration tier alongside RFC and BDC. Some SAP jobs run programs that read files deposited by external systems (or write files for them to consume). COUPA uses this pattern.

**How to apply:**
- Add COUPA as a new system in connectivity diagram (file-based integration, not just BDC)
- Investigate which SAP programs/jobs handle COUPA file exchange (check SM37 job names with COUPA/procurement keywords)
- Check AL11 or OS-level file directories for COUPA interface files
- This pattern may apply to other systems too — jobs reading/writing files = hidden integrations not visible in RFC destinations or IDoc monitoring
- Update `sap_interface_intelligence` skill to include file-based integration as a discovery vector

**Status:** Discovered Session #035 (2026-04-03). Not yet investigated.
