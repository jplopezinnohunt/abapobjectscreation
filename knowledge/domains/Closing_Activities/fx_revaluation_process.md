# FX Revaluation Process (F.05 / SAPF100) — Knowledge Brain

**Domain**: Closing Activities
**Process owner**: Treasury / Finance accountants (per institute)
**Evidence tier**: TIER_1 — direct P01 production data (BKPF/BSIS, VARI/VARIS, T030H, SKB1, T012K, T001)
**Last verified**: Session #078 (2026-06-05)
**Scope**: 9 UNESCO company codes (ICBA, UIL, UBO, IBE, IIEP, UIS, MGIE, ICTP, UNES), 2025–2026

> This is the canonical process-knowledge document. The companion `companions/closing_activities_v1.html` is the user-facing rendering; this `.md` is the authoritative source for agents. Word deliverable for stakeholders: `companions/FX_Revaluation_Conclusions.docx` (regenerate from this brain via `node scripts/build_fx_revaluation_docx.js`).

---

## 0. Strategic Framing — why this analysis matters beyond the error

FX revaluation is **one recurring step in the monthly/annual financial close**, and it exemplifies the project's purpose:

- **The headline is the opportunity, not the error.** The recurring close tasks at UNESCO run interactively, with no scheduling, no execution visibility, and no audit of whether they ran. The value is to **automate them and instrument them for visibility** — "the job log proves it ran, on time, completely." The OB09 error is a minor immediate adjustment, not the story.
- **Methodology = process mining.** We reconstruct the reality of a process — who runs it, when, gaps, configuration, root cause — purely by **mining logs, data, tables and code** (BKPF/BSIS, GLT0, T030H, VARI/VARIS, OB09/FS00, BDC sessions). Read the system, not the documentation. This is the reusable lens for every domain.
- **Domain-by-domain ambition.** For each domain: understand how it works → identify what to improve → automate and give execution visibility → and resolve each incident **with context**. FX revaluation is the first worked example; there are many recurring close tasks (and other domains) that need the same treatment. This is the path from reactive incident-handling to a system that knows itself. (Aligns with the project North Star — SAP Agentic AGI.)

---

## 1. What FX Revaluation Is

Foreign-currency (FX) revaluation restates foreign-currency balances and open items to the period-end exchange rate, so financial statements reflect current FX value. At UNESCO it runs via program **SAPF100** (transaction **F.05**), monthly, per company code.

**Company-code local currency = USD** (confirmed `T001.WAERS` for all relevant company codes; UNES = USD). This single fact governs which accounts have FX exposure: a USD account in a USD company code has **nothing to revalue**.

---

## 2-bis. ⭐ LA TIPOLOGÍA COMPLETA — métodos, variantes y mecanismo (MEDIDO 2026-08-21, s102)

Leído en vivo de P01 con `RS_VARIANT_CONTENTS_RFC` (contenido íntegro de las 4 variantes) y de
`T044A` (definición de los métodos). No es el modelo de dos procesos de §2: es **más fino**, y en
un punto lo corrige.

### Los métodos de valoración (`T044A`) — 3 definidos, 2 en uso

| Método | En uso | `XSALK` | `XPOSD` | `XSALR` | Tipo de cambio | Tipo doc | Qué es |
|---|---|---|---|---|---|---|---|
| **UNBA** | ✅ | X | — | — | **M** (medio) | `JV` | Valoración de **saldos** de cuenta de mayor |
| **UNOI** | ✅ | — | X | X | **M** (medio) | `JV` | Valoración de **partidas abiertas** |
| `UNIM` | ❌ **ninguna variante lo usa** | X | — | — | **V** (venta) | `JV` | Idéntico a UNBA salvo el tipo de cambio |

`UNIM` es la única diferencia real que existe entre métodos definidos: mismo comportamiento que
`UNBA` con tipo de cambio **V** en vez de **M**. Está definido y **nadie lo ejecuta**.

### Las variantes — cuál usa qué (el programa dice qué se PUEDE; la variante, qué se HACE)

| Variante | Método | Mecanismo real | Selección de cuentas |
|---|---|---|---|
| **UNES_UNBA** | UNBA | **SALDO** (`X_SALBEW=X`, OI apagado) | 3 **rangos**: `1000000–1099999`, `1400000–1499999`, `1900000–1999999` — bancos y caja |
| **UNES_DEPOSIT** | UNOI | **Partidas abiertas** G/L (`X_GL=X`) | 17 cuentas **sueltas** (EQ) |
| **UNES_OI_G/L** | UNOI | **Partidas abiertas** G/L (`X_GL=X`) | 6 cuentas sueltas |
| **UNES_OI_AR/AP** | UNOI | **LAS DOS A LA VEZ** — `X_SALBEW=X` **y** `X_GL`/`X_AP`/`X_AR`=X | 12 cuentas |

