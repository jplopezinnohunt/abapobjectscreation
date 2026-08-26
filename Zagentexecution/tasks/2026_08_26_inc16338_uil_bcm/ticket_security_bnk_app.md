# Borrador — ticket a Security (rol BNK_APP para B_REISS)

**Asunto:** Grant BCM approval role `YS:FI:M:BCM_MON_APP______:UIL` to user `B_REISS` — INC-000016338

---

**Request**

Please assign the following role:

| | |
|---|---|
| **SAP user** | `B_REISS` |
| **Person** | Bettina REISS, PERNR 10049633, UNESCO Institute for Lifelong Learning (UIL), Hamburg |
| **Role** | `YS:FI:M:BCM_MON_APP______:UIL` |
| **Org level** | `$BUKRS = UIL` |
| **System** | P01 |
| **Valid from** | 26.08.2026 (open-ended, or aligned to the user validity 31.12.2027) |

**Why**

Bettina REISS was added to the UIL BCM signatory panel on 26.08.2026 (nodes `50037530` and
`50037531`, rules 90000005 / 90000004), authorized by TRS letters `FIN.8/MOD/10.0000003674`
(Deutsche Bank Hamburg AG) and `FIN.8/MOD/10.0000003675` (Société Générale), both dated 11.08.2026
and signed by the Treasurer.

**Node membership alone does not enable signing.** The workflow will resolve the rule and return
her as an eligible approver, but without this role she cannot open the approval application, so the
work item cannot be actioned. Measured today:

```
AGR_USERS  UNAME = B_REISS  ->  6 roles, all HR:
   YCF:HR:EMPL_SELF_SRVCE___:ALL
   YO:HR:D:VOLUNTARY_SEP____:ALL
   YS:HR:D:PA_WORKFLOW______:ALL
   YSF:HR:EMPLOYEE_STAFF____:ALL
   YSF:HR:OFFBOARDING_______:ALL
   Y_HR_ADMINISTRATION
   ->  ZERO roles in the YS:FI:M:BCM_MON_APP______:* family
```

Automated check `bcm_role_gap_check.py` (P01, 26.08.2026):

```
per-node gaps:
  50037530 UIL 90000005 UIL Validation                    -> B_REISS
  50037531 UIL 90000004 UIL signatures for all transfers  -> B_REISS
```

**Precedent for the derived role**

The other five active UIL signatories all hold the same derived role, so this is an existing,
proven assignment and not a new design:

| User | Role | Valid to |
|---|---|---|
| `DB_ABDI` | `YS:FI:M:BCM_MON_APP______:UIL` | 30.06.2028 |
| `I_KEMPF` | `YS:FI:M:BCM_MON_APP______:UIL` | 31.12.2027 |
| `R_VALDES-COT` | `YS:FI:M:BCM_MON_APP______:UIL` | 15.09.2027 |
| `R_ZHOLDOSHAL` | `YS:FI:M:BCM_MON_APP______:UIL` | 14.01.2027 |
| `A_BASOGLU` | `YS:FI:M:BCM_MON_APP______:UIL` | 23.03.2027 |

**Note**

`B_REISS` is a valid, unlocked dialog user (`USR02`: `UFLAG=0`, `USTYP=A`, valid to 31.12.2027) who
**has never logged on** (`TRDAT = 00000000`). An initial logon will be needed before she can
approve.

**Reference:** ticket INC-000016338. This is the item that blocks its closure — the same gap left
INC-000011781 (UBO) open since June.
