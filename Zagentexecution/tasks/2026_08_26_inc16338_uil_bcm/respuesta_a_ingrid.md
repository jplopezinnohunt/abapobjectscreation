# Borrador — respuesta a Ingrid Wettie (INC-000016338)

**Para:** Wettie, Ingrid <i.wettie@unesco.org>
**Cc:** Liste.BFM-TRS-MO ; Ikouna Bouangolh, Patrick
**Asunto:** RE: IMPORTANT: Change in Bank Signatory panel of UIL + Smart ticket INC-000016338

---

Dear Ingrid,

Bettina REISS has been added to the UIL BCM signatory panel. Verified by direct read of `HRP1001`,
not from the screen:

| Rule | Node (RY) | Node name | PERNR | Valid |
|---|---|---|---|---|
| 90000005 (validate) | `50037530` | UIL Validation | 10049633 | 26.08.2026 – unlimited |
| 90000004 (commit) | `50037531` | UIL signatures for all transfers | 10049633 | 26.08.2026 – unlimited |

No signatory was removed — the letters instruct none, and the reconciliation against the carton
found **no over-authorization** in UIL. That is worth saying plainly: UIL is the first entity we
have reconciled where everyone active in SAP is on the carton.

**Three things need a decision from TRS before this ticket can be closed.**

---

**1. The USD 10,000 limit cannot be applied — and it affects TWO people, not one.**

Your note asked to add "her bank limits". The letters cap **two** signatories at USD 10,000.00:
**Ana Suzan BASOGLU** and **Bettina REISS**.

Neither cap is enforceable in SAP today. Amount limits are applied by the responsibility node
itself, and **UIL's two nodes carry no amount band**:

| Node | Amount range configured |
|---|---|
| `50037530` UIL Validation | 0.00 – 9,999,999,999.00 |
| `50037531` UIL signatures | 0.00 – 50,000,000.00 |
| *(for comparison)* UBO `50034892` "up to 10.000" | 0.00 – **10,000.00** |

UBO has tiered nodes; UIL has a single all-amounts node per rule. So both REISS and BASOGLU are
now authorized in SAP for any amount.

**This is not new.** BASOGLU has been on the UIL validation node **without any limit since
27.09.2024**, under letters that already capped her. Adding REISS makes it two rather than one; it
did not create the gap.

To enforce the caps we would need new UIL nodes with a ≤10K band and the panel split across them —
a configuration change, not a data change. **Please confirm which you want:**
(a) create the ≤10K nodes for UIL, or
(b) accept in writing that the USD 10,000 limit is enforced only at the bank, and that SAP grants
    both signatories unlimited release authority.

---

**2. The Treasurer who signs the letters cannot approve UIL payments in SAP.**

**Anssi YLI-HIETANEN (PERNR 10097358)** is on the UIL carton, and his SAP assignment on **both**
UIL nodes **expired on 26.01.2024 — 31 months ago**. He holds the BCM authorization role, so only
the node membership is missing.

The same person is in the same situation in **UBO** (open since INC-000011781, June). Two entities,
one PERNR, one defect. We did not act on it: it is outside what these letters instruct, and we do
not touch a panel without a signed authorization.

**Do you authorize adding 10097358 back to `50037530` and `50037531`?**

---

**3. Ana Suzan BASOGLU can validate but cannot commit.**

She is active on `50037530` (validation) and has **never** been on `50037531` (commit). The carton
says "authorized to sign jointly two by two" without distinguishing the two steps, so the document
does not tell us which is right.

**Is the split intentional, or a maintenance accident?**

---

**Still pending on our side:** the BCM approval role for Bettina's SAP user (`B_REISS`) has been
requested from Security. Being on the node is not enough — without the role she cannot open the
approval application. She also has never logged on to SAP. We will confirm once Security grants it.

**A reminder on the deadline in the Role Management notice:** by **03.09.2026** the UIL
Administrative Officer (Morsal Jamal) should obtain the bank's written confirmation of the
signatory list **including the limits**. Point 1 above is likely to surface there.

Best regards,
Pablo

---

## Notas para Pablo antes de mandar (borrar)

- **Adjunta la tabla del panel** si quieres que Ingrid vea el estado completo de los 7.
- **No menciono el `BEGDA`** (DBS puso 26.08 en vez del 11.08 de la carta, 15 días de hueco). Es un
  tema con DBS, no con TRS — va en un correo aparte, sin dramatizar. Si prefieres que Ingrid lo
  sepa por trazabilidad de auditoría, se añade una línea.
- El punto 1 está escrito para que **quede constancia por escrito** de que se avisó. Es el que
  protege si alguien pregunta el año que viene por qué Basoglu firmó 400K.