> **El modelo de dos procesos de §2 no captura `UNES_OI_AR/AP`**, que activa saldo *y* partidas
> abiertas en la misma ejecución. No son dos cajones: son dos interruptores independientes que una
> variante puede encender a la vez.

> **El mecanismo de selección cambia entre variantes del MISMO programa**: `UNES_UNBA` usa rangos
> `BT`, las tres `_OI`/`_DEPOSIT` usan valores sueltos `EQ`. Suponer uno de los dos deja fuera a la
> mitad de la población.

### La determinación de cuentas se elige POR CUENTA con `SKB1-XOPVW` — y son DOS tablas

§4 describe `T030H`/OB09 como *la* determinación de la revaluación. Es la mitad. El árbol real,
verificado en vivo el 2026-08-21 y ya documentado en el companion desde 2026-05-05:

```
SKB1-XOPVW = 'X'   partidas abiertas  →  KDF  →  T030H   una fila POR CUENTA  (esto es OB09)
SKB1-XOPVW = ''    saldo              →  KDB  →  T030S   una fila por CLAVE (SKB1-KDFSL);
                                                          clave vacía = DEFECTO DEL PLAN
```

Medido en UNES: **2.315 cuentas**, `XOPVW='X'` en **1.155** y vacío en **1.160**; y **`KDFSL` vacío
en las 2.315**, así que toda cuenta valorada por saldo cae en el defecto del plan. `T030S` para
UNES tiene exactamente **2 filas**:

| `KDFSL` | Gasto (`KSOLL`) | Ingreso (`KHABN`) | |
|---|---|---|---|
| *(vacía — defecto)* | `0006045011` | `0007045011` | la que usa **todo** |
| `GRP` | `0005022012` | `0005022012` | definida y **sin usar** |

**Consecuencia práctica**: un check que exija fila en `T030H` a toda cuenta de banco produce
**160 falsos positivos** — las cuentas de saldo no tienen fila y no la necesitan. Pasó en la
primera corrida de `fx_revaluation_scope_check.py` el 2026-08-21.

> **Y un error de método que merece quedar escrito.** Al no encontrar la determinación en `T030`
> con `KTOSL='KDB'` (0 filas) ni en un campo inexistente de `SKB1`, se declaró *"mecanismo sin
> explicar"* y se marcaron 160 cuentas como REVISAR. La respuesta llevaba **meses** en
> `companions/fx_revaluation_f05_v1.html` §*Where 6045011 / 7045011 come from* (TIER_1,
> 2026-05-05), con `T030S` y el árbol por `XOPVW` escritos. No se miró el cerebro antes de declarar
> el hueco: `feedback_brain_first_then_grep`, literal.

**Alcance real, con el árbol correcto** (P01/UNES, FS10, 2026-08-21): de **1.084** cuentas de
banco/inversión — **678 bloqueadas** · **350 completas** · **55 latentes** (sin exposición hoy) ·
**0** con exposición y sin determinación · **1 defecto vivo**: `4041011`, con `T030H` y en ninguna
variante.

### ⛔ Afirmación REFUTADA (estaba en §3 de este mismo documento)

> ~~"La única confirmación pendiente es leer el check `Bal.sheet preparation valuatn` en la
> pantalla de una variante `_UNBA` — **no extraíble por RFC**: VARI/VARIS son tablas pool que solo
> devuelven el nombre de la variante."~~

**Falso, y cerrado.** `RS_VARIANT_CONTENTS_RFC` es remote-enabled y devuelve el contenido íntegro:
las 4 variantes se leyeron enteras, `X_SALBEW` incluido. Lo que no se puede leer es `VARI.CLUSTD`
por `RFC_READ_TABLE` (campo RAW), que no es lo mismo que "la variante no es auditable".
Ver `sap_variant_analysis` y la regla `feedback_read_the_variant_the_variant_is_the_process`.

---

## 2. Execution Model — Two-Step via Batch Input

F.05 / SAPF100 **does not post directly to FI**, and it runs as **two distinct processes** — Open Item revaluation and Balance revaluation — that share one posting mechanism but **diverge on reversal**. They are separate F.05 executions with separate variants.

**Shared posting mechanism (both processes):**
```
1. Accountant runs F.05 (interactively — no background job)
2. SAPF100 reads T030H/OBA1, calculates the FX delta per in-scope account
3. SAPF100 creates a BATCH INPUT SESSION (SM35)        ← not yet in FI
4. SAPF180 processes the session
5. FI documents posted → BKPF with TCODE = 'FBB1', BUDAT = month-end
   ── then the two processes diverge ──
```

**Process A — Open Item Revaluation** (`_OI` variants · Mode A, reversing). F.05 tab = **Open Items**; batch session `{BUKRS}_REVAL_OI`. AR/AP + G/L open items.
```
A1. Valuate : FBB1 valuation, BUDAT = month-end
A2. Reverse : FBB1 reversal,  BUDAT = day 1 of next month
              → SAPF124 daily clearing books the REALIZED FX when the item clears
Net: nothing permanent is booked — the interim valuation is fully reversed on day 1;
     only the realized FX stays. Reversal is MANDATORY (skipping it double-counts).
```

