# Session Learning: Transport Companion Builder + Company Code Copy
**Date:** 2026-03-26
**Project:** SAP Intelligence Platform (abapobjectscreation)
**Session focus:** Ad hoc transport analysis of D01K9B0CBF + D01K9B0F3V (company code STEM copy)

## ✅ Pattern 1: E07T not E070T for RFC
**What worked:** E070T is not readable via RFC_READ_TABLE in D01. E07T works.
**Why it works:** E070T has cross-client restrictions; E07T is the accessible view.
**Reuse:** Always try E07T first when reading transport descriptions via RFC.

## ✅ Pattern 2: TABKEY analysis reveals copy source
**What worked:** Analyzing E071K TABKEYs (e.g., "350STEMCBE01ETB01") identifies the house bank ID, currency, and indirectly the source company code.
**Why it works:** TABKEY = concatenated key fields. Parsing reveals BUKRS + HBKID + HKTID + currency patterns.
**Reuse:** For any TABU object, parse TABKEY to extract business meaning without reading the actual config table.

## ✅ Pattern 3: NR gap detection via NRIV comparison
**What worked:** Query NRIV WHERE SUBOBJECT='STEM' vs SUBOBJECT='IBE' (reference) to find missing number range objects.
**Why it works:** NRIV stores all number range intervals. SUBOBJECT = company code for FI/FM/CO/AA objects.
**Reuse:** When validating any company code copy, always compare NRIV against a known-good reference.

## ✅ Pattern 4: Multi-transport conflict detection
**What worked:** Two transports (FI + FM) both modify T001 for STEM. Detected via E071K TABKEY comparison.
**Why it works:** Same OBJNAME + overlapping TABKEY = potential conflict. Import order matters.
**Reuse:** When analyzing multiple transports for the same company code, always check for table overlap.

## ❌ Error 1: VPN timeout during validation
**What I did:** Ran transport_bank_detail.py with IP 172.16.4.66 — connection timed out.
**Why it failed:** VPN dropped between first and second script run. First script (transport_adhoc_read.py) worked because it ran earlier when VPN was up.
**Fix:** User confirmed VPN was not down — retried successfully with same IP.
**Lesson:** Don't assume hostname resolution is better than IP. Both can fail on VPN drops. The real fix is auto-reconnect pattern from rfc_helpers.py.
**Cost:** ~5min debugging

## ❌ Error 2: Unicode encoding on Windows
**What I did:** Used → and ✓ characters in Python print statements.
**Why it failed:** Windows cp1252 encoding can't handle these Unicode characters.
**Fix:** Added `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` at script start.
**Lesson:** Always set UTF-8 stdout wrapper in Python scripts on Windows when using Unicode characters.
**Cost:** ~2min

## Promote to Central?
- [x] Qualifies — Transport Companion pattern is reusable across all SAP projects
- [x] Company Code Copy checklist is reusable for any UNESCO office creation
