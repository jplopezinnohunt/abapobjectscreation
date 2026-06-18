---
name: Product — Custom-over-Standard Process Overlay (the killer capability)
description: The user's product idea, designed. Overlay a customer's CUSTOM processes on the STANDARD SAP processes, down to the implementing code (Z exits, BDC, custom config). The standard process is the base layer; the customizations are the overlay; the code is the proof. Competitors mine as-is data and cannot separate standard-SAP from customer-customization because they don't see the code/namespace — this is our moat. Persisted s079.
type: project
---

# Custom-over-Standard Process Overlay

User idea (s079): "tendríamos como nuestros Custom process sobre los estándar process" — overlay
UNESCO's CUSTOM processes on the STANDARD SAP processes, down to the implementing code. This is the
killer framing: not "process mining" (commoditized) but **"see your customizations as a layer on
standard SAP, down to the code."**

## The three layers (per process)
1. **BASE — the STANDARD SAP process.** What SAP delivered / intended: standard tcodes, standard table
   flow, standard config, the SAP reference/best-practice process (normative model).
2. **OVERLAY — the customizations.** Where the customer's ACTUAL (mined) process EXTENDS or DEVIATES
   from standard: extra steps, skipped controls, custom routing, custom validations.
3. **IMPLEMENTATION — the code.** For each customization, the OBJECT that implements it: Z exit / BAdI /
   substitution-validation / BDC session / custom config / Z-tcode / .NET-RFC call. The proof.

## How we classify STANDARD vs CUSTOM (the "special for custom code")
1. **Namespace** (TADIR / the brain): Z*/Y* / customer package = custom; SAP package = standard. Every
   program, tcode, table, exit classified deterministically.
2. **Tcode origin** — Z-tcode vs standard SAP tcode (TSTC + namespace).
3. **Step origin** — a mined step that exists in SAP's reference flow = standard; a step that exists only
   because of a custom exit/BDC/Z-program = custom.
4. **Conformance** — discovered (as-implemented) model vs SAP normative/reference model → the DEVIATIONS
   are the customizations (as-implemented vs as-delivered).
5. **Enhancements on standard** — MODSAP/ENHO/CMOD on a STANDARD program = a customization injected into
   standard SAP (the most dangerous kind — YRGGBS00 pisando XREF1, ZXFMDTU02 hardcode).

## Where the custom event data comes from
- **Change documents work for CUSTOM objects too** — custom Z-tables can have change-doc logging on;
  custom processes are mineable via CDHDR/CDPOS like standard ones.
- **Custom Z-tables as event sources** — the GoR starts from a custom master table (our brain builds the GoR).
- **BDC sessions (APQI/APQD)** = the custom batch processes (Allos / Y1 payroll forensics — we have the skill).
- **Exits/BAdI/.NET** — from the brain's code extraction (extracted_code, the connective layer).

## The capabilities (the product)
1. **Custom-vs-standard X-ray** — classify every step/program/table/exit in a discovered process.
2. **The overlay view** — standard base + custom extensions highlighted, with the implementing code per
   extension. "Here is the SAP standard payment process; here are the customer's 7 customizations on it
   (this Z exit, this BDC, this config), and here is the code that does each."
3. **Customization inventory + intent** — what was customized and WHY (the brain: the exit's logic, the
   incidents it causes). A living register of the customer's deviation from standard.
4. **Risk / control conformance** — custom code = the risk surface (hardcodes, SoD breaks, commented-out
   validations). The overlay highlights where customizations break standard controls.
5. **⭐ S/4HANA MIGRATION X-ray** (the commercial hook) — when SAP changes a standard object, the overlay
   shows which customizations are affected. Every customer migrating to S/4 needs exactly this: "what
   custom code/process do we have on standard SAP, and what breaks on upgrade?" This is the #1 SAP concern.
6. **Simplification** — customizations that now replicate STANDARD S/4 functionality = candidates to retire.

## Why competitors structurally cannot do this
Celonis/Signavio mine the as-is DATA — which blends standard-SAP behavior and customer-customization
behavior into one process — but CANNOT separate them, because they don't see the CODE or the namespace.
The custom-over-standard overlay REQUIRES the code layer + namespace classification + exits/BDC/config
unified with the process. Our brain has all of it. This is the moat, and it is uniquely valuable for the
~most-customized SAP shops and for S/4 migration.

## Connection to conformance (the method)
The overlay IS object-centric conformance against a normative (standard) model: discovered model vs SAP
reference process → alignment → the deviations are the customizations → each annotated with its code.
(The pending deep research w7owt1ec3 targets: do SAP/Signavio ship normative reference models, and the
object-centric conformance methods. Mine it exhaustively on return.)

## Next
Build the custom-vs-standard classifier (namespace from TADIR/brain over a discovered process), then the
overlay view, then conformance vs a reference model. Local-buildable now for classification (we have
TADIR/brain); reference models + custom change-docs pending P01/research.