**Process B — Balance Revaluation** (`_UNBA` / `_BA` variants · Mode B, permanent). F.05 tab = **G/L Balances**; batch session `{BUKRS}_REVAL_BA`. Bank/cash balance-sheet accounts.
```
B1. Valuate : FBB1 valuation, BUDAT = month-end, written to the account's
              valuation-difference field
B2. NO reversal — the position is carried; the next run posts only the DELTA
              vs the stored valuation-difference
Net: the revalued balance-sheet position stays. No reversal is CORRECT (Mode B —
     balance-sheet preparation); reversing it would erase the carried position.
```

> The two processes share the same interactive launch — so they share the same **"missed run" risk** (§6) and both end at the OB52 period lock. The OI↔Balance split is the same Mode A vs Mode B distinction in §3, made explicit at the execution level.

### Key facts
- **Zero SAPF100 background jobs exist** (checked APQI/TBTCO). All runs are interactive.
- **FBB1 is the program's internal posting transaction**, NOT manual line entry. `TCODE='FBB1'` + human `USNAM` (not JOBBATCH) in BKPF = interactive SAPF100 execution.
- **11,793 FBB1 documents** posted in 2025 across the 9 company codes.
- Batch sessions are named per institute: `{BUKRS}_REVAL_OI`, `{BUKRS}_REVAL_BA`, with variations (IIEP uses `REVA`, MGIE uses `MGI`, UIL balance uses `REVAL_01`). UNES, ICBA, ICTP, UBO post via `SAPF180/{BUKRS}` with no separately named session — which is why a naive APQI name search misses them.

### How to verify execution from data
- Valuation docs: `BKPF.TCODE='FBB1'` AND `BUDAT` = last days of month (day ≥ 28).
- Reversal docs: `BKPF.TCODE='FBB1'` AND `BUDAT` = day 1–2 of month.
- Which account type a doc valued: join `BSIS.HKONT` → `P01_SKA1.KTOKS` (`BANK` / `OTHR` / `COLL` / `P&L`).

---

## 3. Two Valuation Modes — BOTH Are Correct (critical concept)

Reversal is **not** exclusive to Open Items. SAP F.05 reverses both OI and G/L-balance valuations. The difference is the **mode**, and both are legitimate accounting practice.

| | Mode A — Reversing valuation | Mode B — Balance-sheet preparation valuation |
|--|------------------------------|----------------------------------------------|
| Reversal | Yes — post month-end, reverse day 1 | **No — permanent** |
| Stored as | Temporary snapshot | Written to the account's valuation-difference field; next run posts only the delta |
| Used for | Interim months | Official balance-sheet position (typically year-end) |
| Controlled by | "Reversal posting date" + reverse flag | `Bal.sheet preparation valuatn` checkbox |
| Why | The figure is provisional; the real realized gain/loss posts when the item clears — reversing avoids double-counting | The valuation becomes the carried position; reversing it would be wrong |

### At UNESCO
- **Open Items (`_OI` variants)** run in **Mode A** — valuate month-end, reverse day-1. Confirmed in BKPF for all 8 OI-capable institutes.
- **Balances (`_UNBA` variants)** run effectively as **Mode B** — valuate month-end, no reversal. This is the **standard, correct** treatment for bank/cash balances. It is **not** a defect.
- UIL has one balance reversal (Jan 2025) — that is the one-off **deviation**, not evidence the others are wrong.

> **Anti-regression note:** Do NOT label "balance valuations don't reverse" as an error. It was incorrectly flagged as a defect in an earlier draft and corrected Session #078. ~~The only confirmation still open is reading the `Bal.sheet preparation valuatn` checkbox on a `_UNBA` variant screen (not extractable via RFC — VARI/VARIS are pool tables returning only the variant name).~~ **REFUTADO y CERRADO (s102, 2026-08-21):** `RS_VARIANT_CONTENTS_RFC` devuelve el contenido íntegro de la variante y `UNES_UNBA` lleva **`X_SALBEW = X`** con `X_GL`/`X_AP`/`X_AR` en blanco — valoración de saldo pura, confirmada por lectura, no por pantalla. Lo irrecuperable por `RFC_READ_TABLE` es `VARI.CLUSTD` (campo RAW), que no es lo mismo que "la variante no es auditable". Ver §2-bis.

---

## 4. Account Determination — T030H / OBA1

T030H (maintained in OBA1) maps each FX-exposed account (HKONT) to its valuation adjustment targets:
- `LKORR` — balance-sheet adjustment (correction) account
- `LSBEW` / `LHBEW` — P&L gain/loss accounts
- `CURTP` — currency type (10 = local/company-code currency basis, 30 = group)

