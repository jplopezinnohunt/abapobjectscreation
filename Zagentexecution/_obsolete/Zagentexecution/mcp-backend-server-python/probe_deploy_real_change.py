"""
probe_deploy_real_change.py — Test activate con cambio REAL en D01.

El 403 anterior fue porque escribimos el MISMO source (sin cambios).
SAP ADT no crea versión inactiva si el source no cambió → 403 al activar.

Este probe:
  1. Lee source actual
  2. Agrega un comentario al final (cambio mínimo)
  3. Hace el ciclo completo lock → write → syntax → activate → unlock
  4. Si activa OK → jp_lopez tiene todos los permisos
  5. Restaura el source original
"""
import os, sys
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
sys.path.insert(0, os.path.dirname(__file__))

from sap_adt_rfc_client import SapAdtRfcClient, AdtRfcError

# ── Object to test — Y namespace, jp_lopez is the developer ──────────────────
# Cambiar si se conoce un objeto donde jp_lopez tiene acceso confirmado.
# Empezamos con YCL_FI_ACC_DOCUMENT_ARGA (el objeto problemático).
TEST_OBJECTS = [
    # ZCRP — jp_lopez construye todo el proyecto, permisos plenos confirmados
    ("CLASS", "ZCL_CRP_CERT_READER"),
    # YA namespace — verificar acceso
    ("CLASS", "YCL_FI_ACC_DOCUMENT_ARGA"),
    ("CLASS", "YCL_FI_BANK_RECONCILIATION_BL"),
]


def get_conn():
    return Connection(
        ashost=os.getenv("SAP_ASHOST"),
        sysnr=os.getenv("SAP_SYSNR"),
        client=os.getenv("SAP_CLIENT"),
        user=os.getenv("SAP_USER"),
        passwd=os.getenv("SAP_PASSWD") or os.getenv("SAP_PASSWORD"),
        lang="EN",
    )


def main():
    print("=" * 60)
    print("Probe — Real Change Deploy Test (D01)")
    print("=" * 60)

    conn = get_conn()
    adt = SapAdtRfcClient(conn)
    adt._warmup()

    for obj_type, obj_name in TEST_OBJECTS:
        print(f"\n{'-' * 50}")
        print(f"Testing: {obj_type}/{obj_name}")
        print(f"{'-' * 50}")

        # ── Step 0: Check TADIR ─────────────────────────────────────────────
        print("\n[0] TADIR check...")
        try:
            info = adt.check_tadir(obj_type, obj_name)
            if not info["found"]:
                print(f"    NOT IN TADIR — object does not exist in D01")
                continue
            print(f"    Package:  {info['package']}")
            print(f"    Author:   {info['author']}")
            print(f"    $TMP:     {info['is_tmp']}")
        except Exception as e:
            print(f"    TADIR error: {e}")

        # ── Step 1: Read current source ─────────────────────────────────────
        print("\n[1] Reading current source...")
        try:
            original_source = adt.read_source(obj_type, obj_name)
            lines = original_source.splitlines()
            print(f"    Read OK — {len(lines)} lines")
            print(f"    First line: {lines[0][:80] if lines else '(empty)'}")
        except AdtRfcError as e:
            print(f"    Read FAILED: {e.status} {e.reason}")
            print(f"    Body: {e.body[:300]}")
            continue
        except Exception as e:
            print(f"    Read FAILED (RFC): {e}")
            continue

        # ── Step 2: Add a harmless comment change ───────────────────────────
        timestamp_comment = "* PROBE_TEST_COMMENT - safe to delete"
        if timestamp_comment in original_source:
            # Already has our marker — remove it (restore)
            modified_source = original_source.replace(
                "\n" + timestamp_comment, ""
            ).replace(timestamp_comment + "\n", "")
        else:
            # Add marker at end
            modified_source = original_source.rstrip() + "\n" + timestamp_comment + "\n"

        print(f"\n[2] Lock...")
        try:
            lock_handle = adt.lock(obj_type, obj_name)
            print(f"    Lock OK: {lock_handle[:30]}...")
        except AdtRfcError as e:
            print(f"    Lock FAILED: {e.status} {e.reason}: {e.body[:200]}")
            continue

        print(f"\n[3] Write (modified source)...")
        try:
            adt.write_source(obj_type, obj_name, modified_source, lock_handle)
            print(f"    Write OK")
        except AdtRfcError as e:
            print(f"    Write FAILED: {e.status} {e.reason}: {e.body[:200]}")
            adt.unlock(obj_type, obj_name, lock_handle)
            continue

        print(f"\n[4] Syntax check...")
        try:
            findings = adt.syntax_check(obj_type, obj_name)
            errors = [f for f in findings if f.get("severity") in ("E", "A")]
            print(f"    Findings: {len(findings)} ({len(errors)} errors)")
            if errors:
                for err in errors[:3]:
                    print(f"    [E] {err}")
                print(f"    Aborting activate (syntax errors)")
                adt.unlock(obj_type, obj_name, lock_handle)
                continue
        except Exception as e:
            print(f"    Syntax check error: {e}")

        # PROVEN: unlock BEFORE activate on ECC EhP8.
        # With lock held → 403 "User X is currently editing Y".
        print(f"\n[5] Unlock (required before activate on ECC EhP8)...")
        try:
            adt.unlock(obj_type, obj_name, lock_handle)
            lock_handle = None
            print(f"    Unlock OK")
        except Exception as e:
            print(f"    Unlock error: {e}")

        print(f"\n[6] Activate (after unlock)...")
        try:
            ok = adt.activate(obj_type, obj_name)
            print(f"    Activate: {'OK' if ok else 'returned False'}")
        except AdtRfcError as e:
            print(f"    Activate FAILED: {e.status} {e.reason}")
            print(f"    Body: {e.body[:400]}")
        except Exception as e:
            print(f"    Activate FAILED (exception): {e}")

        # ── Restore original ────────────────────────────────────────────────
        if timestamp_comment in modified_source:
            print(f"\n[7] Restoring original source (lock -> write -> unlock -> activate)...")
            lock2 = None
            try:
                lock2 = adt.lock(obj_type, obj_name)
                adt.write_source(obj_type, obj_name, original_source, lock2)
                adt.unlock(obj_type, obj_name, lock2)
                lock2 = None
                adt.activate(obj_type, obj_name)
                print(f"    Restored OK")
            except Exception as e:
                print(f"    Restore error: {e}")
                if lock2:
                    try:
                        adt.unlock(obj_type, obj_name, lock2)
                    except Exception:
                        pass

    conn.close()
    print("\n\nDone.")


if __name__ == "__main__":
    main()
