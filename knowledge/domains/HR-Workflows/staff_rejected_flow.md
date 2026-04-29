# STAFF REJECT flow — HR Workflow mechanic

**Domain**: HR-Workflows
**Established**: Session #60 (2026-04-22) from user business description
**Confidence**: TIER_2 (empirical / user-attested from business knowledge)
**Needs validation**: source code confirmation via ZCL_HR_FIORI_* handler classes

## The rule

When a staff-routed request is **REJECTED at Step 01**, the behavior is:

| Action | Target state | Next step for creator |
|---|---|---|
| STAFF REJECT at Step 01 | → `STAFF_REJECTED` status | Creator **revises + RESUBMITs** (goes back to Step 01 fresh) OR cancels. **NOT a pop.** |

Key points:

- **Not a pop** — rejection at Step 01 does not pop the workflow stack back to a previous approver (there is no previous approver).
- **Resubmit creates a fresh Step 01** — when the creator fixes and resubmits, the workflow starts a new Step 01 iteration, not a continuation of the rejected one.
- **Cancel is terminal** — creator can abandon the request.

## The symmetric negative rule — RETURN at Step 01 is impossible

| Action | Target | Why |
|---|---|---|
| Any **RETURN** attempt at Step 01 | — | **Impossible** — the Fiori / WebDynpro UI doesn't render the RETURN button on Step 01. The handler, if somehow invoked programmatically, has nothing to pop (no previous step on the stack). |

This is a **UI-enforced invariant**, not a runtime check. The button is conditionally hidden when `current_step = 01` so the user never has the option.

## Why this matters

1. **Debugging direction**: if a user reports "I can't return this at Step 01", the answer is not "there's a bug" — it's "this is by design, use REJECT and let the creator resubmit".
2. **State-machine completeness**: Step 01 only has three outgoing transitions: APPROVE (→ Step 02), REJECT (→ STAFF_REJECTED), CANCEL (→ CANCELLED). RETURN is not in the transition set at Step 01.
3. **Handler code**: any RETURN handler must guard `current_step ≠ 01` before executing the pop logic. Otherwise it would attempt to pop an empty stack and throw (defensive coding already in place — confirmed by user).

## Transition diagram

```
                         ┌─────────────┐
                         │   Step 01   │
                         │ (creator)   │
                         └─────┬───────┘
               REJECT    APPROVE    CANCEL
                  │         │          │
          ┌───────▼──┐  ┌───▼────┐  ┌──▼────────┐
          │ STAFF_   │  │Step 02 │  │ CANCELLED │
          │ REJECTED │  │(next)  │  └───────────┘
          └────┬─────┘  └────────┘
               │
        ┌──────▼──────┐
        │ Creator     │
        │ revises +   │
        │ RESUBMIT    │
        └─────┬───────┘
              │ (fresh iteration)
              ▼
         ┌──────────┐
         │ Step 01  │ (NEW instance, not a pop/resume)
         └──────────┘
```

## Related objects (to validate)

- `ZCL_HR_FIORI_OFFBOARDING_REQ` (Offboarding workflow handler)
- `ZCL_ZHRF_OFFBOARD_DPC_EXT` (Fiori DPC_EXT with workflow methods)
- `ZCL_HRFIORI_CHANGE_SISTER` / `ZCL_HRFIORI_FAMILY_SISTER` (Family workflow)
- `ZCL_ZHR_BENEFITS_REQUE_DPC_EXT` (Benefits workflow)
- `ZCL_HR_FIORI_RENTAL` / `ZCL_HR_FIORI_EDUCATION_GRANT`
- ASR Framework: `CL_HCMFAB_*`, `CL_HRASR00GEN_SERVICE`

## Open validation tasks

- **KU-HRWF-01**: Confirm RETURN button visibility rule in UI5 controller — is it driven by a conditional binding on `current_step` or by a backend metadata field?
- **KU-HRWF-02**: Confirm REJECT → STAFF_REJECTED transition in the handler class (which class / method / line?).
- **KU-HRWF-03**: Confirm RESUBMIT creates a new workflow container vs. reusing the rejected one (audit trail implication).