UNES chart of accounts (KTOPL=UNES): **1,014 rows, 891 distinct HKONTs.**

### The configuration design — main account + sub-account (definitive, Session #078)

UNESCO configures the FX revaluation balance-sheet adjustment in OB09 / T030H in **two valid patterns**, plus one broken state. Across the 944 distinct HKONTs in T030H:

| Pattern | How it revalues | Accounts | Active | Status |
|---------|-----------------|----------|--------|--------|
| **Self-revaluation** (`HKONT = LKORR`) | The account is its own balance-sheet adjustment | 555 | 277 | ✓ dominant pattern |
| **Sub-account** (`BK main → S-BK active sub`) | Adjustment posts to a separate active sub-account | 167 | 163 | ✓ works (e.g. Ecobank) |
| **Sub-account BROKEN** (`BK main → S-BK CLOSED sub`) | Same method, but the sub was blocked | 6 | 6 | ❌ **the error** |
| Empty LKORR | No adjustment configured | 200 | 134 | OK (mostly USD = local cur.) |

#### The 3-account design (per bank/currency, sub-account pattern)
| Role | What it is | Banco Chile CLP | Ecobank ZWG |
|------|-----------|-----------------|-------------|
| **BK** (main) | Operating account, holds cash. **This is what F.05 revalues.** | `1010574` | `1094316` |
| **S-BK** (active sub) | Adjustment account — receives the FX valuation delta. This is the `LKORR` in OB09. | `1110574` | `1194316` |
| **CLOSED S-BK** (old sub) | Previous sub, retired and blocked. | `1109574` | `1194314` |

Numbering convention: **active sub = main + 100000** (Ecobank: 1094316+100000=1194316 ✓; Banco Chile: 1010574+100000=1110574 ✓, exists and active). The active sub itself carries a T030H row pointing to the old closed sub (e.g. `1110574 → 1109574`, `1194316 → 1194314`) — consistent in both banks; harmless because the subs are outside the variant range.

### The error explained

Correct config: `BK main → LKORR = its ACTIVE S-BK sub`. **Ecobank does this right** (`1094316 → 1194316` active → works).

**Banco de Chile is broken:** its sub was migrated (old `1109574` closed → new `1110574` created), **but OB09 was never updated** — the main account still points to the *closed* sub:
```
1010574 (BK main) → LKORR = 1109574  (CLOSED) ❌   should be 1110574 (active sub)
```
So F.05 revalues the active CLP balance, tries to post the adjustment to the blocked `1109574` → *"Account 1109574 is blocked for posting."*

**Two conditions for the runtime error:** (1) the config points to a blocked sub, AND (2) the main account has an FX balance to revalue. No balance → no error (latent).

**Scope:** only **2 accounts are inside the failing variant's ranges** (`1000000–1099999` etc.): `1010571` and `1010574`. The other 4 broken accounts (`1110571/574`, `1143254`, `1194316`) are outside the range → not revalued by this variant → do not raise this error. Only the `1109574` (CLP) path is confirmed from the session screenshot.

### Fix — repoint OB09 to the active sub (do NOT unblock)

The closed subs were retired on purpose — do not unblock them. Repoint the main accounts to their active sub, matching Ecobank:

| Account | LKORR now (wrong) | LKORR correct |
|---------|-------------------|---------------|
| `1010574` CLP | `1109574` (CLOSED) | **`1110574`** (S-BK active) |
| `1010571` USD | `1109571` (CLOSED) | **`1110571`** (S-BK active) |

Two OB09 entries → valuation posts to the active sub → error resolved. No unblocking, no variant change.

> To confirm with Treasury/accounting: that the active sub `1110574/1110571` is the intended adjustment account (the migration target). Then apply the OB09 repoint.

> Correction history (Session #078): earlier drafts said "6 active HKONTs generate the error" and "fix = unblock / KDF redirect." Both imprecise. The accurate statement: a sub-account migration left 2 in-scope main accounts pointing to the retired (blocked) sub; fix = repoint OB09 to the active sub.

### The defect tiers (UNES) — verified Session #078
| Tier | Count | Verdict |
|------|-------|---------|
| Total T030H rows | 1,014 | — |
| Fully empty rows (LKORR+LSBEW+LHBEW blank) | 200 | **Benign.** Active subset (102) are all USD (local cur., nothing to value) or dormant foreign accounts (zero balance). None in the UNES_UNBA range. |
| Distinct HKONTs with a blocked LKORR | 284 | — |
| → HKONT itself also blocked (XSPEB='X') | 278 | **Safe.** F.05 skips blocked HKONTs before the LKORR lookup. No error. Closed accounts that should not be revalued anyway. |
| → HKONT **active** pointing to a closed sub | **6** | **The mis-pointed accounts** (unfinished sub-account migration, § "configuration design"). Only **2 are in the failing variant's range** (`1010574`, `1010571`) → those actually error. Fix = repoint OB09 to the active sub. |

### The 6 mis-pointed accounts (point to a closed sub instead of the active one)
All have `XSPEB=''` (active) and `XLOEB=''` (not marked for deletion). **Balances must be read from GLT0/FAGLFLEXT or FS10N — NOT derived from Gold DB BSIS** (see method below). One verified live: `0001143254` = "S-BK CITIBANK-DAKAR", **XOF**, FY2026 balance **79,719 USD**, ~28 M turnover.

All 6 are company code **UNES**, across **3 banks**: Banco de Chile Santiago (4 accounts — USD & CLP, main "BK" + sub "S-BK"), Citibank Dakar (XOF), Ecobank Harare (ZWG). Currency from the SKAT account name (authoritative), not SKB1.WAERS.

| Source HKONT | Co | Account Name (SKAT) | Currency | Bank / Location | → LKORR (blocked) | Note |
|--------------|----|---------------------|----------|-----------------|-------------------|------|
| 0001143254 | UNES | S-BK CITIBANK - UNESCO DAKAR XOF | **XOF** (SKB1 wrongly=USD) | Citibank, Dakar SN | 0001102304 (**VND!**) | currency mismatch → wrong LKORR; FS10N: 79,719 USD bal, ~28M turnover |
| 0001010574 | UNES | BK BANCO DE CHILE - SANTIAGO CLP | CLP | Banco de Chile, Santiago CL | 0001109574 | main acct · known incident |
| 0001010571 | UNES | BK BANCO DE CHILE - SANTIAGO USD | USD | Banco de Chile, Santiago CL | 0001109571 | main acct (USD leg) |
| 0001110574 | UNES | S-BK BANCO DE CHILE - SANTIAGO CLP | CLP | Banco de Chile, Santiago CL | 0001109574 | sub-bank acct |
| 0001194316 | UNES | S-BK ECOBANK - UNESCO HARARE ZWG | ZWG | Ecobank, Harare ZW | 0001194314 | Zimbabwe Gold, new since Apr 2024 |
| 0001110571 | UNES | S-BK BANCO DE CHILE - SANTIAGO USD | USD | Banco de Chile, Santiago CL | 0001109571 | sub-bank acct |

All sources `XSPEB=''` (active), `XLOEB=''`. The **blocked** accounts are the LKORR targets (0001109571/574, 0001102304, 0001194314 — all `XSPEB='X'`), NOT the sources above. Balances: read from FS10N/FAGLB03 only.

### Reference (reusable) — how to read GL balance totals from GLT0/FAGLFLEXT

> **Note on scope:** balance analysis is **not** part of the error's root cause (that is the OB09 sub-account migration). Balances only *gate which* mis-pointed account triggers the error on a given month. The method below is kept as **reusable methodology** — the correct way to pull a GL balance total in any analysis, learned this session after three wrong attempts.

GL account balances come from the **totals table GLT0** (classic GL) or **FAGLFLEXT** (new GL) — exactly what FS10N reads. Correct extraction:

```
filter: BUKRS, RYEAR, RLDNR='00' (leading ledger), RRCTY='0' (actuals), RVERS='001'
balance(local cur) = SIMPLE SUM of (HSLVT + HSL01..16) across ALL rows of the account
                     — the debit/credit sign is ALREADY in the stored values.
                     Do NOT flip by DRCRK (that double-counts → inflates).
Parse SAP trailing-minus: '2875.00-' → -2875.00.
```

Verified against FS10N: 0001143254 FY2026 = **79,718.87** ✓.

**Live GLT0 FY2026 balances (P01) for the 6 (local USD):**
| HKONT | FY2026 balance | Has FX balance → would revalue? |
|-------|----------------|---------------------------------|
| 0001143254 | 79,719 | yes |
| 0001010574 | 164,918 | yes |
| 0001010571 | 20,096 | yes |
| 0001110574 | −41,145 | yes |
| 0001194316 | 0 | no — no error today |
| 0001110571 | 0 | no — no error today |

So 4 carry a balance (at risk of the error), 2 are at 0. Which accounts carry a balance changes over time, so the at-risk set is not fixed. Gold DB `glt0_p01` covers FY2023–2025 only; FY2026 must be pulled live from P01.

> **DATA-QUALITY LESSON (anti-regression):** Three wrong methods seen and corrected this session for `0001143254`: (a) summing BSIS open-item `DMBTR` → "445,688" (BSIS is not a balance); (b) GLT0 with a DRCRK sign-flip → "56M" (the sign is already in the values — double-counted); (c) `SKB1.WAERS` said USD when the account is XOF. **Correct: GLT0/FAGLFLEXT with RLDNR=00/RRCTY=0/RVERS=001, simple sum (no flip); currency from the SKAT name / document currency; or just read FS10N/FAGLB03.** Verified figure = 79,718.87.

### The error needs a balance — and the variant scopes it

F.05 only errors when the source account carries a non-zero FX balance: it computes the delta and tries to post the adjustment to the (closed) sub → fails. **Balance 0 → no revaluation → no error** (the zero-balance sub-accounts 0001110574/571 do not error today). The account must also be inside the failing variant's ranges. Net: of the 6 mis-pointed accounts, only the **2 in-scope** Banco de Chile mains with a balance (`1010574` CLP, `1010571` USD) actually raise this error. Only the `1109574` (CLP) path is confirmed from the session screenshot. The trigger set shifts as balances change, but the defect — and its fix (repoint OB09 to the active sub, above) — is fixed.

> Everything else in T030H (200 empty, 278 self-blocked, 102 active-empty) was reviewed and is benign. **Anti-regression:** do NOT re-frame this as "incomplete account closure / sweep balance to 0 / unblock the sub" — those were earlier, less precise drafts. The accurate root cause is the **unfinished sub-account migration**; the fix is the **OB09 repoint to the active sub**.

### Are the 6 accounts excluded in the variant? No — the error proves it

VARIS exclusion entries cannot be read via RFC (pool table; content FMs not RFC-callable — needs the F.05 screen or D01 + S_DEVELOP). But the logic is conclusive: an excluded account never reaches account determination, so it **cannot** raise "Account XXXX is blocked for posting." The runtime error therefore proves the 6 are **in scope, not excluded**. (To list exclusions for *other* accounts, read the variant's selection options for `sign='E'`.)

### Canonical procedure — removing an account from FX revaluation

| # | Step | Where / check |
|---|------|---------------|
| 1 | **Verify balance = 0** (precondition for blocking) | FAGLB03/FS10N or `SUM(DMBTR)` in BSIS — zero in all currencies |
| 2 | **Block for posting** (`XSPEB='X'`, "CLOSED" desc) | FS00 — once blocked, F.05 skips it as a *source* automatically |
| 3 | **Remove from valuation determination (T030H, both ways):** (a) delete rows where the account is the *source* HKONT; (b) where it is an *LKORR target* for other accounts, **redirect** those dependents to a replacement adjustment account before retiring it | OBA1/KDF = house-bank closure checklist **Step 4 ("OBA1: Remove entry")** |
| 4 | **Variant exclusion** — the range always covers the entire bank GL band (`0001xxxxxx`), so you can never remove an account by narrowing the range (it would drop live accounts too). Range-level removal = either **block (Step 2)** — F.05 skips blocked HKONTs in-range — or, if the account must stay **active** but not be FX-valued, an explicit exclusion (`sign='E'`). | F.05 → variant → selection options. Exclusion only for the active-but-exclude case; blocking suffices for closed accounts |
| 5 | **Verify** — F.05 test/simulation run | No "blocked for posting" error; no unintended scope drop |

**This procedure is general reference** (the discipline that prevents the next migration from breaking) — NOT the fix for the current error. The current fix is the OB09 repoint to the active sub (above). What was skipped here: when the old Banco de Chile sub was retired, Step 3 (repoint OB09 to the new active sub) was not done.

---

## 5. Variant Inventory — SAPF100 (27 variants)

21 UNESCO operational + 6 SAP-delivered (`SAP&*`, not used in monthly close). Source: VARI + VARIS (pool tables — only the variant name is RFC-readable; full content needs `RFC_ABAP_INSTALL_AND_RUN` on D01, which is blocked on P01 by S_DEVELOP).

### Naming convention
| Suffix | Meaning | Scope |
|--------|---------|-------|
| `_OI` | "AP/AR/GL OI revaluation" (Open Items tab) | AR/AP + G/L open items |
| `_UNBA` / `_BA` | "Balances Revaluation" (G/L Balances tab) | Balance-sheet accounts incl. bank |
| `_OI_AR/AP`, `_OI_G/L` | Split OI scopes | Subledger vs G/L OI |
| `_DEPOSIT` | "Deposit {range}" | Specific deposit/OTHR accounts |
| `GRP CUR` | Group currency | Cross-currency |
| `SAP&*` | SAP-delivered audit variants | Not operational |

### Per-company coverage (confirmed from 2025 BSIS execution)
| Company | Variants | Bank accounts revalued | Note |
|---------|----------|------------------------|------|
| IBE | IBE_OI, IBE_UNBA | 1 | clean |
| ICBA | ICBA_OI, ICBA_UNBA | 2 | balance runs 8/12 months |
| **ICTP** | ICTP_OI **only** | 0 | **No balance variant — structural coverage gap** |
| IIEP | IIEP_OI, IIEP_UNBA | 3 | best-covered; S_COURONNAUD runs balance |
| MGIE | MGIE_OI, MGIE_UNBA | 1 | OI reversals inconsistent |
| UBO | GRP CUR, OI_AR/AP, OI_G/L, UNBA | 0 | no bank FX exposure; 3 variants mislabeled "UNES" |
| UIL | UIL_OI, UIL_UNBA | 2 | clean |
| UIS | UIS_OI, UIS_UNBA | 1 | clean |
| UNES | DEPOSIT, OI_AR/AP, OI_G/L, UNBA | 82 | largest; UNES_UNBA is the error-generating variant |

### Which UNES variant generates the error
- **`UNES_UNBA`** covers the full bank-balance range `0001001604 → 0001098174` (82 bank accounts across 25 bank families) — **this is the variant that revalues the mis-pointed Banco de Chile mains (`1010574`, `1010571`) whose closed sub triggers the error.** Stale since 27.04.2007.
- **`UNES_DEPOSIT`** covers only 4041xxx OTHR accounts (EUR, 1 active = 0004041017) — its description "4041011 > 4041013" refers to those source accounts. **Does NOT cover the 82 bank accounts.** Not the error source.

### UNES bank account groups (82 accounts, 25 bank families)
Citibank (19), Standard Chartered (15), Société Générale (12), Ecobank (9), then 21 single/double-account banks. The 2 in-scope error accounts are the **Banco de Chile** main USD/CLP accounts.

---

## 6. Process Coverage & Operational Findings

### Confirmed strong
- 108/108 institute×month closing cycles present in 2025 (except ICTP Jul+Nov).
- OI valuation + day-1 reversal confirmed for all 8 OI institutes.
- Balance valuation (no reversal) consistent across all balance-capable institutes — standard practice.

### Real operational issues (not the false alarms)
1. **Unfinished Banco de Chile sub-account migration (UNES)** — the one genuine config error: 2 in-scope main accounts point to the closed sub instead of the active one → "blocked for posting". Fix = OB09 repoint. → §4.
2. **ICTP structural fragility** — no balance variant, and a single user (M_VENUTI → T_CARPENE) with no backup. Missed Jul+Nov 2025 and May 2026 (3 gaps in 17 months) whenever the user is absent.
3. **MGIE OI reversals inconsistent** — several months show valuation without the day-1 OI reversal.
4. **OI reversal timing lag (UNES)** — OI reversals (which *should* happen) run late on average; surfaces unrealized FX in interim reporting longer than ideal.
5. **UBO variant mislabeling** — 3 variants describe "UNES"; parameters appear correct (0 bank accounts processed) but descriptions are misleading for audit.

### NOT issues (reviewed and cleared — anti-regression)
- Balance valuations not reversing → standard Mode B. §3.
- 200 empty / 102 active-empty T030H rows → USD or dormant. §4.
- 278 self-blocked HKONTs with blocked LKORR → correctly skipped. §4.

### Who runs it & timing (2025 production)
One primary accountant per institute, no backup enforcement:
| Institute | Primary user | 2025 avg valuation lag | Note |
|-----------|-------------|------------------------|------|
| ICBA | E_GEBREMARIA / A_MULUGETA | ~2.6d | best; 2 users alternate |
| UIL | DB_ABDI | ~8.0d | consistent |
| UBO | P_TUCKER | ~24.3d* | chronic late in 2025 (*per-doc recompute ≈17.8d — definition-dependent) |
| IBE | V_KOHEMUN | ~9.0d | — |
| IIEP | F_CADIO + S_COURONNAUD | ~5.1d | best-covered; S_COURONNAUD runs balance |
| UIS | N_MOUSSA | ~3.7d | clean |
| MGIE | P_ARORA | ~5.1d | mid-month posting pattern (anomaly) |
| ICTP | M_VENUTI → T_CARPENE | ~7.6d | single point of failure |
| UNES | J_LA | ~6.7d | largest volume; OI reversal lag avg 11.8d |

OI valuation + day-1 reversal monthly for all 8 OI institutes; balance valuation monthly without reversal (Mode B, correct). Lag = CPUDT − BUDAT.

### 2026 trend (Jan–May, live data)
- BKPF complete Jan–May 2026 (272K rows for FY2026).
- **~78% average valuation-lag reduction vs 2025**, with **no automation added** — accountability/awareness effect. UBO 24.3d→1.2d, UIL 8.0d→0.4d, IBE 9.0d→0.7d.
- **ICTP missed May 2026** (T_CARPENE absent) — 3rd gap in 17 months (after Jul+Nov 2025).
- **UNES May 2026 cross-covered by P_TUCKER** (UBO accountant) — J_LA absent; ad-hoc, undocumented backup.

### Known unknowns & open verifications
- **KU-CA-001** — confirm `1110574/1110571` is the intended migration target adjustment account (Treasury) before the OB09 repoint. §4.
- **KU-CA-002** — confirm `_UNBA` valuation mode: read the `Bal.sheet preparation valuatn` checkbox (decides whether balance non-reversal is intentional Mode B). §3.
- Exact variant GL-account selection ranges — read VARI/VARID/VARIS content on D01 via `RFC_ABAP_INSTALL_AND_RUN` (blocked on P01 by S_DEVELOP). §5.
- MGIE `P_ARORA` mid-month posting rationale — interview.

### Falsifiable predictions (testable)
- **FALS-CA-001** — Creating an SM36 SAPF100 job for one BUKRS (e.g. ICTP) will produce revaluation documents with CPUDT = BUDAT (sub-hour lag). Test: create ICTP job, monitor first month-end run.
- **FALS-CA-002** — Without a backup user or SM36 job, ICTP will miss at least one month in 2026. Test: monitor BKPF monthly for ICTP valuation docs. (Already partly confirmed — May 2026 missed.)
- **FALS-CA-003** — Repointing OB09 for the 2 in-scope accounts to the active sub (`1110574/1110571`) will eliminate the "blocked for posting" error. Test: F.05 simulation run → zero error for the previously-failing accounts.

### Proposed month-end close calendar (target state)
| Timing | Activity | Current | Target (automated) |
|--------|----------|---------|--------------------|
| Day 25–28 (last biz days) | Revalue open FX positions (SAPF100 valuation, BUDAT = month-end) | Interactive, lag 0–62d, ICTP gaps | SM36 job, last biz day 23:00, per BUKRS |
| Day 1 (new month) | Reverse prior-month FX (OI reversal, BUDAT = day 1) | Interactive, UNES avg 11.8d late | SM36 job, day 1 06:00 |
| Day 28–31 (pre-close) | FX sign-off gate before OB52 period lock | Does not exist — period locks without FX check | Controller sign-off; job log = evidence |

---

## 7. Two Levels of Action — Fix the Error, Then Capture the Big Opportunity

The OB09 fix (§4) removes one error. The far larger value is **automating F.05 with background jobs** — and the infrastructure already exists in the same system.

### Level 1 — Tactical (fix the error)
Repoint 2 OB09 entries to the active sub-account (§4). Effort: 2 config entries · Impact: 1 error resolved.

### Level 2 — Strategic (automate F.05) — the real opportunity
**Today there are ZERO SAPF100 background jobs** — all FX revaluation is launched interactively by individual accountants. Meanwhile `SAPF124` (automatic clearing) **already runs daily as a JOBBATCH job** — the exact template to copy.

Schedule SM36 jobs for SAPF100 per company code: valuation last business day 23:00 + reversal day-1 06:00, under JOBBATCH. Effort: 9 BUKRS × (valuation + reversal) variants.

**What automation eliminates — all at once:**
| Problem today (manual/interactive) | Evidence | After SM36 jobs |
|------------------------------------|----------|-----------------|
| Missed months (period closes with no FX reval, undetected) | ICTP missed Jul+Nov 2025, May 2026 (single user, no backup) | Job runs regardless of who is present |
| Timing lag (posted days/weeks after month-end) | 2025 avg lag up to ~18–24d; 2026 ↓~78% but still manual/fragile | CPUDT = BUDAT, zero lag |
| Single-point-of-failure (one accountant, no backup) | ICTP, UBO; ad-hoc cross-coverage May 2026 | No human dependency for the run |
| No sign-off gate (OB52 locks without checking FX) | ICTP gaps found by data mining months later | Job log = sign-off evidence |
| No audit trail of "did it run?" | Reconstructed manually from BKPF this session | SM37 job history, automatic |

**Low-risk, high-value:** the pattern is already proven here — SAPF124 clears automatically every day under JOBBATCH without incident. The 78% timing improvement seen in 2026 was driven only by accountability/awareness; jobs would make it **structural and permanent**.

### Remaining items
3. **Assign backups** for single-user institutes (ICTP especially) — until jobs remove the human dependency.
4. **FX sign-off gate** before OB52 period lock (the job log becomes the evidence).
5. **Confirm `_UNBA` valuation mode** (read the `Bal.sheet preparation valuatn` checkbox) and document it.
6. **Add ICTP balance variant** if ICTP carries bank/balance-sheet FX that should be revalued.

---

## 8. Methodology Reference

The reusable technique for analyzing any program's variants (pool-table extraction, naming-convention decode, account-block cross-reference, execution reconstruction from BKPF/BSIS) is documented separately:
- Skill: `.agents/skills/sap_variant_analysis/SKILL.md`
- Knowledge: `knowledge/domains/Closing_Activities/sap_variant_forensic_methodology.md`

## 9. Related

- Companion: `companions/closing_activities_v1.html`
- Calendar/timing knowledge: `knowledge/domains/Closing_Activities/fx_revaluation_closing_calendar_2025.md`
- Domain index: `knowledge/domains/Closing_Activities/README.md`
- Tables: T030H (OBA1), SKB1.XSPEB (block flag), T012K (house bank → GL), T001.WAERS (local currency), VARI/VARIS (variants), BKPF.TCODE='FBB1', BSIS+P01_SKA1.KTOKS (account type)
